import copy
import json
import pprint
"""
After all the snakes have returned their move decision the engine will, for each snake,

    Move head by adding a new body part at the start of the body array in the move direction
    Reduce health
    Check if the snake ate and adjust health
    Remove the final body segment
    If the snake ate this turn, add a new body segment, underneath the current tail, this will cause the snake to grow on the following turn.
    Check for snake death (see Snake Deaths)
    Check if food needs to be spawned. (see Food Spawn Rules)

"""

def check_if_update_was_accurate(prediction, actual_data):
    prediction_copy = copy.deepcopy(prediction)
    actual_data_copy = copy.deepcopy(actual_data)
    del prediction_copy['board']['food']
    del actual_data_copy['board']['food']
    assert len(prediction_copy) == len(actual_data_copy), "not same length"
    for pred, act in zip(prediction_copy, actual_data_copy):
        if pred != act:
            print(pred, act, prediction_copy[pred], actual_data_copy[act])

    a = prediction_copy
    b = actual_data_copy
    result = [(k, a[k], b[k]) for k in a if k in b and a[k] != b[k]]
    pp = pprint.PrettyPrinter(indent=4)
    # print("result")
    pp.pprint(result)
    assert prediction_copy == actual_data_copy

def printBoard(data):
    turn = data['turn']
    board = data['board']
    height = board['height']
    width = board['width']
    food_locations = board['food']
    snakes = board['snakes']
    board_data = []

    for x in range(width):
        board_data.append([])
        for y in range(height):
            board_data[x].append(' ')

    for food in food_locations:
        board_data[food['x']][food['y']] = 'F'

    for i, snake in zip(range(len(snakes)), snakes):
        for body_part in snake['body']:
            board_data[body_part['x']][body_part['y']] = i

    print('\n')
    print("TURN", turn)
    print('\n'.join([''.join(['{:4}'.format(item) for item in row])
                     for row in board_data]))
    print('\n')


directions = ['up', 'down', 'left', 'right']
def nextField(direction, currentPosition):
    if direction is 'up':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] - 1}
    elif direction is 'down':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] + 1}
    elif direction is 'left':
        return {'x': currentPosition['x'] - 1, 'y': currentPosition['y']}
    elif direction is 'right':
        return {'x': currentPosition['x'] + 1, 'y': currentPosition['y']}

def nextFieldWithTupel(direction, currentPosition):
    if direction is 'up':
        return currentPosition[0], currentPosition[1] - 1
    elif direction is 'down':
        return currentPosition[0], currentPosition[1] + 1
    elif direction is 'left':
        return currentPosition[0] - 1, currentPosition[1]
    elif direction is 'right':
        return currentPosition[0] + 1, currentPosition[1]

def not_deadly_location_on_board(goal, deadly_locations, width, height):
    if goal['x'] < 0 or goal['x'] >= width or goal['y'] < 0 or goal['y'] >= height:
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
            curNeighbour = nextFieldWithTupel(d, cur)
            if not visited.__contains__(curNeighbour) and not queue.__contains__(curNeighbour):
                if not_deadly_location_on_board(curNeighbour, deadly_locations, width, height):
                    queue.append(curNeighbour)

    return visited

def update(original_data, moves):

    #original_data = json.loads('{"game": {"id": "3553defc-bfab-4dc2-8ccf-fcb8a150b90b"}, "turn": 0, "board": {"height": 15, "width": 15, "food": [{"x": 14, "y": 1}, {"x": 5, "y": 4}, {"x": 9, "y": 4}, {"x": 12, "y": 2}, {"x": 14, "y": 13}, {"x": 9, "y": 8}, {"x": 6, "y": 12}, {"x": 13, "y": 13}, {"x": 0, "y": 0}, {"x": 12, "y": 3}], "snakes": [{"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}]}, "you": {"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}}')
    updated_data = copy.deepcopy(original_data)
    game = updated_data['game']
    game_id = game['id']
    updated_data['turn'] = updated_data['turn']+1
    board = updated_data['board']
    height = board['height']
    width = board['width']
    food_locations: list = board['food']
    snakes: list = board['snakes']
    you = updated_data['you']
    you_head = you['body'][0]

    # Move head by adding a new body part at the start of the body array in the move direction
    for move, snake in zip(moves, snakes):
        destination = nextField(move, snake['body'][0])
        snake['body'].insert(0, destination)

    # Reduce health
    for snake in snakes:
        snake['health'] = snake['health']-1

    # Check if the snake ate and adjust health
    for snake in snakes:
        head = snake['body'][0]
        if food_locations.__contains__(head):
            snake['health'] = 100
            food_locations.remove(head)

    # Remove the final body segment
    for snake in snakes:
        del snake['body'][-1]

    # If the snake ate this turn, add a new body segment, underneath the current tail,
    # this will cause the snake to grow on the following turn.
    for snake in snakes:
        if snake['health'] == 100:
            snake['body'].append(copy.deepcopy(snake['body'][-1]))

    # Check for snake death (see Snake Deaths)
    snakes_that_die = []
    deadly_locations = []
    for snake in snakes:
        deadly_locations.append(snake['body'][1:]) # everything except head

    heads = []
    for snake in snakes:
        heads.append(snake['body'][0])

    for snake in snakes:
        # Wall or snake body collision
        if not not_deadly_location_on_board(snake['body'][0], deadly_locations, width, height):
            snakes_that_die.append(snake)
            continue

        if snake['health'] == 0:
            snakes_that_die.append(snake)
            continue

        for other_snake in snakes:
            if other_snake is not snake:
                if other_snake['body'][0] is snake['body'][0]:
                    if not len(snake['body']) > len(other_snake['body']):
                        snakes_that_die.append(snake)
                        continue
                    
    for dead_snake in snakes_that_die:
        snakes.remove(dead_snake)
    # Check if food needs to be spawned. (see Food Spawn Rules)

    for snake in snakes:
        if snake['body'][1] == you['body'][0]:
            you['health'] = snake['health']
            you['body'] = snake['body']

    return updated_data

