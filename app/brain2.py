import random
import time
import itertools
from operator import itemgetter
import Game_object_pool
import game_engine
import copy
import settings

try:
    from printer import Logger

    def log(turn, snake, message):
        Logger().log(turn, snake, message)

    def log(data, message):
        Logger().log(data['turn'], data['you'], message)

# I don't wanna log all when in ranked, so i dont push the logger
except ImportError:
    def log(turn, snake, message):
        # print(message)
        pass

    def log(data, message):
        # print(message)
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


Priotities:
1) Improve min max with space
2) Fix min max head on head
3) Don't follow tails if you die if enemy eats food
4) Fix escape path with food
5) Fix escape path generally
6) Find source of timeouts
7) when 50/50 head  on head chooses path where other is less likely to go
8) I can check if i can escape by reaching a thing before him, but that does not imply i do it
9) have exactly 11*11 tiles items that get reused everywhere

Starvation rule 
You need a fixed thing for 8 snakes
And a minimax for 1v1
Then replace deepcopy by pooling

As for escaping:
I need - A fast heuristik on wether a space is escapable
-An exact one
-One that gives the path

-time window to search for escape path ?

-dont follow tails in ways that make you die if the snake eats food

Zone where im dead       - Zone where im alive
######################## - ###################

check_if_space_is_escapable
FFFFFFFFF TTTTTTTTTTTTTT   TTTTTTTTTTTTTTTTTTT

I need a function with Tail reachability
FFFFFFFFFFFFFFFFFFFFFFFF   FFFFFFFFFTTTTTTTTTT



-maybe if only 1 path, update
-Ita about being able to reach a tail


-Need early game improvement
-Improve min max for head lockdown so take moves into account i wont play

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


def neighbour_tile(direction, current_position):
    if direction == 'up':
        return {'x': current_position['x'], 'y': current_position['y'] - 1}
    elif direction == 'down':
        return {'x': current_position['x'], 'y': current_position['y'] + 1}
    elif direction == 'left':
        return {'x': current_position['x'] - 1, 'y': current_position['y']}
    elif direction == 'right':
        return {'x': current_position['x'] + 1, 'y': current_position['y']}


def not_deadly_location_on_board(goal, data, deadly_locations):
    if not on_board(goal, data):
        return False
    if goal in deadly_locations:
        return False
    return True


def on_board(tile, data):
    width = data['board']['width']
    height = data['board']['height']
    if tile['x'] < 0 or tile['x'] >= width or tile['y'] < 0 or tile['y'] >= height:
        return False
    return True


def list_of_reachable_tiles(start, data, deadly_locations):
    visited = []
    queue = [start]

    while queue:
        cur_tile = queue.pop(0)
        visited.append(cur_tile)
        for direction in directions:
            cur_neighbour = neighbour_tile(direction, cur_tile)
            if cur_neighbour not in visited and cur_neighbour not in queue:
                if not_deadly_location_on_board(cur_neighbour, data, deadly_locations):
                    queue.append(cur_neighbour)

    return visited


def list_of_reachable_tiles_with_tail_fix(start, data, deadly_locations):
    deadly_locations = copy.deepcopy(deadly_locations)
    for snake in data['board']['snakes']:
        tail = snake['body'][-1]
        if tail in deadly_locations:
            # TODO FIx, tails don't count as reachable if food has been eaten and yournext to them
            # YOu could still reach them with a longer path
            if get_board_distance_between_two_points(start, tail) > 1:
                deadly_locations.remove(tail)

    reachable_tile_list = list_of_reachable_tiles(start, data, deadly_locations)
    return reachable_tile_list


def get_number_of_reachable_tiles(data, head):
    deadly_locations = get_deadly_locations(data)
    return len(list_of_reachable_tiles(head, data, deadly_locations))


def get_deadly_locations(data):
    board = data['board']
    snakes = board['snakes']

    deadly_locations = []
    for snake in snakes:
        for body_part in snake['body'][:-1]:
            deadly_locations.append(body_part)

    return deadly_locations


def get_moves_without_direct_death(data, *snake):
    you_before = data['you']

    if snake:
        snake = snake[0]
        data['you'] = snake

    you = data['you']
    you_head = you['body'][0]

    deadly_locations = get_deadly_locations(data)

    directions_without_direct_death = ['up', 'down', 'left', 'right']

    for d in directions:
        next_tile = neighbour_tile(d, you_head)
        if not not_deadly_location_on_board(next_tile, data, deadly_locations):
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
            possible_deadly_head_on_head_collision.append(neighbour_tile(d, head))

    directions_without_deadly_head_on_head_collision = []
    for d in directions_without_direct_death:
        next_tile = neighbour_tile(d, you_head)
        if next_tile not in possible_deadly_head_on_head_collision:
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
            possible_deadly_head_on_head_collision.append(neighbour_tile(d, head))

    directions_without_deadly_head_on_head_collision = []
    for d in directions_without_direct_death:
        next_tile = neighbour_tile(d, you_head)
        if next_tile not in possible_deadly_head_on_head_collision:
            directions_without_deadly_head_on_head_collision.append(d)

    return directions_without_deadly_head_on_head_collision


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
        my_distance = get_bird_distance_between_two_points(you_head, apple)
        for snake in board['snakes']:
            if snake == you:
                continue
            his_distance = get_bird_distance_between_two_points(snake['body'][0], apple)
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
        next_tile = neighbour_tile(d, you_head)
        distance = get_bird_distance_between_two_points(next_tile, apple)
        distances_to_apple.append(distance)

    return distances_to_apple


def get_moves_that_directly_lead_to_food(data):
    board = data['board']
    food = board['food']
    you = data['you']
    you_head = you['body'][0]

    moves_that_directly_lead_to_food = []
    for d in directions:
        next_tile = neighbour_tile(d, you_head)
        if next_tile in food:
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
        next_tile = neighbour_tile(d, you_head)
        if next_tile in tails:
            moves_that_directly_lead_to_tails.append(d)

    return moves_that_directly_lead_to_tails


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


def get_bird_distance_between_two_points(point1, point2):
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
    return get_bird_distance_between_two_points(snake1['body'][0], snake2['body'][0])


def get_directions_that_lead_towards_the_center(data):
    directions_that_lead_to_center = []
    you_head = data['you']['body'][0]
    smallest_distance_to_center = 1000
    for d in directions:
        next_tile = neighbour_tile(d, you_head)
        if get_distance_to_center(data, next_tile) < smallest_distance_to_center:
            smallest_distance_to_center = get_distance_to_center(data, next_tile)

    for d in directions:
        next_tile = neighbour_tile(d, you_head)
        if get_distance_to_center(data, next_tile) == smallest_distance_to_center:
            directions_that_lead_to_center.append(d)

    return directions_that_lead_to_center


def get_distance_to_center_if_move_is_made(data):
    distances_to_center = []
    you_head = data['you']['body'][0]
    for d in directions:
        next_tile = neighbour_tile(d, you_head)
        distance = get_distance_to_center(data, next_tile)
        distances_to_center.append(distance)

    return distances_to_center


def min_max_search_for_moves_without_unavoidable_head_collision(data, time_limit):
    # TODO Instore time limit
    directions_without_direct_death = get_moves_without_direct_death(data)
    directions_that_lead_to_potential_unavoidable_head_on_head = []

    for my_move in directions_without_direct_death:
        possible_move_combinations = get_possible_moves_for_all_nearby_snakes(data, my_move)
        for possibility in possible_move_combinations:
            if time.time() > time_limit:
                log(data, "Incomplete min_max for unavoidable head on head")
                return directions_that_lead_to_potential_unavoidable_head_on_head

            updated = game_engine.pool_update(copy.deepcopy(data), possibility)
            not_deadly_moves_in_update = get_moves_without_direct_death(updated)
            moves_without_potential_deadly_head_on_head_collision = \
                get_moves_without_potential_deadly_head_on_head_collision(updated, not_deadly_moves_in_update)
            Game_object_pool.GamePool().return_object(updated)

            if not moves_without_potential_deadly_head_on_head_collision:
                directions_that_lead_to_potential_unavoidable_head_on_head.append(my_move)
                break

    return directions_that_lead_to_potential_unavoidable_head_on_head


def create_map_with_duration(data):
    time_tiles_are_blocked = []
    for x in range(data['board']['width']):
        time_tiles_are_blocked.append([])
        for y in range(data['board']['height']):
            time_tiles_are_blocked[x].append(0)

    # Do head separately
    for snake in data['board']['snakes']:
        durations = range(len(snake['body']))
        durations.reverse()
        for body_part, position in zip(snake['body'], durations):
            cur = time_tiles_are_blocked[int(body_part['x'])][int(body_part['y'])]
            time_tiles_are_blocked[int(body_part['x'])][int(body_part['y'])] = max(position, cur)

    return time_tiles_are_blocked


def create_map_with_reachtime(data, start_direction, snake, duration_map):
    time_to_reach_tile = []
    for x in range(data['board']['width']):
        time_to_reach_tile.append([])
        for y in range(data['board']['height']):
            time_to_reach_tile[x].append('inf')

    start = snake['body'][0]
    time_to_reach_tile[start['x']][start['y']] = 0
    visited = []
    queue = [start]

    if start_direction:
        first_tile = neighbour_tile(start_direction, start)
        time_to_reach_tile[first_tile['x']][first_tile['y']] = 1
        queue = [first_tile]

    deadly_locations = get_deadly_locations(data)

    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for d in directions:
            cur_neighbour = neighbour_tile(d, cur)
            if cur_neighbour not in visited and cur_neighbour not in queue:
                if not_deadly_location_on_board(cur_neighbour, data, deadly_locations):
                    queue.append(cur_neighbour)
                    distance_to_head = time_to_reach_tile[cur['x']][cur['y']]
                    time_to_reach_tile[cur_neighbour['x']][cur_neighbour['y']] = distance_to_head + 1

                elif on_board(cur_neighbour, data):
                    duration = duration_map[cur_neighbour['x']][cur_neighbour['y']]
                    distance_to_head = time_to_reach_tile[cur['x']][cur['y']]
                    if distance_to_head + 1 > duration:
                        queue.append(cur_neighbour)
                        time_to_reach_tile[cur_neighbour['x']][cur_neighbour['y']] = distance_to_head + 1

    return time_to_reach_tile


def tiles_others_can_reach_before_me(data):
    width = data['board']['width']
    height = data['board']['height']
    snake_map_dic = {}
    list_of_tiles_others_reach_before_me = []

    normal_duration_map = create_map_with_duration(data)
    # TODO is that deepcopy here really necessary ?
    duration_map_if_enemy_moves_to_tile = copy.deepcopy(normal_duration_map)

    for snake in data['board']['snakes']:
        reach_time_map = create_map_with_reachtime(data, None, snake, normal_duration_map)
        snake_map_dic[snake['id']] = reach_time_map

    for x in range(width):
        for y in range(height):
            tile = {'x': x, 'y': y}
            im_first_to_tile, enemy_duration = i_reach_tile_first(tile, snake_map_dic, data)
            if not im_first_to_tile:
                list_of_tiles_others_reach_before_me.append(tile)
                duration_map_if_enemy_moves_to_tile[x][y] = enemy_duration

    return list_of_tiles_others_reach_before_me, duration_map_if_enemy_moves_to_tile


def create_map_with_reachtime_for_all_snakes(data, duration_map):
    start = time.time()
    reach_tile_data = initialise_reachtime_data(data)

    queue = []
    next_queue = []
    visited_in_current_iteration = []
    previously_visited = []
    deadly_locations = get_deadly_locations(data)

    for snake in data['board']['snakes']:
        head = snake['body'][0]
        queue.append(head)

    while queue:
        cur = queue.pop(0)
        visited_in_current_iteration.append(cur)
        expand_node(data, cur, reach_tile_data, next_queue, duration_map, previously_visited, deadly_locations)

        if not queue:
            queue = next_queue
            next_queue = []
            previously_visited = previously_visited + visited_in_current_iteration
            visited_in_current_iteration = []

    #print("time", time.time()-start)
    return reach_tile_data


def initialise_reachtime_data(data):
    reach_tile_data = []
    for x in range(data['board']['width']):
        reach_tile_data.append([])
        for y in range(data['board']['height']):
            reach_tile_data[x].append({'snake': None, 'reach_time': None, 'duration': None})

    for snake in data['board']['snakes']:
        head = snake['body'][0]
        reach_tile_data[head['x']][head['y']]['snake'] = snake
        reach_tile_data[head['x']][head['y']]['reach_time'] = 0
        reach_tile_data[head['x']][head['y']]['duration'] = len(snake['body']) - 1

    return reach_tile_data


def expand_node(data, cur, reach_tile_data, next_queue, duration_map, previously_visited, deadly_locations):
    for d in directions:
        cur_neighbour = neighbour_tile(d, cur)

        if on_board(cur_neighbour, data):
            # if it is in previously visited, another snakes reaches it quicker
            if cur_neighbour not in previously_visited:
                cur_data_for_cur_tile = reach_tile_data[cur['x']][cur['y']]
                cur_data_for_neighbour = reach_tile_data[cur_neighbour['x']][cur_neighbour['y']]

                if this_snake_if_first_or_bigger(data, cur_data_for_cur_tile, cur_data_for_neighbour):
                    if not_deadly_location_on_board(cur_neighbour, data, deadly_locations):
                        set_reach_time_data_for_neighbour_tile(cur_data_for_neighbour, cur_data_for_cur_tile,
                                                               next_queue, cur_neighbour)

                    elif on_board(cur_neighbour, data):
                        duration = duration_map[cur_neighbour['x']][cur_neighbour['y']]
                        distance_to_head = cur_data_for_cur_tile['reach_time']
                        if distance_to_head + 1 > duration:
                            set_reach_time_data_for_neighbour_tile(cur_data_for_neighbour, cur_data_for_cur_tile,
                                                                   next_queue, cur_neighbour)


def this_snake_if_first_or_bigger(data, cur_data_for_cur_tile, cur_data_for_neighbour):
    if not cur_data_for_neighbour['snake']:
        return True
    else:
        # Maybe add a thing where your snake considers tiles it can reach at the same time as others as not good
        return len(cur_data_for_cur_tile['snake']['body']) > len(cur_data_for_neighbour['snake']['body'])


def set_reach_time_data_for_neighbour_tile(cur_data_for_neighbour, cur_data_for_cur_tile, next_queue, cur_neighbour):
    cur_data_for_neighbour['snake'] = cur_data_for_cur_tile['snake']
    cur_data_for_neighbour['reach_time'] = cur_data_for_cur_tile['reach_time'] + 1
    cur_data_for_neighbour['duration'] = cur_data_for_cur_tile['duration'] + 1

    if cur_neighbour not in next_queue:
        next_queue.append(cur_neighbour)


def i_reach_tile_first(tile, snake_map_dic, data):
    # TODO Inaccurate because duration is taken from first snake the reaches tile in loop
    # not necessarily the first in the game to reach it
    for snake in data['board']['snakes']:
        if snake == data['you']:
            continue
        else:
            my_reach_time = snake_map_dic[data['you']['id']][tile['x']][tile['y']]
            enemy_reach_time = snake_map_dic[snake['id']][tile['x']][tile['y']]

            if enemy_reach_time == 'inf':
                continue
            if my_reach_time == 'inf':
                return False, enemy_reach_time + len(snake['body'])

            if my_reach_time > enemy_reach_time:
                return False, enemy_reach_time + len(snake['body'])
            if my_reach_time == enemy_reach_time:
                if not len(data['you']['body']) > len(snake['body']):
                    return False, enemy_reach_time + len(snake['body'])
    return True, -1


def check_if_space_is_escapable(data, head, escape_points, escape_timings):
    number_of_tiles = get_number_of_reachable_tiles(data, head)
    return min(escape_timings) <= number_of_tiles


def get_directions_that_are_escapable(data, directions_without_direct_death, time_limit):
    # Checks which directions are escapable assuming enemy snakes don't move
    # TODO mostly fails when food is involved
    # Eg, i could escape on a path if the snakes ate no food
    sure_death = []
    sure_life = []
    unknown_survival = []
    for direction in directions_without_direct_death:
        new_head = neighbour_tile(direction, data['you']['body'][0])

        deadly_locations = get_deadly_locations(data)
        deadly_locations_dic = get_deadly_locations(data)
        duration_map = create_map_with_duration(data)
        escape_points, escape_timings = get_escape_points(data, new_head, deadly_locations_dic, duration_map)

        escape = find_way_out(data, new_head, deadly_locations, escape_points, escape_timings, time_limit)

        if escape == "Cannot escape" or escape is None:
            sure_death.append(direction)
        elif escape == "Time limit":
            unknown_survival.append(direction)
        else:
            # either can reach tail or a path
            sure_life.append(direction)

    return {'sure_death': sure_death, 'sure_life': sure_life, 'unknown_survival': unknown_survival}


def get_escape_points(data, start_tile, deadly_locations, duration_map):
    escape_points = []
    escape_timings = []

    visited = []
    queue = [start_tile]

    if on_board(start_tile, data):
        escape_points.append(start_tile)
        escape_timings.append(duration_map[start_tile['x']][start_tile['y']])

    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for d in directions:
            cur_neighbour = neighbour_tile(d, cur)
            if cur_neighbour not in visited and cur_neighbour not in queue:
                if not_deadly_location_on_board(cur_neighbour, data, deadly_locations):
                    queue.append(cur_neighbour)
                else:
                    if on_board(cur_neighbour, data):
                        escape_points.append(cur_neighbour)
                        escape_timings.append(duration_map[cur_neighbour['x']][cur_neighbour['y']])

    return escape_points, escape_timings


def i_can_reach_a_tail(data, start, deadly_locations):
    reachable = list_of_reachable_tiles_with_tail_fix(start, data, deadly_locations)
    tails = []
    for snake in data['board']['snakes']:
        tails.append(snake['body'][-1])
        if snake['body'][-1] in reachable:
            return True

    return False


def find_way_out(data, start, deadly_locations, escape_points, escape_timings, time_limit):

    if i_can_reach_a_tail(data, start, deadly_locations):
        return "Can reach a tail"

    if not check_if_space_is_escapable(data, start, escape_points, escape_timings):
        return "Cannot escape"

    # TODO make sure min max simple always has 0.2 seconds
    # TODO eventually problems here
    time_frame = 0.05
    time_end = min(time.time() + time_frame, time_limit)
    escape_path = breadth_first_saving_path_search(data, [start], escape_points, escape_timings, time_end)

    # Cancelled because time
    if time.time() > time_end:
        if not escape_path:
            escape_path = "Time limit"

    return escape_path


def breadth_first_saving_path_search(data, path, escape_points, escape_timings, time_limit):
    if time.time() > time_limit:
        return None

    directions_to_explore = []
    for d in directions:
        next_tile = neighbour_tile(d, path[-1])

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
        next_tile = neighbour_tile(d, path[-1])
        new_path = copy.deepcopy(path)
        new_path.append(next_tile)
        follower_result = breadth_first_saving_path_search(data, new_path, escape_points, escape_timings, time_limit)

        if follower_result:
            return follower_result

    return None


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
            elif get_head_distance(my_snake, snake) >= 4.5:  # if he is far away
                moves_without_potential_head_collision =\
                    get_moves_without_potential_deadly_head_on_head_collision(data, moves_without_direct_death)
                if moves_without_potential_head_collision:
                    possible_moves.append([random.choice(moves_without_potential_head_collision)])
                else:
                    possible_moves.append([random.choice(moves_without_direct_death)])
            else:
                possible_moves.append(moves_without_direct_death)
    data['you'] = my_snake

    all_possible_combinations = list(itertools.product(*possible_moves))
    return all_possible_combinations


def simple_evaluation(data):
    global state_count
    state_count += 1
    if im_dead(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    else:
        return 0.5

state_count = 0
def simple_max_value(data, depth, time_limit):
    if im_dead(data) or not get_moves_without_direct_death(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    if depth == 0:
        return simple_evaluation(data)
    else:
        child_scores = []
        for move in get_moves_without_direct_death(data):
            if time.time() > time_limit:
                return "cancel"
            child_scores.append(simple_min_value(data, depth, move, time_limit))
        return max(child_scores)


def simple_min_value(position, depth, my_move, time_limit):
    child_scores = []
    for move_combination in get_possible_moves_for_all_snakes(position, my_move):
        if time.time() > time_limit:
            return "cancel"

        updated_position = game_engine.pool_update(position, move_combination)
        child_scores.append(simple_max_value(updated_position, depth - 1, time_limit))
        Game_object_pool.GamePool().return_object(updated_position)

    return min(child_scores)


def simple_best_move(data, time_limit, depth_limit):
    global state_count
    state_count = 0
    available_moves = ['up', 'down', 'left', 'right']
    deadly_moves = []
    winning_moves = []

    max_depth = 0
    while available_moves and time.time() < time_limit and max_depth < depth_limit:
        max_depth += 1
        log(data, "Reached depth " + str(max_depth))

        # Error if deleting from list while iterating
        loop_moves = copy.deepcopy(available_moves)
        for move in loop_moves:
            simple_score = simple_min_value(data, max_depth, move, time_limit)
            if simple_score == 0:
                available_moves.remove(move)
                deadly_moves.append(move)
            elif simple_score == 1:
                available_moves.remove(move)
                winning_moves.append(move)
            elif simple_score == 0.5:
                pass
            else:
                #assert simple_score == "cancel"
                #TODO remove before tournament
                break

    log(data, "statecount " + str(state_count))
    return deadly_moves, winning_moves, available_moves


alpha_beta_state_count = 0
def alpha_beta_best_move(data, time_limit, depth_limit):
    global alpha_beta_state_count
    alpha_beta_state_count = 0
    available_moves = ['up', 'down', 'left', 'right']
    deadly_moves = []
    winning_moves = []

    max_depth = 0
    while available_moves and time.time() < time_limit and max_depth < depth_limit and not winning_moves:
        max_depth += 1
        log(data, "Reached depth " + str(max_depth))

        # Error if deleting from list while iterating
        loop_moves = copy.deepcopy(available_moves)
        for move in loop_moves:
            simple_score = simple_alphabeta(data, max_depth, -1, 10, move, time_limit)
            if simple_score == 0:
                available_moves.remove(move)
                deadly_moves.append(move)
            elif simple_score == 1:
                available_moves.remove(move)
                winning_moves.append(move)
            elif simple_score == 0.5:
                pass
            else:
                #assert simple_score == "cancel"
                #TODO remove before tournament
                break

    log(data, "statecount alpha beta" + str(alpha_beta_state_count))
    return deadly_moves, winning_moves, available_moves


def simple_alphabeta(data, depth, alpha, beta, my_move, time_limit):
    global alpha_beta_state_count
    if im_dead(data) or not get_moves_without_direct_death(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    if depth == 0:
        alpha_beta_state_count += 1
        return simple_evaluation(data)

    # maximising
    if my_move is None:
        ab_max_value = -1

        for move in get_moves_without_direct_death(data):
            if time.time() > time_limit:
                return "cancel"
            max_child_value = simple_alphabeta(data, depth, alpha, beta, move, time_limit)
            if type(max_child_value) == str:
                return "cancel"

            ab_max_value = max(ab_max_value, max_child_value)
            alpha = max(alpha, ab_max_value)

            if alpha >= beta:
                break  # beta cut-off
        return ab_max_value

    else:
        ab_min_value = 10
        for move_combination in get_possible_moves_for_all_snakes(data, my_move):
            if time.time() > time_limit:
                return "cancel"

            updated_position = game_engine.pool_update(data, move_combination)
            min_child_value = simple_alphabeta(updated_position, depth - 1, alpha, beta, None, time_limit)
            Game_object_pool.GamePool().return_object(updated_position)

            if type(min_child_value) == str:
                return "cancel"

            ab_min_value = min(ab_min_value, min_child_value)
            beta = min(beta, ab_min_value)

            if alpha >= beta:
                break  # alpha cut-off
        return ab_min_value


state_count2 = 0


def evaluation(data):
    global state_count2
    state_count2 += 1
    if im_dead(data):
        return 0
    if len(data['board']['snakes']) == 1:
        return 1
    moves_without_direct_death = get_moves_without_direct_death(data)
    if not moves_without_direct_death:
        return 0
    moves_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, moves_without_direct_death)
    if not moves_without_potential_deadly_head_on_head_collision:
        return 0
    future_escape = get_directions_that_are_escapable_future(data, moves_without_direct_death,
                                                             moves_without_potential_deadly_head_on_head_collision,
                                                             )
    if not future_escape['sure_life'] and not future_escape['unknown_survival']:
        return 0

    else:
        return 0.5


def my_evaluation(data):
    my_snake = data['you']
    my_score = evaluation(data)
    if my_score == 0 or my_score == 1:
        return my_score

    enemy_scores = []
    for snake in data['board']['snakes']:
        if snake == data['you']:
            continue

        data['you'] = snake
        score = evaluation(data)
        enemy_scores.append(score)

    data['you'] = my_snake

    if max(enemy_scores) == 0:
        return 1

    return 0.5


def max_value(data, depth, time_limit):
    if im_dead(data) or not get_moves_without_direct_death(data):
        return 0
    elif len(data['board']['snakes']) == 1:
        return 1
    if depth == 0:
        return evaluation(data)
    else:
        child_scores = []
        for move in get_moves_without_direct_death(data):
            if time.time() > time_limit:
                return "cancel"
            child_scores.append(min_value(data, depth, move, time_limit))
        return max(child_scores)


def min_value(position, depth, my_move, time_limit):
    child_scores = []
    for move_combination in get_possible_moves_for_all_snakes(position, my_move):
        if time.time() > time_limit:
            return "cancel"

        updated_position = game_engine.pool_update(position, move_combination)
        child_scores.append(max_value(updated_position, depth - 1, time_limit))
        Game_object_pool.GamePool().return_object(updated_position)

    return min(child_scores)


def best_move(data, time_limit):
    global state_count2
    state_count2 = 0
    available_moves = ['up', 'down', 'left', 'right']
    deadly_moves = []
    winning_moves = []

    max_depth = 0
    while available_moves and time.time() < time_limit:
        max_depth += 1
        log(data, "Reached depth " + str(max_depth))

        # Error if deleting from list while iterating
        loop_moves = copy.deepcopy(available_moves)
        for move in loop_moves:
            simple_score = min_value(data, max_depth, move, time_limit)
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
                #TODO remove before tournament
                break

    log(data, "deadly_moves2" + str(deadly_moves))
    log(data, "winning_moves2" + str(winning_moves))
    log(data, "available_moves2" + str(available_moves))
    log(data, "Statecount " + str(state_count2))
    return deadly_moves, winning_moves, available_moves


def add_tiles_to_deadly_locations_where_i_would_be_stuck(data, deadly_locations, duration_map_if_enemy_moves_to_tile):
    deadly_locations = copy.deepcopy(deadly_locations)
    for x in range(data['board']['width']):
        for y in range(data['board']['height']):
            tile = {'x': x, 'y': y}
            if tile not in deadly_locations:
                safe_neighbour_count = 0
                neighbour_durations = []
                for d in directions:
                    neighbour = neighbour_tile(d, tile)

                    if not on_board(neighbour, data):
                        continue
                    elif neighbour == data['you']['body'][0]:
                        # TODO might create problems in future, fix
                        safe_neighbour_count += 1
                    elif neighbour in deadly_locations:
                        neighbour_durations.append(duration_map_if_enemy_moves_to_tile[neighbour['x']][neighbour['y']])
                    else:
                        safe_neighbour_count += 1

                if safe_neighbour_count <= 1:
                    deadly_locations.append(tile)
                    duration_map_if_enemy_moves_to_tile[tile['x']][tile['y']] = min(neighbour_durations)

    return deadly_locations, duration_map_if_enemy_moves_to_tile


# FUTURE ESCAPE
def get_directions_that_are_escapable_future(
        data,
        directions_without_direct_death,
        directions_without_potential_head_on_head_collision,
        time_limit):
    # TODO mostly fails when food is involved
    # Eg, i could escape on a path if the snakes ate no food
    sure_death = []
    sure_life = []
    unknown_survival = []

    list_of_tiles_others_reach_before_me, duration_map_if_enemy_moves_to_tile = \
        tiles_others_can_reach_before_me(data)

    deadly_locations = get_deadly_locations(data)
    deadly_locations = deadly_locations + list_of_tiles_others_reach_before_me

    # check for duplicates

    deadly_locations, duration_map_if_enemy_moves_to_tile = \
        add_tiles_to_deadly_locations_where_i_would_be_stuck(
            data, deadly_locations, duration_map_if_enemy_moves_to_tile)

    for direction in directions_without_direct_death:
        if direction in directions_without_potential_head_on_head_collision:
            new_head = neighbour_tile(direction, data['you']['body'][0])

            if new_head in deadly_locations:
                escape = "deadly start"
            else:
                escape_points, escape_timings = \
                    get_escape_points(data, new_head, deadly_locations, duration_map_if_enemy_moves_to_tile)
                escape = find_way_out(data, new_head, deadly_locations, escape_points, escape_timings, time_limit)

        else:
            escape = "Potential head on head"

        if escape == "Cannot escape" or \
                escape is None or \
                escape == "Potential head on head" or \
                escape == "deadly start":
            sure_death.append(direction)
        elif escape == "Time limit":
            unknown_survival.append(direction)
        else:
            # either can reach tail or a path
            sure_life.append(direction)

    return {'sure_death': sure_death, 'sure_life': sure_life, 'unknown_survival': unknown_survival}


# FUTURE ESCAPE
def get_directions_that_are_escapable_future2(
        data,
        directions_without_direct_death,
        directions_without_potential_head_on_head_collision,
        time_limit):
    # TODO mostly fails when food is involved
    # Eg, i could escape on a path if the snakes ate no food
    sure_death = []
    sure_life = []
    unknown_survival = []

    duration_map = create_map_with_duration(data)
    reach_time_data = create_map_with_reachtime_for_all_snakes(data, duration_map)

    deadly_locations = get_deadly_locations(data)

    duration_map_if_enemy_moves_to_tile = []
    for x in range(data['board']['width']):
        duration_map_if_enemy_moves_to_tile.append([])
        for y in range(data['board']['height']):
            duration_map_if_enemy_moves_to_tile[x].append('inf')
            snake = reach_time_data[x][y]['snake']
            if snake:
                duration_map_if_enemy_moves_to_tile[x][y] = reach_time_data[x][y]['duration']
                if snake != data['you']:
                    tile = {'x': x, 'y': y}
                    if tile not in deadly_locations:
                        deadly_locations.append(tile)

    deadly_locations, duration_map_if_enemy_moves_to_tile = \
        add_tiles_to_deadly_locations_where_i_would_be_stuck(
            data, deadly_locations, duration_map_if_enemy_moves_to_tile)

    for direction in directions_without_direct_death:
        if direction in directions_without_potential_head_on_head_collision:
            new_head = neighbour_tile(direction, data['you']['body'][0])

            if new_head in deadly_locations:
                escape = "deadly start"
            else:
                escape_points, escape_timings = \
                    get_escape_points(data, new_head, deadly_locations, duration_map_if_enemy_moves_to_tile)
                escape = find_way_out(data, new_head, deadly_locations, escape_points, escape_timings, time_limit)

        else:
            escape = "Potential head on head"

        if escape == "Cannot escape" or \
                escape is None or \
                escape == "Potential head on head" or \
                escape == "deadly start":
            sure_death.append(direction)
        elif escape == "Time limit":
            unknown_survival.append(direction)
        else:
            # either can reach tail or a path
            sure_life.append(direction)

    return {'sure_death': sure_death, 'sure_life': sure_life, 'unknown_survival': unknown_survival}


def get_best_move_based_on_current_data(data):
    log(data, "##### GET BEST MOVE #####")

    start_time = time.time()
    time_limit = start_time + settings.BASE_TIME

    directions_without_direct_death = get_moves_without_direct_death(data)
    log(data, "directions_without_direct_death: " + str(directions_without_direct_death))

    if not directions_without_direct_death:
        log(data, "No directions without death, so we go up")
        return 'up'
    if len(directions_without_direct_death) == 1:
        log(data, "Only one direction without death, so we go " + directions_without_direct_death[0])
        return directions_without_direct_death[0]

    # TODO, directions with guaranteed head on head collision
    directions_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death)
    log(data, "directions_without_potential_deadly_head_on_head_collision: " +
        str(directions_without_potential_deadly_head_on_head_collision))

    escapabilty_dic = get_directions_that_are_escapable(data, directions_without_direct_death, time_limit)
    log(data, ("sure_death= " + str(escapabilty_dic['sure_death'])))
    log(data, ("sure_life= " + str(escapabilty_dic['sure_life'])))
    log(data, ("unknown= " + str(escapabilty_dic['unknown_survival'])))

    future_escapabilty_dic = get_directions_that_are_escapable_future(
        data,
        directions_without_direct_death,
        directions_without_potential_deadly_head_on_head_collision,
        time_limit)

    log(data, ("sure_death_future= " + str(future_escapabilty_dic['sure_death'])))
    log(data, ("sure_life_future= " + str(future_escapabilty_dic['sure_life'])))
    log(data, ("unknown_future= " + str(future_escapabilty_dic['unknown_survival'])))

    directions_without_potential_head_on_head_with_longer_snakes = \
        get_moves_without_potential_deadly_head_on_head_collision_with_longer_snakes(
            data, directions_without_direct_death)
    log(data, "directions_without_potential_head_on_head_with_longer_snakes: " +
        str(directions_without_potential_head_on_head_with_longer_snakes))

    directions_with_food = get_moves_that_directly_lead_to_food(data)
    log(data, "moves_that_directly_lead_to_food: " + str(directions_with_food))

    distances_to_center = get_distance_to_center_if_move_is_made(data)
    log(data, "distances_to_center: " + str(distances_to_center))

    if len(data['board']['snakes']) != 1:
        directions_that_lead_to_head_lockdown_min_max = \
            min_max_search_for_moves_without_unavoidable_head_collision(data, time_limit)
    else:
        directions_that_lead_to_head_lockdown_min_max = []
    log(data, "directions_that_lead_to_head_lockdown_min_max: " + str(directions_that_lead_to_head_lockdown_min_max))

    closest_apple = get_food_im_closest_to(data)
    log(data, "closest_apple: " + str(closest_apple))

    distances_to_closest_apple = get_distance_to_apple_if_move_is_made(data, closest_apple)
    log(data, "distances_to_closest_apple: " + str(distances_to_closest_apple))

    directions_with_tails = get_moves_that_directly_lead_to_tails(data)
    log(data, "directions_with_tails: " + str(directions_with_tails))

    deadly_moves, winning_moves, available_moves = \
        alpha_beta_best_move(data, start_time + settings.TOTAL_TIME,
                             settings.SIMPLE_ALPHA_BETA_DEPTH_LIMIT)

    log(data, 'deadly_moves ' + str(deadly_moves))
    log(data, 'winning_moves ' + str(winning_moves))
    log(data, 'available_moves ' + str(available_moves))

    move_score_list = []
    points = [0, 0, 0, 0]
    for d, score, distance_to_center, distance_to_apple in \
            zip(directions, points, distances_to_center, distances_to_closest_apple):
        if d in directions_without_direct_death:
            score += 100000000000000
        if d in winning_moves:
            score += 10000000000000
        if d not in deadly_moves:
            score += 1000000000000
        if d in directions_without_potential_head_on_head_with_longer_snakes:
            score += 100000000000
        if d in directions_without_potential_deadly_head_on_head_collision:
            score += 10000000000
        if d not in future_escapabilty_dic['sure_death']:
            score += 1000000000
        if d in future_escapabilty_dic['sure_life']:
            score += 100000000
        if d not in escapabilty_dic['sure_death']:
            score += 10000000
        if d in escapabilty_dic['sure_life']:
            score += 1000000
        if d not in directions_that_lead_to_head_lockdown_min_max:
            score += 100000
        if closest_apple and data['you']['health'] < 100:
            score += 10000 - distance_to_apple*500
        if True:  # distance to center points
            score += 1000 - distance_to_center*20  # needs to always be bigger than 0
        if d in directions_with_tails:
            score += 100
        if d in directions_with_food:
            score += 10
        move_score_list.append((d, score))

    move_score_list.sort(key=itemgetter(1), reverse=True)

    # use randomness to avoid being stuck in a loop
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])

    log(data, 'move_score_list' + str(move_score_list))
    log(data, 'equivalent_best_moves' + str(equivalent_best_moves))
    return random.choice(equivalent_best_moves), move_score_list


def test_alpha_beta(data):
    for depth in range(5):

        # TODO aspiration window

        ab_start_time = time.time()
        alpha_beta_results = alpha_beta_best_move(data, time.time() + 10000000, depth)
        ab_time = time.time() - ab_start_time

        min_max_start_time = time.time()
        min_max_results = simple_best_move(data, time.time() + 100000000, depth)
        min_max_time = time.time() - min_max_start_time

        print("Turn", data["turn"])

        ab_time_per_state = "N/A"
        if alpha_beta_state_count != 0:
            ab_time_per_state = ab_time / alpha_beta_state_count

        min_max_time_per_state = "N/A"
        if state_count != 0:
            min_max_time_per_state = min_max_time / state_count

        print("alpha-beta", alpha_beta_state_count, ab_time, ab_time_per_state, alpha_beta_results)
        print("min-max   ", state_count, min_max_time, min_max_time_per_state, min_max_results)

        assert alpha_beta_results == min_max_results
        assert alpha_beta_state_count <= state_count

