import json
import os
import random
import bottle
import brain
import time
import sys
from api import ping_response, start_response, move_response, end_response
import game_engine


previous_data = "f"
@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    global previous_data
    data = bottle.request.json
    previous_data = data

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print(json.dumps(data))

    color = "#00FF00"

    return start_response(color)


@bottle.post('/move')
def move():
    data = bottle.request.json
    my_move_response = get_move_response_string(data)
    return move_response(my_move_response)

state_list = []
def get_move_response_string(data):
    global previous_data
    start_time = time.time()
    #game_engine.save_to_logs(data)
    #print('turn:', data['turn'])

    #print(data['turn'] > 0 and previous_data is not "f" and len(data['board']['snakes'][0]['body']) > 1 and
         # previous_data['game']['id'] == data['game']['id'])
    #print(data['turn'] > 0, previous_data is not "f", len(data['board']['snakes'][0]['body']) > 1,
          #previous_data is not "f" and previous_data['game']['id'] == data['game']['id'])
    """
    if data['turn'] > 0 and previous_data is not "f" and len(data['board']['snakes'][0]['body']) > 1 and \
            previous_data['game']['id'] == data['game']['id']:
        print('check_prediction')
        played_moves = game_engine.get_played_moves(previous_data, data)
        previous_data_prediction = game_engine.update(previous_data, played_moves)
        game_engine.check_if_update_was_accurate(previous_data_prediction, data)
    """
    previous_data = data
    #print(brain.evaluate_position(data))
    #print(brain.max_value(data, 2))
    if data['you']['name'] == "1":
        #game_engine.save_to_logs(data, "test1.txt")
        pass

    my_move_response = brain.get_best_move(data)

    #print(time.time() - start_time)
    return my_move_response


@bottle.post('/end')
def end():
    global previous_data
    previous_data = "f"
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) == 2:
        port += int(sys.argv[1])
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', str(port)),
        debug=os.getenv('DEBUG', True)
    )

