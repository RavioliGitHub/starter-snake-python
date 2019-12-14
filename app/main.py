import json
import os
import random
import bottle
import brain
import brain2
import time
import sys
import Game_object_pool
from api import ping_response, start_response, move_response, end_response
import game_engine


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
    Game_object_pool.GamePool().init_pool(data)

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print("starting")
    print(json.dumps(data))

    color = "#00FF00"

    return start_response(color)


@bottle.post('/move')
def move():
    print("Received move request, unpacking data")
    data = bottle.request.json
    print("Received move request ", data['turn'])
    my_move_response = get_move_response_string(data)
    return move_response(my_move_response)


state_list = []
def get_move_response_string(data):
    start_time = time.time()

    timeFrame = 0.15
    #print("remeber to reset timeframe before commting")
    #TODO RESET TIMEFRAME
    timeLimit = time.time() + timeFrame
    response2 = brain2.get_best_move_based_on_current_data(data, timeLimit)

    if type(response2) == str:
        response2 = (response2, [])

    my_move_response2, move_score_list2 = response2

    print("response time", time.time()-start_time)
    print("Responded to move request ", data['turn'], " with ", my_move_response2, move_score_list2)
    return my_move_response2


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print("end")
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

