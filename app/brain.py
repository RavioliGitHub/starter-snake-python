import random
import json
import time
from operator import itemgetter
import itertools
import game_engine
import copy
import pprint
try:
    from printer import Logger

    def log(turn, snake, message):
        Logger().log(turn, snake, message)

    def log(data, message):
        Logger().log(data['turn'], data['you'], message)
except ImportError:
    def log(turn, snake, message):
        #print(message)
        pass

    def log(data, message):
        #print(message)
        pass
"""
MAKE LOTS OF SMALL RULE THAT ARE AlWAYS true
1 move rules
then, just test priorities

"""

"""
BEHAVIOR I WANT TO ENFORCE

1.) Dont do moves that kill me immediately

2.) Avoid potential deadly head on head collisions

3.) Avoid going in tight spaces

4.) Avoid starvation

5.) Kill if possible

6.) 1v1 component ?

7.) Avoid spaces with many nearby bigger snakes

8.) Try full minimax


You need a fixed thing for 8 snakes
And a minimax for 1v1
Then replace deepcopy by pooling

As for escaping:
I need - A fast heuristik on wether a space is escapable
-An exact one
-One that gives the path

-time window to search for escape path ?

Zone where im dead       - Zone where im alive
######################## - ###################

check_if_space_is_escapable
FFFFFFFFF TTTTTTTTTTTTTT   TTTTTTTTTTTTTTTTTTT

I need a function with Tail reachability
FFFFFFFFFFFFFFFFFFFFFFFF   FFFFFFFFFTTTTTTTTTT



-maybe if only 1 path, update
-Ita about being able to reach a tail

TODO
Prefer head on head with snakes of equal length, also for lockdown
Improve to tight space calculation, as it fucks up sometimes
Map where you avoid zones with many bigger heads
Auto start leaderboard extraction
Plot leaderboard extraction
Create macro so that isNotMe becomes data[snake] != data[you] ? 
Need min max algo if 1v1

"""
directions = ['up', 'down', 'left', 'right']

#More tail follow ?
#https://play.battlesnake.com/g/10450b66-391b-47ec-8aa8-38704fa3e660/

#For min max add better death sentences

#Algorithms for blocked space
#Blocked space into minmax

#Do path where you just hug the wall
#Lookup table `?


def next_field(direction, current_position):
    if direction == 'up':
        return current_position['x'], current_position['y'] - 1
    elif direction == 'down':
        return current_position['x'], current_position['y'] + 1
    elif direction == 'left':
        return current_position['x'] - 1, current_position['y']
    elif direction == 'right':
        return current_position['x'] + 1, current_position['y']


def next_field_dic(direction, current_position):
    if direction == 'up':
        return {'x': current_position['x'], 'y': current_position['y'] - 1}
    elif direction == 'down':
        return {'x': current_position['x'], 'y': current_position['y'] + 1}
    elif direction == 'left':
        return {'x': current_position['x'] - 1, 'y': current_position['y']}
    elif direction == 'right':
        return {'x': current_position['x'] + 1, 'y': current_position['y']}


def next_field_with_tupel(direction, current_position):
    if direction == 'up':
        return current_position[0], current_position[1] - 1
    elif direction == 'down':
        return current_position[0], current_position[1] + 1
    elif direction == 'left':
        return current_position[0] - 1, current_position[1]
    elif direction == 'right':
        return current_position[0] + 1, current_position[1]


def not_deadly_location_on_board(goal, deadly_locations, width, height):
    if goal[0] < 0 or goal[0] >= width or goal[1] < 0 or goal[1] >= height:
        return False
    if deadly_locations.__contains__(goal):
        return False
    return True


def not_deadly_location_on_board_dic(goal, deadly_locations, width, height):
    if goal['x'] < 0 or goal['x'] >= width or goal['y'] < 0 or goal['y'] >= height:
        return False
    if deadly_locations.__contains__(goal):
        return False
    return True


def on_board(tile, data):
    width = data['board']['width']
    height = data['board']['height']
    if tile['x'] < 0 or tile['x'] >= width or tile['y'] < 0 or tile['y'] >= height:
        return False
    return True


def list_of_reachable_tiles_dic(data, start):
    deadly_locations = get_deadly_locations(data)
    width = data['board']['width']
    height = data['board']['height']

    start_dic = {'x':start[0], 'y':start[1]}

    for snake in data['board']['snakes']:
        tail_tupel = snake['body'][-1]['x'], snake['body'][-1]['y']
        tail_dic = snake['body'][-1]
        if tail_tupel in deadly_locations:
            # TODO FIx, tails dont count as reachable if food has been eaten and yournext to them
            # YOu could still reach them with a longer path
            if get_board_distance_between_two_points(start_dic, tail_dic) > 1:
                deadly_locations.remove(tail_tupel)

    reachable_dic_list = []
    reachable_tupel_list = list_of_reachable_tiles(start, deadly_locations, width, height)

    for tile_tupel in reachable_tupel_list:
        reachable_dic_list.append({'x':tile_tupel[0], 'y':tile_tupel[1]})

    return reachable_dic_list


def list_of_reachable_tiles(start, deadly_locations, width, height):
    visited = []
    queue = [start]

    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for d in directions:
            cur_neighbour = next_field_with_tupel(d, cur)
            if not visited.__contains__(cur_neighbour) and not queue.__contains__(cur_neighbour):
                if not_deadly_location_on_board(cur_neighbour, deadly_locations, width, height):
                    queue.append(cur_neighbour)

    return visited


def get_number_of_reachable_tiles(data, head):
    width = data['board']['width']
    height = data['board']['height']
    deadly_locations = get_deadly_locations(data)
    return len(list_of_reachable_tiles((head['x'], head['y']), deadly_locations, width, height))


def get_deadly_locations(data):
    board = data['board']
    snakes = board['snakes']

    deadly_locations = []
    for snake in snakes:
        for e in snake['body'][:-1]:
            deadly_locations.append((e['x'], e['y']))

    return deadly_locations


def get_deadly_locations_dic(data):
    board = data['board']
    snakes = board['snakes']

    deadly_locations = []
    for snake in snakes:
        for e in snake['body'][:-1]:
            deadly_locations.append(e)

    return deadly_locations


def get_moves_without_direct_death(data, *snake):
    you_before = data['you']

    if snake:
        snake = snake[0]
        data['you'] = snake

    board = data['board']
    height = board['height']
    width = board['width']
    you = data['you']
    you_head = you['body'][0]

    deadly_locations = get_deadly_locations(data)

    directions_without_direct_death = ['up', 'down', 'left', 'right']

    if you_head['x'] == 0:
        directions_without_direct_death.remove('left')
    if you_head['x'] == width - 1:
        directions_without_direct_death.remove('right')
    if you_head['y'] == 0:
        directions_without_direct_death.remove('up')
    if you_head['y'] == height - 1:
        directions_without_direct_death.remove('down')

    for d in directions:
        next_tile = next_field(d, you_head)
        if deadly_locations.__contains__(next_tile):
            directions_without_direct_death.remove(d)

    data['you'] = you_before
    return directions_without_direct_death


def get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death):
    board = data['board']
    snakes = board['snakes']
    you = data['you']
    you_head = you['body'][0]

    deadly_enemy_heads = []
    for snake in snakes:
        if snake['body'] != you['body'] and len(snake['body']) >= len(you['body']):
            deadly_enemy_heads.append(snake['body'][0])

    possible_deadly_head_on_head_collision = []
    for head in deadly_enemy_heads:
        for d in directions:
            possible_deadly_head_on_head_collision.append(next_field(d, head))

    directions_without_deadly_head_on_head_collision = []
    for d in directions_without_direct_death:
        next_tile = next_field(d, you_head)
        if not possible_deadly_head_on_head_collision.__contains__(next_tile):
            directions_without_deadly_head_on_head_collision.append(d)

    return directions_without_deadly_head_on_head_collision


def get_moves_without_potential_deadly_head_on_head_collision_with_longer_snakes(data, directions_without_direct_death):
    board = data['board']
    snakes = board['snakes']
    you = data['you']
    you_head = you['body'][0]

    heads_of_longer_enemies = []
    for snake in snakes:
        if snake['body'] != you['body'] and len(snake['body']) > len(you['body']):
            heads_of_longer_enemies.append(snake['body'][0])

    possible_deadly_head_on_head_collision = []
    for head in heads_of_longer_enemies:
        for d in directions:
            possible_deadly_head_on_head_collision.append(next_field(d, head))

    directions_without_deadly_head_on_head_collision = []
    for d in directions_without_direct_death:
        next_tile = next_field(d, you_head)
        if not possible_deadly_head_on_head_collision.__contains__(next_tile):
            directions_without_deadly_head_on_head_collision.append(d)

    return directions_without_deadly_head_on_head_collision


def get_least_constraining_moves(data, directions_without_direct_death):
    board = data['board']
    height = board['height']
    width = board['width']
    you = data['you']
    you_head = you['body'][0]
    directions_with_most_space = []

    if data['turn'] == 0:
        for d in directions:
            directions_with_most_space.append(d)
        return directions_with_most_space

    number_of_reachable_tiles = []
    deadly_locations = get_deadly_locations(data)
    for d in directions_without_direct_death:
        next_tile = next_field(d, you_head)
        reachable_tiles = list_of_reachable_tiles(next_tile, deadly_locations, width, height)
        number_of_reachable_tiles.append(len(reachable_tiles))

    while len(number_of_reachable_tiles) < 3:
        number_of_reachable_tiles.append(-1)

    for i in range(3):
        cur = number_of_reachable_tiles[i]
        prev = number_of_reachable_tiles[(i - 1) % 3]
        next = number_of_reachable_tiles[(i + 1) % 3]
        if cur >= prev and cur >= next:
            directions_with_most_space.append(directions_without_direct_death[i])

    return directions_with_most_space


def get_food_im_closest_to(data):
    board = data['board']
    food = board['food']
    you = data['you']
    you_head = you['body'][0]
    close_apples = []
    closest_apple = None
    distance_to_closest_apple = 100
    for apple in food:
        someone_else_will_be_first = False
        my_distance = get_distance_between_two_points(you_head, apple)
        for snake in board['snakes']:
            if snake == you:
                continue
            his_distance = get_distance_between_two_points(snake['body'][0], apple)
            if his_distance < my_distance:
                someone_else_will_be_first = True
                break
        if not someone_else_will_be_first:
            close_apples.append(apple)
            if my_distance < distance_to_closest_apple:
                closest_apple = apple
                distance_to_closest_apple = my_distance

    return closest_apple


def get_distance_to_apple_if_move_is_made(data, apple):
    if apple is None:
        return [0, 0, 0, 0]
    distances_to_apple = []
    you_head = data['you']['body'][0]
    for d in directions:
        next_tile = next_field_dic(d, you_head)
        distance = get_distance_between_two_points(next_tile, apple)
        distances_to_apple.append(distance)

    return distances_to_apple


def get_moves_that_directly_lead_to_food(data):
    board = data['board']
    food = board['food']
    you = data['you']
    you_head = you['body'][0]

    food_locations = []
    for e in food:
        food_locations.append((e['x'], e['y']))

    moves_that_directly_lead_to_food = []
    for d in directions:
        next_tile = next_field(d, you_head)
        if food_locations.__contains__(next_tile):
            moves_that_directly_lead_to_food.append(d)

    return moves_that_directly_lead_to_food


def get_moves_that_directly_lead_to_tails(data):

    you = data['you']
    you_head = you['body'][0]

    tails = []
    for snake in data['board']['snakes']:
        tails.append(snake['body'][-1])

    moves_that_directly_lead_to_tails = []
    for d in directions:
        next_tile = next_field_dic(d, you_head)
        if tails.__contains__(next_tile):
            moves_that_directly_lead_to_tails.append(d)

    return moves_that_directly_lead_to_tails


def get_best_move_based_on_current_data(data, timeLimit):
    log(data, "##### GET BEST MOVE #####")

    directions_without_direct_death = get_moves_without_direct_death(data)
    log(data, "directions_without_direct_death: "+ str(directions_without_direct_death))

    escapabilty_dic = get_directions_that_are_escapable(data, directions_without_direct_death)

    if not directions_without_direct_death:
        log(data, "No directions without death, so we go up")
        return 'up'
    if len(directions_without_direct_death) == 1:
        log(data, "Only one direction without death, so we go " + directions_without_direct_death[0])
        return directions_without_direct_death[0]


    #TODO, directions with guaranteed head on head collision
    directions_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death)
    log(data, "directions_without_potential_deadly_head_on_head_collision: " + str(directions_without_potential_deadly_head_on_head_collision))

    directions_without_potential_head_on_head_with_longer_snakes = \
        get_moves_without_potential_deadly_head_on_head_collision_with_longer_snakes(data, directions_without_direct_death)
    log(data, "directions_without_potential_head_on_head_with_longer_snakes: " + str(directions_without_potential_head_on_head_with_longer_snakes))

    directions_with_most_space = get_least_constraining_moves(data, directions_without_direct_death)
    log(data, "directions_with_most_space: "+ str(directions_with_most_space))

    directions_with_food = get_moves_that_directly_lead_to_food(data)
    log(data, "moves_that_directly_lead_to_food: " + str(directions_with_food))

    distances_to_center = get_distance_to_center_if_move_is_made(data)
    log(data, "distances_to_center: " + str(distances_to_center))

    if len(data['board']['snakes']) != 1:
        directions_that_lead_to_head_lockdown_min_max = min_max_search_for_moves_without_unavoidable_head_collision(data)
    else:
        directions_that_lead_to_head_lockdown_min_max = []
    log(data, "directions_that_lead_to_head_lockdown_min_max: " + str(directions_that_lead_to_head_lockdown_min_max))

    closest_apple = get_food_im_closest_to(data)
    log(data, "closest_apple: "+ str(closest_apple))

    distances_to_closest_apple = get_distance_to_apple_if_move_is_made(data, closest_apple)
    log(data, "distances_to_closest_apple: "+ str(distances_to_closest_apple))

    directions_with_tails = get_moves_that_directly_lead_to_tails(data)
    log(data, "directions_with_tails: " + str(directions_with_tails))

    move_score_list = []
    points = [0, 0, 0, 0]
    for d, score, distance_to_center, distance_to_apple in zip(directions, points, distances_to_center, distances_to_closest_apple):
        if directions_without_direct_death.__contains__(d):
            score += 100000000000
        if d not in escapabilty_dic['sure_death']:
            score += 10000000000
        if d in escapabilty_dic['sure_life']:
            score += 1000000000
        #TODO verify if it is actually a good idead to remove
        #if directions_with_most_space.__contains__(d):
            #score += 100000000
        if directions_without_potential_head_on_head_with_longer_snakes.__contains__(d):
            score += 10000000
        if directions_without_potential_deadly_head_on_head_collision.__contains__(d):
            score += 1000000
        if not directions_that_lead_to_head_lockdown_min_max.__contains__(d):
            score += 100000
        if closest_apple and data['you']['health'] < 100:
            score += 10000 - distance_to_apple*500
            #TODO remove assertion before using in tournament
            #assert 10000 - distance_to_apple*500 > 100
        if True:  # distance to center points
            score += 1000 - distance_to_center*20  # needs to always be bigger than 0
        if directions_with_tails.__contains__(d):
            score += 100
        if directions_with_food.__contains__(d):
            score += 10
        move_score_list.append((d, score))

    create_map_with_duration(data)
    create_map_with_reachtime(data, data['you'])
    move_score_list.sort(key=itemgetter(1), reverse=True)


    deadly_moves, winning_moves, available_moves = simple_best_move(data, timeLimit)
    if winning_moves:
        return random.choice(winning_moves)
    elif available_moves:
        for move in move_score_list:
            if move[0] in deadly_moves:
                move_score_list.remove(move)
                move = (move[0], 0)
                move_score_list.append(move)


    # use randomness to avoid being stuck in a loop
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])

    log(data, 'move_score_list' + str(move_score_list))
    log(data, 'equivalent_best_moves' + str(equivalent_best_moves))
    return random.choice(equivalent_best_moves)


def get_distance_to_center(data, position):
    board = data['board']
    height = board['height']
    width = board['width']
    center = ((width-1)/2.0, (height-1)/2.0)
    x1 = center[0]
    y1 = center[1]
    x2 = position['x']
    y2 = position['y']
    distance = pow(pow((x2 - x1), 2) + pow((y2 - y1), 2), 0.5)
    return distance


def get_distance_between_two_points(point1, point2):
    x1 = point1['x']
    y1 = point1['y']
    x2 = point2['x']
    y2 = point2['y']
    distance = pow(pow((x2 - x1), 2) + pow((y2 - y1), 2), 0.5)
    return distance


def get_board_distance_between_two_points(point1, point2):
    x1 = point1['x']
    y1 = point1['y']
    x2 = point2['x']
    y2 = point2['y']
    distance = abs(x2-x1) + abs(y2-y1)
    return distance


def get_head_distance(snake1, snake2):
    return get_distance_between_two_points(snake1['body'][0], snake2['body'][0])


def get_directions_that_lead_towards_the_center(data):
    directions_that_lead_to_center = []
    you_head = data['you']['body'][0]
    current_distance_to_center = get_distance_to_center(data, you_head)
    smallest_distance_to_center = 1000
    for d in directions:
        next_tile = next_field_dic(d, you_head)
        if get_distance_to_center(data, next_tile) < smallest_distance_to_center:
            smallest_distance_to_center = get_distance_to_center(data, next_tile)

    for d in directions:
        next_tile = next_field_dic(d, you_head)
        if get_distance_to_center(data, next_tile) == smallest_distance_to_center:
            directions_that_lead_to_center.append(d)

    return directions_that_lead_to_center


def get_distance_to_center_if_move_is_made(data):
    distances_to_center = []
    you_head = data['you']['body'][0]
    for d in directions:
        next_tile = next_field_dic(d, you_head)
        distance = get_distance_to_center(data, next_tile)
        distances_to_center.append(distance)

    return distances_to_center


def get_best_move_min_max(data, depth):
    if not get_moves_without_direct_death(data):
        return 'up'

    move_score_list = []
    for move in get_moves_without_direct_death(data):
        move_score_list.append((move, min_value(data, depth, move)))

    move_score_list.sort(key=itemgetter(1), reverse=True)
    # use randomness to avoid being stuck in a loop
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])
    return random.choice(equivalent_best_moves)


def remove_all_snakes_that_are_far_away(data_original):
    data = copy.deepcopy(data_original)
    for snake in data_original['board']['snakes']:
        if get_distance_between_two_points(data['you']['body'][0], snake['body'][0]) >= 3.5:
            data['board']['snakes'].remove(snake)


def min_max_search_for_moves_without_unavoidable_head_collision(data):
    directions_without_direct_death = get_moves_without_direct_death(data)
    directions_that_lead_to_potential_unavoidable_head_on_head = []

    for my_move in directions_without_direct_death:
        possible_move_combinations = get_possible_moves_for_all_nearby_snakes(data, my_move)
        for possibility in possible_move_combinations:
            updated = game_engine.update(copy.deepcopy(data), possibility)
            not_deadly_moves_in_update = get_moves_without_direct_death(updated)
            if not get_moves_without_potential_deadly_head_on_head_collision(updated, not_deadly_moves_in_update):
                directions_that_lead_to_potential_unavoidable_head_on_head.append(my_move)
                break

    return directions_that_lead_to_potential_unavoidable_head_on_head


def create_map_with_duration(data):
    time_tiles_are_blocked = []
    for x in range(data['board']['width']):
        time_tiles_are_blocked.append([])
        for y in range(data['board']['height']):
            time_tiles_are_blocked[x].append(0)

    #Do head separately
    for snake in data['board']['snakes']:
        durations = range(len(snake['body']))
        durations.reverse()
        for body_part, position in zip(snake['body'], durations):
            time_tiles_are_blocked[int(body_part['x'])][int(body_part['y'])] = position

    return time_tiles_are_blocked


def create_map_with_reachtime(data, snake):
    time_to_reach_tile = []
    for x in range(data['board']['width']):
        time_to_reach_tile.append([])
        for y in range(data['board']['height']):
            time_to_reach_tile[x].append('inf')

    start = snake['body'][0]
    time_to_reach_tile[start['x']][start['y']] = 0
    visited = []
    queue = [start]
    width = data['board']['width']
    height = data['board']['height']
    deadly_locations = get_deadly_locations_dic(data)

    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for d in directions:
            cur_neighbour = next_field_dic(d, cur)
            if cur_neighbour not in visited and cur_neighbour not in queue:
                if not_deadly_location_on_board_dic(cur_neighbour, deadly_locations, width, height):
                    queue.append(cur_neighbour)
                    distance_to_head = time_to_reach_tile[cur['x']][cur['y']]
                    time_to_reach_tile[cur_neighbour['x']][cur_neighbour['y']] = distance_to_head + 1

    return time_to_reach_tile


def tiles_others_can_reach_before_me(data):
    width = data['board']['width']
    height = data['board']['height']
    snake_map_dic = {}
    list_of_tiles_others_reach_before_me = []

    for snake in data['board']['snakes']:
        reach_time_map = create_map_with_reachtime(data, snake)
        snake_map_dic[snake['id']] = reach_time_map

    for x in range(width):
        for y in range(height):
            tile = {'x':x, 'y':y}
            if not i_reach_tile_first(tile, snake_map_dic, data):
                list_of_tiles_others_reach_before_me.append(tile)

    return list_of_tiles_others_reach_before_me


def i_reach_tile_first(tile, snake_map_dic, data):
    for snake in data['board']['snakes']:
        if snake == data['you']:
            continue
        else:
            my_reach_time = snake_map_dic[data['you']['id']][tile['x']][tile['y']]
            enemy_reach_time = snake_map_dic[snake['id']][tile['x']][tile['y']]

            if my_reach_time > enemy_reach_time:
                return False
            if my_reach_time == enemy_reach_time:
                if not len(data['you']['body']) > len(snake['body']):
                    return False
    return True


def get_directions_that_are_probably_too_tight(data):
    directions_that_are_probably_too_tight = []
    for d in get_moves_without_direct_death(data):
        new_theoretical_head = next_field_dic(d, data['you']['body'][0])
        if get_number_of_reachable_tiles(data, new_theoretical_head) < len(data['you']['body']):
            directions_that_are_probably_too_tight.append(d)
    return directions_that_are_probably_too_tight


def check_if_space_is_escapable(data, head):
    number_of_tiles = get_number_of_reachable_tiles(data, head)
    escape_points, escape_timings = get_escape_points(data, head)
    #TODO take snake length into account
    #Maybe not necessary ?
    #print("For head " , head, "there are ", number_of_tiles, " tiles and min(escape_timings)= ", min(escape_timings) )

    return min(escape_timings) <= number_of_tiles


def get_directions_that_are_escapable(data, directions_without_direct_death):
    #TODO mostly fails when food is involved
    #Eg, i could escape on a path if the snakes ate no food
    sure_death = []
    sure_life = []
    unknown_survival = []
    for direction in directions_without_direct_death:
        new_head = next_field_dic(direction, data['you']['body'][0])
        escape = find_way_out(data, new_head)

        if escape == "Cannot escape" or escape is None:
            sure_death.append(direction)
        elif escape == "Time limit":
            unknown_survival.append(direction)
        else:
            #either can reach tail or a path
            sure_life.append(direction)

    log(data, ("sure_death= " + str(sure_death)))
    log(data, ("sure_life= " + str(sure_life)))
    log(data, ("unknown= " + str(unknown_survival)))

    return {'sure_death':sure_death, 'sure_life':sure_life, 'unknown_survival':unknown_survival}


def get_escape_points(data, start_tile):
    duration_map = create_map_with_duration(data)
    escape_points = []
    escape_timings = []

    visited = []
    queue = [start_tile]
    width = data['board']['width']
    height = data['board']['height']
    deadly_locations = get_deadly_locations_dic(data)

    if on_board(start_tile, data):
        escape_points.append(start_tile)
        escape_timings.append(duration_map[start_tile['x']][start_tile['y']])

    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for d in directions:
            cur_neighbour = next_field_dic(d, cur)
            if cur_neighbour not in visited and cur_neighbour not in queue:
                if not_deadly_location_on_board_dic(cur_neighbour, deadly_locations, width, height):
                    queue.append(cur_neighbour)
                else:
                    if on_board(cur_neighbour, data):
                        escape_points.append(cur_neighbour)
                        escape_timings.append(duration_map[cur_neighbour['x']][cur_neighbour['y']])

    return escape_points, escape_timings



def i_can_reach_a_tail(data, start):
    reachable = list_of_reachable_tiles_dic(data, (start['x'], start['y']))
    tails = []
    for snake in data['board']['snakes']:
        tails.append(snake['body'][-1])
        if snake['body'][-1] in reachable:
            return True

    return False


def find_way_out(data, start):

    if i_can_reach_a_tail(data, start):
        return "Can reach a tail"

    if not check_if_space_is_escapable(data, start):
        return "Cannot escape"

    timeFrame= 0.1
    escape_points, escape_timings = get_escape_points(data, start)

    timeEnd = time.time() + timeFrame
    time_start  = time.time()
    escape_path = breadth_first_saving_path_search(data, [start], escape_points, escape_timings, timeEnd)

    #Cancelled because time
    if time.time() - time_start > timeFrame:
        if not escape_path:
            escape_path = "Time limit"

    return escape_path


def breadth_first_saving_path_search(data, path, escape_points, escape_timings, time_limit):
    if time.time() > time_limit:
        return None

    directions_to_explore = []
    for d in directions:
        next_tile = next_field_dic(d, path[-1])

        if not on_board(next_tile, data):
            continue
        if next_tile in path:
            continue
        if next_tile in escape_points:
            corresponding_timing = escape_timings[escape_points.index(next_tile)]
            if len(path) > corresponding_timing:
                path.append(next_tile)
                return path
        else:
            directions_to_explore.append(d)

    for d in directions_to_explore:
        next_tile = next_field_dic(d, path[-1])
        new_path = copy.deepcopy(path)
        new_path.append(next_tile)
        follower_result = breadth_first_saving_path_search(data, new_path, escape_points, escape_timings, time_limit)

        if follower_result:
            return follower_result

    return None


def number_of_free_tiles(data):
    empty_tiles = []
    for x in range(data['board']['width']):
        for y in range(data['board']['height']):
            empty_tiles.append({'x': x, 'y': y})
    for snake in data['board']['snakes']:
        for location in snake['body']:
            if location in empty_tiles:
                empty_tiles.remove(location)
    return len(empty_tiles)


def get_map_of_head_danger(data):
    board = data['board']
    width = board['width']
    height = board['height']
    snakes = board['snakes']
    you = data['you']
    you_head = you['body'][0]
    danger_zone = 5

    deadly_enemy_heads = []
    for snake in snakes:
        if snake['body'] != you['body'] and len(snake['body']) >= len(you['body']):
            deadly_enemy_heads.append(snake['body'][0])

    danger_map = []
    for x in range(data['board']['width']):
        danger_map.append([])
        for y in range(data['board']['height']):
            danger_map[x].append(0)
    fill_danger_map(data, danger_map)
    return danger_map


def fill_danger_map(data, danger_map):
    board = data['board']
    snakes = board['snakes']
    width = board['width']
    height = board['height']
    you = data['you']

    for snake in snakes:
        if snake != you and len(snake['body']) >= len(you['body']):
            enemy_head = snake['body'][0]
            for x in range(width):
                for y in range(height):
                    danger_map[x][y] += max(0, 6-get_board_distance_between_two_points({'x': x, 'y': y}, enemy_head))
                   #danger_map[x][y] = min(abs(5-danger_map[x][y]), 5)


evaluation_count = 0
def evaluate_position(data):
    global evaluation_count
    evaluation_count += 1
    #print(evaluation_count)
    if not data['board']['snakes']:
        return 0.5
    #print(im_dead(position))
    # print(position)
    # print(get_moves_without_direct_death(position))
    #print(not get_moves_without_direct_death(position))
    my_head = (data['you']['body'][0]['x'], data['you']['body'][0]['y'])
    width = data['board']['width']
    height = data['board']['height']
    #print(float(len(list_of_reachable_tiles(my_head, get_deadly_locations(data), width, height)))/number_of_free_tiles(data))
    #print(len(list_of_reachable_tiles(my_head, get_deadly_locations(data), width, height)), number_of_free_tiles(data))
    if len(list_of_reachable_tiles(my_head, get_deadly_locations(data), width, height)) < len(data['you']['body']):
        return float(len(list_of_reachable_tiles(my_head, get_deadly_locations(data), width, height)))/(width*height)
    elif not get_moves_without_potential_deadly_head_on_head_collision(data, get_moves_without_direct_death(data)):
        return 0.5
    else:
        return 1


def im_dead(data):
    board = data['board']
    snakes = board['snakes']
    you = data['you']

    for snake in snakes:
        if snake['id'] == you['id']:
            return False
    return True


def get_possible_moves_for_all_snakes(data, my_move):
    snakes = data['board']['snakes']
    my_snake = data['you']
    possible_moves = []

    for snake in snakes:
        if snake == my_snake:
            possible_moves.append([my_move])
        else:
            data['you'] = snake
            moves_without_direct_death = get_moves_without_direct_death(data)
            if not moves_without_direct_death:
                possible_moves.append(['up'])
            else:
                possible_moves.append(moves_without_direct_death)
    data['you'] = my_snake

    #print(possible_moves)
    all_possible_combinations = list(itertools.product(*possible_moves))
    return all_possible_combinations


def get_possible_moves_for_all_nearby_snakes(data, my_move):
    snakes = data['board']['snakes']
    my_snake = data['you']
    possible_moves = []

    for snake in snakes:
        if snake == my_snake:
            possible_moves.append([my_move])
        else:
            data['you'] = snake
            moves_without_direct_death = get_moves_without_direct_death(data)
            if not moves_without_direct_death:
                possible_moves.append(['up'])
            elif get_head_distance(my_snake, snake) >= 3.5:  # if he is far away
                moves_without_potential_head_collision =\
                    get_moves_without_potential_deadly_head_on_head_collision(data, moves_without_direct_death)
                if moves_without_potential_head_collision:
                    possible_moves.append([random.choice(moves_without_potential_head_collision)])
                else:
                    possible_moves.append([random.choice(moves_without_direct_death)])
            else:
                possible_moves.append(moves_without_direct_death)
    data['you'] = my_snake

    #print(possible_moves)
    all_possible_combinations = list(itertools.product(*possible_moves))
    return all_possible_combinations



def min_value(position, depth, my_move):
    child_scores = []
    for move_combination in get_possible_moves_for_all_snakes(position, my_move):
        updated_position = game_engine.update(position, move_combination)
        child_scores.append(max_value(updated_position, depth-1))

    # print('min', depth, child_scores)
    return min(child_scores)


def max_value(data, depth):
    if im_dead(data) or not get_moves_without_direct_death(data):
        return 0
    if len(data['board']['snakes']) == 1:
        return 1000000
    if depth == 0:
        return evaluate_position(data)
    else:
        child_scores = []
        for move in get_moves_without_direct_death(data):
            child_scores.append(min_value(data, depth, move))

        # print(position['turn'], position['you']['name'], depth, max(child_scores), child_scores, get_moves_without_direct_death(position))

        # print('max', depth, get_moves_without_direct_death(position), child_scores)
        return max(child_scores)


def simple_evaluation(data):
    if im_dead(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    else:
        return 0.5


def simple_max_value(data, depth, timeLimit):
    if im_dead(data) or not get_moves_without_direct_death(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    if depth == 0:
        return simple_evaluation(data)
    else:
        child_scores = []
        for move in get_moves_without_direct_death(data):
            if time.time() > timeLimit:
                return "cancel"
            child_scores.append(simple_min_value(data, depth, move, timeLimit))

        position = data
        #print(position)
        #print(position['turn'], position['you']['name'], depth, max(child_scores), child_scores, get_moves_without_direct_death(position))

        #print('max', depth, get_moves_without_direct_death(position), child_scores)
        return max(child_scores)


def simple_min_value(position, depth, my_move, timeLimit):
    child_scores = []
    for move_combination in get_possible_moves_for_all_snakes(position, my_move):
        if time.time() > timeLimit:
            return "cancel"
        updated_position = game_engine.update(position, move_combination)
        child_scores.append(simple_max_value(updated_position, depth-1, timeLimit))

    #print('min', depth, child_scores)
    return min(child_scores)


def simple_best_move(data, timeLimit):
    available_moves = ['up', 'down', 'left', 'right']
    deadly_moves = []
    winning_moves = []

    depth = 0
    while available_moves:
        depth += 1
        log(data, "Reached depth " + str(depth))
        for move in available_moves:
            simple_score = simple_min_value(data, depth, move, timeLimit)
            if simple_score == 0:
                available_moves.remove(move)
                deadly_moves.append(move)
            elif simple_score == 1:
                available_moves.remove(move)
                winning_moves.append(move)
            elif simple_score == 0.5:
                pass
            else:
                assert simple_score == "cancel"
                return deadly_moves, winning_moves, available_moves
    return deadly_moves, winning_moves, available_moves


