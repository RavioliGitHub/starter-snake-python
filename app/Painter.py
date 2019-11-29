from Tkinter import Tk, Label, Button, Canvas, Frame, Text
import Tkinter as tk
import game_engine
import time
import brain
import math
from printer import Logger
#import pyperclip
import main
import pprint
from printer import Logger


def log(turn, snake, message):
    Logger().log(turn, snake, message)


def log(data, message):
    Logger().log(data['turn'], data['you'], message)

block_size = 20


print_duration = False
print_reachTime = True
print_headDanger = False
print_escape_points = False
print_future_duration = False
print_future_escape_points = False


class Window(Tk):
    def __init__(self, data, state_queue, pause=False):
        Tk.__init__(self, className="MySnakeWindow")
        self.height = data['board']['height']
        self.width = data['board']['width']
        self.state_queue = state_queue
        self.state_list = []
        self.turn = 0
        self.pause = pause
        self.FPS = 60
        self.snake_color_by_id = self.create_snake_color_by_id(data)
        self.canvas = Canvas(master=self, width=self.width * block_size * 2 + 700, height=self.height * block_size)
        self.canvas.grid(row=0, column=0)
        self.textFrame = Frame(master=self, bg='orange', height=100)
        self.textFrame.grid()
        self.textWidgets = {}
        self.prepareLogLabels(data)

        self.pause_replay, self.fps_button = self.create_buttons()
        self.Frame = Frame(self)
        time.sleep(1)
        self.after(10, self.update_state_list)
        self.after(1000/self.FPS, self.draw_next_state)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()


    def prepareLogLabels(self, data):
        totalLineSpace = 30
        labelHeight = int(math.floor(totalLineSpace/len(data['board']['snakes'])))

        i = 0
        j = 0
        for snake in data['board']['snakes']:
            # titles
            Label(master=self.textFrame, text=snake['name']).grid(row=i, column=j)

            #Actual labels
            textLabel = Text(master=self.textFrame, height=labelHeight, width=60)
            self.textWidgets[snake['id']] = textLabel
            textLabel.grid(row=i, column=j+1)
            j += 2
            if j == 4:
                j = 0
                i += 1

    def calculate_moves(self, *args):
        data = self.state_list[self.turn]
        snakes = data['board']['snakes']
        for snake in snakes:
            data['you'] = snake
            response = main.get_move_response_string(data)
            log(data, response)
            print(snake['name'], response)
        self.update_text_lables(data)

    def calculate_this_state_by_engine(self, *args):
        if self.turn == 0:
            print("Not possible for turn 0")
            return
        cur_state = self.state_list[self.turn]
        prev_state = self.state_list[self.turn-1]
        moves = game_engine.get_played_moves(prev_state, cur_state)

        cur_state_by_engine = game_engine.update(prev_state, moves)
        self.draw_on_canvas(cur_state_by_engine)

    def show_coordinates(self, *args):
        for x in range(self.width):
            for y in range(self.height):
                self.canvas.create_text((x * block_size, y * block_size + 8), text=(x+1, y+1))

    def on_closing(self, *args):
        empty_state_queue(self.state_queue)
        self.destroy()

    def copy_current_data_to_clipboard(self, *args):
        #pyperclip.copy(str(self.state_list[self.turn]))
        pass

    def save_to_logs(self, *args):
        game_engine.save_list_to_logs(self.state_list, "PainterTestFile.txt")

    def create_snake_color_by_id(self, data):
        snake_colors = ['green', 'blue', 'yellow', 'gray', 'brown', 'purple', 'black', 'orange']
        snake_color_by_id = {}

        for snake, color in zip(data['board']['snakes'], snake_colors):
            snake_color_by_id[snake['id']] = color

        return snake_color_by_id

    def increase_fps(self, *args):
        self.FPS = self.FPS + 10
        self.fps_button["text"] = self.FPS

    def decrease_fps(self, *args):
        self.FPS = self.FPS - 10
        if self.FPS < 1:
            self.FPS = 1
        self.fps_button["text"] = self.FPS

    def pause_flip(self, *args):
        self.pause = not self.pause
        if self.pause:
            self.pause_replay["text"] = "Play"
        else:
            self.pause_replay["text"] = "Pause"

    def reload_game(self, *args):
        self.turn = 0
        self.draw_on_canvas(self.state_list[self.turn])

    def forward(self, *args):
        self.turn = self.turn + 1
        if self.turn >= len(self.state_list):
            self.turn = len(self.state_list)-1
        self.draw_on_canvas(self.state_list[self.turn])

    def backward(self, *args):
        self.turn = self.turn - 1
        if self.turn < 0:
            self.turn = 0
        self.draw_on_canvas(self.state_list[self.turn])

    def create_buttons(self):
        buttonFrame = Frame(master=self)
        buttonFrame.grid(row=0, column=1)

        self.bind("<Escape>", self.on_closing)
        pause = Button(master=buttonFrame, command=self.pause_flip, text="Pause")
        pause.grid()
        self.bind("<space>", self.pause_flip)
        fps_button = Button(master=buttonFrame, text=self.FPS)
        fps_button.bind('<Button-1>', self.increase_fps)
        self.bind("<Up>", self.increase_fps)
        fps_button.bind('<Button-3>', self.decrease_fps)
        self.bind("<Down>", self.decrease_fps)
        fps_button.grid()
        reload = Button(master=buttonFrame, command=self.reload_game, text="Reload")
        reload.grid()
        forward = Button(master=buttonFrame, command=self.forward, text="Forward")
        forward.grid()
        self.bind("<Right>", self.forward)
        backward = Button(master=buttonFrame, command=self.backward, text="Backward")
        backward.grid()
        self.bind("<Left>", self.backward)
        save_button = Button(master=buttonFrame, command=self.save_to_logs, text="Save to logs")
        save_button.grid()
        copy_data_to_clipboard_button = Button(master=buttonFrame, command=self.copy_current_data_to_clipboard, text="Clip")
        copy_data_to_clipboard_button.grid()
        grid_positions = Button(master=buttonFrame, command=self.show_coordinates, text="Coordinates")
        grid_positions.grid()
        engine_calculation = Button(master=buttonFrame, command=self.calculate_this_state_by_engine, text="Engine")
        engine_calculation.grid()
        self.bind("<e>", self.calculate_this_state_by_engine)
        move_calculation = Button(master=buttonFrame, command=self.calculate_moves, text="Calculate moves")
        move_calculation.grid()
        self.bind("<c>", self.calculate_moves)
        return pause, fps_button

    def update_state_list(self):
        data = self.state_queue.get()
        if data == "GAME DONE":
            return
        elif data:
            self.state_list.append(data)
        self.after(10, self.update_state_list)

    def draw_next_state(self):
        if not self.pause and self.state_list:
            if self.turn >= len(self.state_list):
                self.turn = len(self.state_list)-1
            self.draw_on_canvas(self.state_list[self.turn])
            self.update()
            self.turn = self.turn + 1
            if self.turn >= len(self.state_list):
                self.turn = len(self.state_list) - 1
        self.after(1000/self.FPS, self.draw_next_state)

    def draw_on_canvas(self, data):
        canvas = self.canvas
        canvas.delete("all")
        board = data['board']
        height = board['height']
        width = board['width']
        snakes = board['snakes']
        food_locations = board['food']
        danger_map = brain.get_map_of_head_danger(data)

        for x in range(width):
            for y in range(height):
                canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                        fill='white')

        for food in food_locations:
            x = food['x']
            y = food['y']
            canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                    fill='red', outline='black')

        if print_headDanger:
            for x in range(width):
                for y in range(height):
                    pass
                    canvas.create_text((x * block_size + 10, y * block_size + 10)
                                       , text=danger_map[x][y])

        for snake in snakes:
            color = self.snake_color_by_id[snake['id']]
            for body_part, i in zip(snake['body'], range(len(snake['body']))):
                x = body_part['x']
                y = body_part['y']
                canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                        fill=color)

                if i != 0 and snake['body'][i] != snake['body'][i - 1]:
                    off1, off2, off3, off4 = offset(
                        get_direction_between_two_fields(snake['body'][i], snake['body'][i - 1]))
                    canvas.create_line((x * block_size + off1, y * block_size + off2,
                                        (x + 1) * block_size + off3, (y + 1) * block_size + off4)
                                       , fill=color, width=1)
            x = snake['body'][0]['x']
            y = snake['body'][0]['y']
            head_offset = 3
            canvas.create_rectangle((x * block_size + head_offset, y * block_size + head_offset,
                                     (x + 1) * block_size - head_offset, (y + 1) * block_size - head_offset),
                                    fill='purple')
            #assert self.turn == data["turn"], (self.turn, data["turn"])
        self.draw_other_info(data)
        self.update_text_lables(data)

    def draw_other_info(self, data):
        canvas = self.canvas
        board = data['board']
        height = board['height']
        width = board['width']
        snakes = board['snakes']
        food_locations = board['food']
        you = data['you']
        you_head = you['body'][0]
        snake_colors = ['green', 'blue', 'yellow', 'gray', 'brown', 'purple', 'black', 'orange']

        canvas.create_text((width * block_size + 100, 10), text='Turn: ' + str(data['turn']))
        duration_map = brain.create_map_with_duration(data)
        for snake, i in zip(snakes, range(1, len(snakes)+1)):
            info_height = int(snake['id'])*block_size + 30
            color = self.snake_color_by_id[snake['id']]
            canvas.create_text((width * block_size + 10, info_height)
                               , text=snake['name'])
            canvas.create_text((width * block_size + 200, info_height)
                               , text=snake['health'])
            canvas.create_text((width * block_size + 350, info_height)
                               , text=len(snake['body']))
            canvas.create_text(
                (width * block_size + 300, info_height)
                , text=round(brain.get_distance_to_center(data, snake['body'][0]), 2))
            canvas.create_rectangle((width * block_size + 20, info_height - 10,
                                     width * block_size + 20 + snake['health'], info_height - 10 + 20),
                                    fill=color)
            if snake == data['you']:
                canvas.create_text(
                    (width * block_size + 400, info_height)
                    , text="you")

            if print_duration:
                for body_part in snake['body']:
                    canvas.create_text((body_part['x'] * block_size + 10, body_part['y'] * block_size + 10)
                                       , text=duration_map[int(body_part['x'])][int(body_part['y'])])

            if print_reachTime or print_future_duration:
                tiles_others_reach_before_me, future_duration_map = brain.tiles_others_can_reach_before_me(data)
                for tile in tiles_others_reach_before_me:
                    head_offset = 5
                    x = tile['x']
                    y = tile['y']
                    canvas.create_rectangle((x * block_size + head_offset, y * block_size + head_offset,
                                             (x + 1) * block_size - head_offset, (y + 1) * block_size - head_offset),
                                            fill='red')

            if print_future_duration:
                for x in range(width):
                    for y in range(height):
                        canvas.create_text((x * block_size + 10, y * block_size + 10)
                                           , text=future_duration_map[x][y])

            if print_reachTime:
                reach_time_map = brain.create_map_with_reachtime(data, data['you'])
                for x in range(width):
                    for y in range(height):
                        canvas.create_text((x * block_size + 10, y * block_size + 10)
                                           , text=reach_time_map[x][y])

            if print_escape_points:
                deadly_locations_dic = brain.get_deadly_locations_dic(data)
                duration_map = brain.create_map_with_duration(data)
                escape_points, escape_timings = brain.get_escape_points(data, data['you']['body'][0], deadly_locations_dic, brain)

            if print_future_escape_points:
                list_of_tiles_others_reach_before_me, duration_map_if_enemy_moves_to_tile = brain.tiles_others_can_reach_before_me(data)
                deadly_locations = brain.get_deadly_locations(data)
                deadly_locations = deadly_locations + brain.transform_to_tuple_list(list_of_tiles_others_reach_before_me)
                deadly_locations_dic = brain.transform_to_dic_list(deadly_locations)
                # check for duplicates

                escape_points, escape_timings = brain.get_escape_points(data, data['you']['body'][0], deadly_locations_dic, duration_map_if_enemy_moves_to_tile)

            if print_escape_points or print_future_escape_points:
                for tile, timing in zip(escape_points, escape_timings):
                    head_offset = 5
                    x = tile['x']
                    y = tile['y']
                    canvas.create_rectangle((x * block_size + head_offset, y * block_size + head_offset,
                                             (x + 1) * block_size - head_offset, (y + 1) * block_size - head_offset),
                                            fill='orange')
                    canvas.create_text((x * block_size + 10, y * block_size + 10)
                                       , text=str(timing))

    def update_text_lables(self, data):
        for snake in data['board']['snakes']:
            label = self.textWidgets[snake['id']]

            log = ["None"]
            if str(data['turn']) in Logger().logs.keys():
                if snake['id'] in Logger().logs[str(data['turn'])].keys():
                    log = Logger().logs[str(data['turn'])][snake['id']]

            label.delete('1.0', tk.END)
            for line in log:
                label.insert(tk.END, line)
                label.insert(tk.END, "\n")

            label.insert(tk.END, "#"*10)
            label.insert(tk.END, "\n")
        self.update_idletasks()

directions = ['up', 'down', 'left', 'right']

def next_field(direction, currentPosition):
    if direction == 'up':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] - 1}
    elif direction == 'down':
        return {'x': currentPosition['x'], 'y': currentPosition['y'] + 1}
    elif direction == 'left':
        return {'x': currentPosition['x'] - 1, 'y': currentPosition['y']}
    elif direction == 'right':
        return {'x': currentPosition['x'] + 1, 'y': currentPosition['y']}


def get_direction_between_two_fields(start, end):
    for d in directions:
        if end == next_field(d, start):
            return d


def offset(direction):
    size = block_size
    if direction == 'up':
        return 0, 0, 0, -size
    if direction == 'down':
        return 0, size, 0, 0
    if direction == 'left':
        return 0, 0, -size, 0
    if direction == 'right':
        return size, 0, 0, 0
    return 0, 0, 0, 0  # applies at the beginning, when several body parts are on one spot


def empty_state_queue(state_queue):
    while state_queue.get():
        pass

