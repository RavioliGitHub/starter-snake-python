
from Tkinter import Tk, Label, Button, Canvas, Frame
import time
block_size = 20


class Window(Tk):
    def __init__(self, data, state_queue):
        Tk.__init__(self, className="MySnakeWindow")
        height = data['board']['height']
        width = data['board']['width']
        self.state_queue = state_queue
        self.state_list = []
        self.turn = 0
        self.pause = False
        self.FPS = 80
        self.canvas = Canvas(master=self, width=width * block_size * 2, height=height * block_size)
        self.canvas.pack()
        self.end, self.pause_replay, self.fps_button = self.create_buttons()
        self.Frame = Frame(self)
        self.after(10, self.update_state_list)
        self.after(1000/self.FPS, self.draw_next_state)
        self.mainloop()

    def increase_fps(self, args):
        self.FPS = self.FPS + 10
        self.fps_button["text"] = self.FPS

    def decrease_fps(self, args):
        self.FPS = self.FPS - 10
        if self.FPS < 1:
            self.FPS = 1
        self.fps_button["text"] = self.FPS

    def pause_flip(self):
        self.pause = not self.pause
        if self.pause:
            self.pause_replay["text"] = "Play"
        else:
            self.pause_replay["text"] = "Pause"

    def reload_game(self):
        self.turn = 0
        self.draw_on_canvas(self.state_list[self.turn])

    def forward(self):
        self.turn = self.turn + 1
        if self.turn >= len(self.state_list):
            self.turn = len(self.state_list)-1
        self.draw_on_canvas(self.state_list[self.turn])

    def backward(self):
        self.turn = self.turn - 1
        if self.turn < 0:
            self.turn = 0
        self.draw_on_canvas(self.state_list[self.turn])

    def create_buttons(self):
        end = Button(master=self, command=self.destroy, text="selfdestruction")
        end.pack()
        pause = Button(master=self, command=self.pause_flip, text="Pause")
        pause.pack()
        fps_button = Button(master=self, text=self.FPS)
        fps_button.bind('<Button-1>', self.increase_fps)
        fps_button.bind('<Button-3>', self.decrease_fps)
        fps_button.pack()
        reload = Button(master=self, command=self.reload_game, text="Reload")
        reload.pack()
        forward = Button(master=self, command=self.forward, text="Forward")
        forward.pack()
        backward = Button(master=self, command=self.backward, text="Backward")
        backward.pack()
        return end, pause, fps_button

    def update_state_list(self):
        data = self.state_queue.get()
        if data == "GAME DONE":
            return
        elif data:
            self.state_list.append(data)
        self.after(10, self.update_state_list)

    def draw_next_state(self):
        if not self.pause:
            if self.turn >= len(self.state_list):
                self.turn = len(self.state_list)-1
            self.draw_on_canvas(self.state_list[self.turn])
            self.turn = self.turn + 1
        self.after(1000/self.FPS, self.draw_next_state)

    def draw_on_canvas(self, data):
        canvas = self.canvas
        canvas.delete("all")
        self.draw_other_info(data)
        board = data['board']
        height = board['height']
        width = board['width']
        snakes = board['snakes']
        food_locations = board['food']
        you = data['you']
        you_head = you['body'][0]
        snake_colors = ['green', 'blue', 'yellow', 'gray', 'brown', 'purple', 'black', 'orange']

        for x in range(width):
            for y in range(height):
                canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                        fill='white')

        for food in food_locations:
            x = food['x']
            y = food['y']
            canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                    fill='red', outline='black')

        for snake, color in zip(snakes, snake_colors):
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

        for snake, i in zip(snakes, range(1, len(snakes)+1)):
            canvas.create_text((width * block_size + 10, round(height/len(snakes)*block_size*i-block_size/2))
                               , text=snake['name'])
            canvas.create_text((width * block_size + 100, round(height / len(snakes) * block_size * i - block_size / 2))
                               , text=snake['health'])




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

