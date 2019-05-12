import Queue
from Painter import Window
import thread
import game_engine
import brain
import main
import random
import time


def run_game(number_of_snakes):
    state_queue = Queue.Queue()
    FOOD_SPAWN_CHANCE = 20
    data = game_engine.create_game(number_of_snakes)
    thread.start_new_thread(Window, (data, state_queue))
    if number_of_snakes == 1:
        end_conditions = 0
    else:
        end_conditions = 1

    while len(data['board']['snakes']) != end_conditions:
        state_queue.put(data)
        moves = []
        for snake in data['board']['snakes']:
            data['you'] = snake
            moves.append(main.get_move_response_string(data))
        data = game_engine.update(data, moves)
        if random.randint(0, 100) < FOOD_SPAWN_CHANCE:
            game_engine.add_food(data)

    state_queue.put("GAME DONE")
    while not state_queue.empty():
        time.sleep(0.5)
