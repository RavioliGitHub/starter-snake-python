import os
import Game_object_pool
import cherrypy
import json
import time
import brain2

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

# TODO turn back to true before commit
main_print = True

def remove_shouts(data):
    for snake in data['board']['snakes']:
        snake.pop('shout', None)
    data['you'].pop('shout', None)


class Battlesnake(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        return {
            "apiversion": "1",
            "author": "",  # TODO: Your Battlesnake Username
            "color": "#888888",  # TODO: Personalize
            "head": "default",  # TODO: Personalize
            "tail": "default",  # TODO: Personalize
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        # TODO: Use this function to decide how your snake is going to look on the board.


        global previous_data
        data = cherrypy.request.json
        remove_shouts(data)
        previous_data = data
        Game_object_pool.GamePool().init_pool(data)

        print("starting")
        print(json.dumps(data))

        print("START")
        return "ok"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):
        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        # TODO: Use the information in cherrypy.request.json to decide your next move.
        if main_print:
            print("Received move request, unpacking data")
            data = cherrypy.request.json
        remove_shouts(data)
        if main_print:
            print("Received move request ", data['turn'])
        my_move_response = self.get_move_response_string(data)
        return {"move": my_move_response}

    state_list = []
    def get_move_response_string(self, data):
        start_time = time.time()

        response2 = brain2.get_best_move_based_on_current_data(data)

        if type(response2) == str:
            response2 = (response2, [])

        my_move_response2, move_score_list2 = response2

        if main_print:
            print("response time", time.time() - start_time, "name", data['you']['name'])
            print("Responded to move request ", data['turn'], " with ", my_move_response2, move_score_list2)
        return my_move_response2

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json

        print("END")
        print(json.dumps(data))
        return "ok"


if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update(
        {"server.socket_port": int(os.environ.get("PORT", "8080")),}
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)