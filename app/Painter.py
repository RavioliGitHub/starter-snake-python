from Tkinter import Tk, Label, Button, Canvas, Frame
import game_engine
import time
import brain
#import pyperclip
import main
import pprint
block_size = 20


class Window(Tk):
    def __init__(self, data, state_queue):
        Tk.__init__(self, className="MySnakeWindow")
        self.height = data['board']['height']
        self.width = data['board']['width']
        self.state_queue = state_queue
        self.state_list = []
        self.turn = 0
        self.pause = False
        self.FPS = 60
        self.snake_color_by_id = self.create_snake_color_by_id(data)
        self.canvas = Canvas(master=self, width=self.width * block_size * 2 + 700, height=self.height * block_size)
        self.canvas.pack()
        self.pause_replay, self.fps_button = self.create_buttons()
        self.Frame = Frame(self)
        time.sleep(1)
        self.after(10, self.update_state_list)
        self.after(1000/self.FPS, self.draw_next_state)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def calculate_moves(self, *args):
        data = self.state_list[self.turn]
        snakes = data['board']['snakes']
        for snake in snakes:
            data['you'] = snake
            print(snake['name'], main.get_move_response_string(data))

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
        self.bind("<Escape>", self.on_closing)
        pause = Button(master=self, command=self.pause_flip, text="Pause")
        pause.pack()
        self.bind("<space>", self.pause_flip)
        fps_button = Button(master=self, text=self.FPS)
        fps_button.bind('<Button-1>', self.increase_fps)
        self.bind("<Up>", self.increase_fps)
        fps_button.bind('<Button-3>', self.decrease_fps)
        self.bind("<Down>", self.decrease_fps)
        fps_button.pack()
        reload = Button(master=self, command=self.reload_game, text="Reload")
        reload.pack()
        forward = Button(master=self, command=self.forward, text="Forward")
        forward.pack()
        self.bind("<Right>", self.forward)
        backward = Button(master=self, command=self.backward, text="Backward")
        backward.pack()
        self.bind("<Left>", self.backward)
        save_button = Button(master=self, command=self.save_to_logs, text="Save to logs")
        save_button.pack()
        copy_data_to_clipboard_button = Button(master=self, command=self.copy_current_data_to_clipboard, text="Clip")
        copy_data_to_clipboard_button.pack()
        grid_positions = Button(master=self, command=self.show_coordinates, text="Coordinates")
        grid_positions.pack()
        engine_calculation = Button(master=self, command=self.calculate_this_state_by_engine, text="Engine")
        engine_calculation.pack()
        self.bind("<e>", self.calculate_this_state_by_engine)
        move_calculation = Button(master=self, command=self.calculate_moves, text="Calculate moves")
        move_calculation.pack()
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

        for x in range(width):
            for y in range(height):
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
            head_offset = 5
            canvas.create_rectangle((x * block_size + head_offset, y * block_size + head_offset,
                                     (x + 1) * block_size - head_offset, (y + 1) * block_size - head_offset),
                                    fill='purple')
            assert self.turn == data["turn"], (self.turn, data["turn"])
            self.draw_other_info(data)

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

            for body_part in snake['body']:
                canvas.create_text((body_part['x'] * block_size + 10, body_part['y'] * block_size + 10)
                                   , text=duration_map[int(body_part['x'])][int(body_part['y'])])


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

