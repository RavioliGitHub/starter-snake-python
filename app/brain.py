import random
import json
import time
from operator import itemgetter
import itertools
import game_engine

directions = ['up', 'down', 'left', 'right']


def next_field(direction, current_position):
    if direction is 'up':
        return current_position['x'], current_position['y'] - 1
    elif direction is 'down':
        return current_position['x'], current_position['y'] + 1
    elif direction is 'left':
        return current_position['x'] - 1, current_position['y']
    elif direction is 'right':
        return current_position['x'] + 1, current_position['y']


def next_field_with_tupel(direction, current_position):
    if direction is 'up':
        return current_position[0], current_position[1] - 1
    elif direction is 'down':
        return current_position[0], current_position[1] + 1
    elif direction is 'left':
        return current_position[0] - 1, current_position[1]
    elif direction is 'right':
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


def get_best_move(data):
    directions_without_direct_death = get_moves_without_direct_death(data)

    if not directions_without_direct_death:
        return 'up'
    if len(directions_without_direct_death) == 1:

        return directions_without_direct_death[0]
    directions_without_potential_deadly_head_on_head_collision = \
        get_moves_without_potential_deadly_head_on_head_collision(data, directions_without_direct_death)
    directions_with_most_space = get_least_constraining_moves(data, directions_without_direct_death)
    directions_with_food = get_moves_that_directly_lead_to_food(data)

    move_score_list = []
    points = [0, 0, 0, 0]
    for d, score in zip(directions, points):
        if directions_without_direct_death.__contains__(d):
            score += 1000
        if directions_with_most_space.__contains__(d):
            score += 100
        if directions_without_potential_deadly_head_on_head_collision.__contains__(d):
            score += 10
        if directions_with_food.__contains__(d):
            score += 1
        move_score_list.append((d, score))

    move_score_list.sort(key=itemgetter(1), reverse=True)
    # use randomness to avoid being stuff in a loop
    equivalent_best_moves = []
    for move in move_score_list:
        if move[1] == move_score_list[0][1]:
            equivalent_best_moves.append(move[0])
    return random.choice(equivalent_best_moves)


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
    
    print('min', depth, child_scores)
    return min(child_scores)


def max_value(position, depth):
    if depth == 0:
        return evaluate_position(position)
    if not position['board']['snakes']:
        return 10
    if im_dead(position) or not get_moves_without_direct_death(position):
        return 0
    if len(position['board']['snakes']) == 1:
        return 1000000
    else:
        child_scores = []
        for move in get_moves_without_direct_death(position):
            child_scores.append(min_value(position, depth, move))

    print('max', depth, get_moves_without_direct_death(position), child_scores)
    return max(child_scores)
