import json
import os
import bottle
import brain2
import time
import sys
import Game_object_pool
from api import ping_response, start_response, move_response, end_response, get_response

# TODO turn back to true before commit
main_print = True

def remove_shouts(data):
    for snake in data['board']['snakes']:
        snake.pop('shout', None)
    data['you'].pop('shout', None)

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

@bottle.get('/')
def get():
    print("starting get response")
    return get_response()


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
    remove_shouts(data)
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
    if main_print:
        print("Received move request, unpacking data")
    data = bottle.request.json
    remove_shouts(data)
    if main_print:
        print("Received move request ", data['turn'])
    my_move_response = get_move_response_string(data)
    return move_response(my_move_response)


state_list = []
def get_move_response_string(data):
    start_time = time.time()

    response2 = brain2.get_best_move_based_on_current_data(data)

    if type(response2) == str:
        response2 = (response2, [])

    my_move_response2, move_score_list2 = response2

    if main_print:
        print("response time", time.time()-start_time, "name", data['you']['name'])
        print("Responded to move request ", data['turn'], " with ", my_move_response2, move_score_list2)
    return my_move_response2


@bottle.post('/end')
def end():
    data = bottle.request.json
    remove_shouts(data)

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
