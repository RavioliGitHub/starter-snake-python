import Queue
from Painter import Window
import thread
import game_engine
import brain
import main
import random
import time
import json
import situation_creator


def replay_logs(file):
    logs = open(file, "r")
    states = logs.read()
    logs.close()
    state_list = states.split("\n")
    first_state = json.loads(state_list[0].replace("'", '"'))
    state_queue = Queue.Queue()
    thread.start_new_thread(Window, (first_state, state_queue))

    for state in state_list:
        if state:
            state_queue.put(json.loads(state.replace("'", '"')))

    state_queue.put("GAME DONE")
    state_queue.put("REMOVE THIS FLAG WHEN DONE DRAWING")
    while not state_queue.empty():
        
        time.sleep(0.2)


def replay_logs_using_engine(file):
    logs = open(file, "r")
    states = logs.read()
    logs.close()
    state_list = states.split("\n")

    first_state = json.loads(state_list[0].replace("'", '"'))
    state_queue_logs = Queue.Queue()
    state_queue_engine = Queue.Queue()
    thread.start_new_thread(Window, (first_state, state_queue_logs))
    print("1")
    thread.start_new_thread(Window, (first_state, state_queue_engine))
    print("2")

    # TURN 0
    print("3")
    state_queue_engine.put(first_state)
    print("4")
    state_queue_logs.put(first_state)
    print("5")

    # TURN 1 - END
    for turn in range(len(state_list)-1):
        current_state = json.loads(state_list[turn].replace("'", '"'))
        next_state_logs = json.loads(state_list[turn+1].replace("'", '"'))
        moves = game_engine.get_played_moves(current_state, next_state_logs)
        next_state_by_engine = game_engine.update(current_state, moves)

        state_queue_engine.put(next_state_by_engine)
        state_queue_logs.put(next_state_logs)

    state_queue_logs.put("GAME DONE")
    state_queue_engine.put("GAME DONE")
    state_queue_logs.put("REMOVE THIS FLAG WHEN DONE DRAWING")
    state_queue_engine.put("REMOVE THIS FLAG WHEN DONE DRAWING")
    while not state_queue_engine.empty() and not state_queue_logs.empty():
        print("waiting")
        time.sleep(0.2)


def run_game_without_window(number_of_snakes):
    print("start" , number_of_snakes)
    FOOD_SPAWN_CHANCE = 20
    data = game_engine.create_game(number_of_snakes)
    if number_of_snakes == 1:
        end_conditions = 0
    else:
        end_conditions = 1

    while len(data['board']['snakes']) > end_conditions:
        moves = []
        for snake in data['board']['snakes']:
            data['you'] = snake
            moves.append(main.get_move_response_string(data))
        data = game_engine.update(data, moves)
        if random.randint(0, 100) < FOOD_SPAWN_CHANCE:
            game_engine.add_food(data)
    print("Done")


def run_game_from_drawing():
    state_queue = Queue.Queue()
    situation_creator.Window(state_queue)
    while state_queue.empty():
        time.sleep(0.5)
    data = state_queue.get()
    FOOD_SPAWN_CHANCE = 20
    number_of_snakes = len(data['board']['snakes'])
    thread.start_new_thread(Window, (data, state_queue))
    if number_of_snakes == 1:
        end_conditions = 0
    else:
        end_conditions = 1

    while len(data['board']['snakes']) > end_conditions:
        print(data['turn'])
        state_queue.put(data)
        moves = []
        for snake in data['board']['snakes']:
            data['you'] = snake
            start = time.time()
            moves.append(main.get_move_response_string(data))
            #print(round(time.time()-start, 2))
        data = game_engine.update(data, moves)
        if random.randint(0, 100) < FOOD_SPAWN_CHANCE:
            game_engine.add_food(data)
    state_queue.put(data)

    state_queue.put("GAME DONE")
    state_queue.put("REMOVE THIS FLAG WHEN DONE DRAWING")
    while not state_queue.empty():
        time.sleep(0.5)


def run_game(number_of_snakes, *args):
    state_queue = Queue.Queue()
    FOOD_SPAWN_CHANCE = 20
    data = game_engine.create_game(number_of_snakes)
    if args:
        data = args[0]
        number_of_snakes = len(data['board']['snakes'])
    thread.start_new_thread(Window, (data, state_queue))
    if number_of_snakes == 1:
        end_conditions = 0
    else:
        end_conditions = 1

    while len(data['board']['snakes']) > end_conditions:
        print(data['turn'])
        state_queue.put(data)
        moves = []
        for snake in data['board']['snakes']:
            data['you'] = snake
            start = time.time()
            moves.append(main.get_move_response_string(data))
            # brain.min_max_search_for_moves_without_unavoidable_head_collision(data)
            # print(round(time.time()-start, 2))
        data = game_engine.update(data, moves)
        if random.randint(0, 100) < FOOD_SPAWN_CHANCE:
            game_engine.add_food(data)
    state_queue.put(data)

    state_queue.put("GAME DONE")
    state_queue.put("REMOVE THIS FLAG WHEN DONE DRAWING")
    while not state_queue.empty():
        time.sleep(0.5)


#run_game_from_drawing()
# run_game_without_window(2)
#replay_logs("PainterTestFile.txt")
#run_game(4)
#replay_logs_using_engine("PainterTestFile.txt")