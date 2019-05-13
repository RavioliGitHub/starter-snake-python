import copy
import random
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
directions = ['up', 'down', 'left', 'right']
def next_field(direction, currentPosition):
    if direction is 'up':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] - 1}
    elif direction is 'down':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] + 1}
    elif direction is 'left':
        return {'x': currentPosition['x'] - 1, 'y': currentPosition['y']}
    elif direction is 'right':
        return {'x': currentPosition['x'] + 1, 'y': currentPosition['y']}



def compare_elements(pre, act):
    if type(pre) is dict:
        for key in pre:
            compare_elements(pre[key], act[key])
    elif type(pre) is list:
        for pre_el, act_el in zip(pre, act):
            compare_elements(pre_el, act_el)
    else:

        if pre != act:
            print("diff", pre, act)

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

    boadWithGrid = []
    for x in range(width+2):
        boadWithGrid.append([])
        for y in range(height+2):
            if x == 0 or x == width+1 or y == 0 or y == height+1:
                boadWithGrid[x].append('#')
            else:
                boadWithGrid[x].append(board_data[x-1][y-1])

    print('\n')
    prettyString = ('\n'.join([''.join(['{:1}'.format(item) for item in row])
                     for row in boadWithGrid]))
    return prettyString

def parallel_print_boards(board_list):
    print_list = []
    for board_string in board_list:
        print_list.append([])
        for line in board_string.split('\n'):
            print_list[-1].append(line)

    for i in range(len(print_list[0])):
        s = ''
        for solo_list in print_list:
            s += solo_list[i]
            s += '   '
        print(s)

def get_differences(original, copy):
    result = ''
    for ori, cop in zip(original, copy):
        if ori is cop:
            result += ori
        else:
            result += 'X'
    return result

def print_compare(data1, data2):
    board1 = printBoard(data1)
    board2 = printBoard(data2)
    diff = get_differences(board1, board2)
    parallel_print_boards([board1, diff, board2])

def print_one_line_diff(name, pred, act):
    print(name, 'doesnt match:', 'Prediction = ', pred, ' || Actual = ', act)

def pretty_print_diff(prediction, actual):
    if not prediction['game']['id'] == actual['game']['id']:
        print_one_line_diff('Game ID', prediction['game']['id'], actual['game']['id'])
    if not prediction['turn'] == actual['turn']:
        print_one_line_diff('Turn ', prediction['turn'], actual['turn'])
    if not prediction['board']['height'] == actual['board']['height']:
        print_one_line_diff('height', prediction['board']['height'], actual['board']['height'])
    if not prediction['board']['width'] == actual['board']['width']:
        print_one_line_diff('width', prediction['board']['width'], actual['board']['width'])
    if not prediction['board']['snakes'] == actual['board']['snakes']:
        print('ERROR IN SNAKES')
    for pre_snake in prediction['board']['snakes']:
        found = False
        for act_snake in actual['board']['snakes']:
            if pre_snake['id'] == act_snake['id']:
                compare_snakes_inline(pre_snake, act_snake)
                found = True
        if not found:
            print('Snake was not deleted ', pre_snake['name'])
    for act_snake in actual['board']['snakes']:
        found = False
        for pre_snake in prediction['board']['snakes']:
            if pre_snake['id'] == act_snake['id']:
                found = True
        if not found:
            print('Snake was deleted by error', act_snake['name'])


def compare_snakes_inline(pre_snake, act_snake):
    # name id health body
    if not pre_snake['name'] == act_snake['name']:
        print_one_line_diff('Snake name', pre_snake['name'], act_snake['name'])
    if not pre_snake['id'] == act_snake['id']:
        print_one_line_diff('Snake ID', pre_snake['id'], act_snake['id'])
    if not pre_snake['health'] == act_snake['health']:
        print_one_line_diff('Snake Health', pre_snake['health'], act_snake['health'])
    if not pre_snake['body'] == act_snake['body']:
        print_one_line_diff('Snake body', pre_snake['body'], act_snake['body'])


def check_if_update_was_accurate(prediction, actual_data):
    prediction_copy = copy.deepcopy(prediction)
    actual_data_copy = copy.deepcopy(actual_data)
    del prediction_copy['board']['food']
    del actual_data_copy['board']['food']
    assert len(prediction_copy) == len(actual_data_copy), "not same length"
    #compare_elements(prediction_copy, actual_data_copy)

    if not prediction_copy == actual_data_copy:
        pretty_print_diff(prediction_copy, actual_data_copy)
        """
        print_compare(prediction, actual_data)
        print('prediction \n', prediction_copy)
        print('actual \n', actual_data_copy)
        a = prediction_copy
        b = actual_data_copy
        result = [(k, a[k], b[k]) for k in a if k in b and a[k] != b[k]]
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(result)
        """
        assert prediction_copy == actual_data_copy



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

def get_played_moves(previous_data, current_data):
    assert type(previous_data) is dict, previous_data
    assert type(current_data) is dict, current_data
    assert type(previous_data['board']['snakes']) is list, previous_data['board']['snakes']
    moves = []
    current_snakes = current_data['board']['snakes']
    for pre_snake in previous_data['board']['snakes']:
        lenght = len(moves)
        for cur_snake in current_snakes:
            if pre_snake['id'] == cur_snake['id']:
                for d in directions:
                    next_tile = next_field(d, cur_snake['body'][1])
                    if cur_snake['body'][0] == next_tile:
                        moves.append(d)
        # snake died
        if lenght == len(moves):
            for d in directions:
                next_tile = next_field(d, pre_snake['body'][0])
                if pre_snake['body'][1] == next_tile:
                    moves.append(d)

    return moves



def update(original_data, moves):

    #original_data = json.loads('{"game": {"id": "3553defc-bfab-4dc2-8ccf-fcb8a150b90b"}, "turn": 0, "board": {"height": 15, "width": 15, "food": [{"x": 14, "y": 1}, {"x": 5, "y": 4}, {"x": 9, "y": 4}, {"x": 12, "y": 2}, {"x": 14, "y": 13}, {"x": 9, "y": 8}, {"x": 6, "y": 12}, {"x": 13, "y": 13}, {"x": 0, "y": 0}, {"x": 12, "y": 3}], "snakes": [{"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}]}, "you": {"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}}')
    updated_data = copy.deepcopy(original_data)
    game = updated_data['game']
    game_id = game['id']
    updated_data['turn'] = updated_data['turn']+1
    board = updated_data['board']
    height = board['height']
    width = board['width']
    food_locations = board['food']
    snakes = board['snakes']
    you = updated_data['you']
    you_head = you['body'][0]

    # Move head by adding a new body part at the start of the body array in the move direction
    for move, snake in zip(moves, snakes):
        destination = next_field(move, snake['body'][0])
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
        for body_part in snake['body'][1:]:
            deadly_locations.append(body_part)
        # everything except head, which is handly seperately, not always deadly

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

def save_to_logs(data, file):
    log_read = open("app\\" + file, "r")
    content = log_read.read()
    log_read.close()

    log_write = open("app\\" + file, "w")
    message = str(data)

    text = content + '\n' + message
    log_write.write(text)
    log_write.close()


def create_game(number_of_snakes):
    HEIGHT = 11
    WIDTH = 11
    FOOD_AT_START = 5
    SNAKE_START_LENGTH = 3
    START_POSITIONS = [(1,1), (WIDTH-2, HEIGHT-2), (1, HEIGHT-2), (WIDTH-2, 1),
                       (round(WIDTH/2), 1), (WIDTH-2, round(HEIGHT/2)), (round(WIDTH/2), HEIGHT-2), (1, round(HEIGHT/2))]

    data = {}
    data['game'] = {}
    data['game']['id'] = "ID_FILLER"
    data['turn'] = 0
    data['board'] = {}
    data['board']['height'] = HEIGHT
    data['board']['width'] = WIDTH
    data['board']['snakes'] = []
    for i in range(number_of_snakes):
        snake = {}
        snake['id'] = str(i)
        snake['name'] = str(i)
        snake['health'] = 100
        snake['body'] = []
        for j in range(SNAKE_START_LENGTH):
            snake['body'].append({'x': START_POSITIONS[i][0], 'y': START_POSITIONS[i][1]})
        data['board']['snakes'].append(snake)

    data['board']['food'] = []
    empty_tiles = []
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if (x, y) not in START_POSITIONS:
                empty_tiles.append({'x': x, 'y': y})

    for tile in random.sample(empty_tiles, FOOD_AT_START):
        data['board']['food'].append(tile)
    data['you'] = data['board']['snakes'][0]
    return data


def add_food(data):
    empty_tiles = []
    for x in range(data['board']['width']):
        for y in range(data['board']['height']):
            empty_tiles.append({'x': x, 'y': y})
    for location in data['board']['food']:
        empty_tiles.remove(location)
    for snake in data['board']['snakes']:
        for location in snake['body']:
            if location in empty_tiles:
                empty_tiles.remove(location)
    data['board']['food'].append(random.choice(empty_tiles))


