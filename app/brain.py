import random
import json


def nextField(direction, currentPosition):
    if direction is 'up':
        return currentPosition['x'], currentPosition['y'] - 1
    elif direction is 'down':
        return currentPosition['x'], currentPosition['y'] + 1
    elif direction is 'left':
        return currentPosition['x'] - 1, currentPosition['y']
    elif direction is 'right':
        return currentPosition['x'] + 1, currentPosition['y']

def main(data):
    print("MAIN")
    #data = json.loads('{"game": {"id": "3553defc-bfab-4dc2-8ccf-fcb8a150b90b"}, "turn": 0, "board": {"height": 15, "width": 15, "food": [{"x": 14, "y": 1}, {"x": 5, "y": 4}, {"x": 9, "y": 4}, {"x": 12, "y": 2}, {"x": 14, "y": 13}, {"x": 9, "y": 8}, {"x": 6, "y": 12}, {"x": 13, "y": 13}, {"x": 0, "y": 0}, {"x": 12, "y": 3}], "snakes": [{"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}]}, "you": {"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}}')
    game = data['game']
    game_id = game['id']
    turn = data['turn']
    board = data['board']
    height = board['height']
    width = board['width']
    food = board['food']
    snakes = board['snakes']
    you = data['you']
    you_head = you['body'][0]

    food_locations = []
    for e in food:
        food_locations.append((e['x'], e['y']))

    deadly_locations = []
    for snake in snakes:
        for e in snake['body']:
            deadly_locations.append((e['x'], e['y']))

    enemy_heads = []
    for snake in snakes:
        enemy_heads.append(snake['body'][0])
    enemy_heads.remove(you_head)

    directions = ['up', 'down', 'left', 'right']
    possible_head_on_head_collision = []
    for head in enemy_heads:
        for d in directions:
            possible_head_on_head_collision.append(nextField(d, head))

    elements = [game, game_id, turn, board, height, width, food, you_head, food_locations, deadly_locations]

    directions_without_direct_death = ['up', 'down', 'left', 'right']

    if you_head['x'] == 0:
        directions_without_direct_death.remove('left')
    if you_head['x'] == width-1:
        directions_without_direct_death.remove('right')
    if you_head['y'] == 0:
        directions_without_direct_death.remove('up')
    if you_head['y'] == height-1:
        directions_without_direct_death.remove('down')

    for d in directions:
        nextTile = nextField(d, you_head)
        if deadly_locations.__contains__(nextTile):
            directions_without_direct_death.remove(d)

    directions_without_head_on_head_collision = []
    for d in directions_without_direct_death:
        nextTile = nextField(d, you_head)
        if not possible_head_on_head_collision.__contains__(nextTile):
            directions_without_head_on_head_collision.append(d)

    if directions_without_head_on_head_collision:
        for d in directions_without_head_on_head_collision:
            nextTile = nextField(d, you_head)
            if food_locations.__contains__(nextTile):
                return d
        return random.choice(directions_without_head_on_head_collision)

    direction = random.choice(directions_without_direct_death)

    return direction


