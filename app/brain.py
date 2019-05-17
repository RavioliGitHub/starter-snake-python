import random
import json
import time
from operator import itemgetter
import itertools
import game_engine


"""
BEHAVIOR I WANT TO ENFORCE

1.) Dont do moves that kill me immediately

2.) Avoid potential deadly head on head collisions

3.) Avoid going in tight spaces

4.) Avoid starvation

5.) Kill if possible

"""
directions = ['up', 'down', 'left', 'right']


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


def get_deadly_locations(data):
    board = data['board']
    snakes = board['snakes']

    deadly_locations = []
    for snake in snakes:
        for e in snake['body'][:-1]:
            deadly_locations.append((e['x'], e['y']))

    return deadly_locations


def get_moves_without_direct_death(data):
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


def get_best_move_based_on_current_data(data):
    directions_without_direct_death = get_moves_without_direct_death(data)

    if not directions_without_direct_death:
        return 'up'
    if len(directions_without_direct_death) == 1:

        return directions_without_direct_death[0]
    directions_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death)
    directions_with_most_space = get_least_constraining_moves(data, directions_without_direct_death)
    directions_with_food = get_moves_that_directly_lead_to_food(data)
    directions_that_lead_to_center = get_directions_that_lead_towards_the_center(data)
    directions_that_might_lead_to_head_on_head_lockdown = \
        directions_that_lead_to_potential_50_50_head_on_head_collision(data)

    move_score_list = []
    points = [0, 0, 0, 0]
    for d, score in zip(directions, points):
        if directions_without_direct_death.__contains__(d):
            score += 100000
        if directions_with_most_space.__contains__(d):
            score += 10000
        if directions_without_potential_deadly_head_on_head_collision.__contains__(d):
            score += 1000
        if not directions_that_might_lead_to_head_on_head_lockdown.__contains__(d):
            score += 100
        if directions_that_lead_to_center.__contains__(d):
            score += 10
        if directions_with_food.__contains__(d):
            score += 1
        move_score_list.append((d, score))
    #print()
    #print(directions_with_most_space)
    #print directions_that_lead_to_center
    move_score_list.sort(key=itemgetter(1), reverse=True)
    #print(move_score_list)
    #for snake in data['board']['snakes']:
       #print(data['you']['name'], snake['name'], get_distance_between_two_points(data['you']['body'][0], snake['body'][0]))
    #print(data['you']['name'], "problesm", directions_that_lead_to_potential_50_50_head_on_head_collision(data))
    # use randomness to avoid being stuck in a loop
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])
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


def get_directions_that_lead_towards_the_center(data):
    directions_that_lead_to_center = []
    you_head = data['you']['body'][0]
    current_distance_to_center = get_distance_to_center(data, you_head)
    for d in directions:
        next_tile = next_field_dic(d, you_head)
        if get_distance_to_center(data, next_tile) < current_distance_to_center:
            directions_that_lead_to_center.append(d)
    return directions_that_lead_to_center


def directions_that_lead_to_potential_50_50_head_on_head_collision(data):
    directions_that_lead_to_potential_collision = []
    you_head = data['you']['body'][0]
    for snake in data['board']['snakes']:
        if round(get_distance_between_two_points(you_head, snake['body'][0]), 2) == 3.16 or \
            round(get_distance_between_two_points(you_head, snake['body'][0]), 2) == 2.83:
            for my_d in directions:
                if my_d not in directions_that_lead_to_potential_collision:
                    for his_d in directions:
                        my_next_tile = next_field_dic(my_d, you_head)
                        his_next_tile = next_field_dic(his_d, snake['body'][0])
                        new_distance = get_distance_between_two_points(my_next_tile, his_next_tile)
                        if round(new_distance, 2) == 1.41:
                            directions_that_lead_to_potential_collision.append(my_d)
    return directions_that_lead_to_potential_collision


def get_best_move_min_max(data, depth):
    if not get_moves_without_direct_death(data):
        return 'up'

    move_score_list = []
    for move in get_moves_without_direct_death(data):
        move_score_list.append((move, min_value(data, depth, move)))

    move_score_list.sort(key=itemgetter(1), reverse=True)
    # use randomness to avoid being stuck in a loop
    # print(move_score_list)
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])
    # print(equivalent_best_moves)
    return random.choice(equivalent_best_moves)


def create_map_with_duration(data):
    pass


def probably_too_tight():
    pass



"""
def evaluate_position(data):
    directions_without_direct_death = get_moves_without_direct_death(data)
    if not directions_without_direct_death:
        return 0
    directions_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death)
    directions_with_most_space = get_least_constraining_moves(data, directions_without_direct_death)
    directions_with_food = get_moves_that_directly_lead_to_food(data)

    score = 0
    for d in directions:
        if directions_without_direct_death.__contains__(d):
            score += 1000
        if directions_with_most_space.__contains__(d):
            score += 100
        if directions_without_potential_deadly_head_on_head_collision.__contains__(d):
            score += 10
        if directions_with_food.__contains__(d):
            score += 1

    return score
"""


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


def evaluate_position(data):
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
