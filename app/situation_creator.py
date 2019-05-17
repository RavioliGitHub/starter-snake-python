from Tkinter import Tk, Label, Button, Canvas, Frame
import game_engine
import time
import brain
#import pyperclip
import main
import thread
from functools import partial
block_size = 40
directions = ['up', 'down', 'left', 'right']
elements = ['food', 1, 2, 3, 4, 5, 6, 7, 8]
colors = ['red', 'green', 'blue', 'yellow', 'gray', 'brown', 'purple', 'black', 'orange']
el_color_by_id = {}
for el, color in zip(elements, colors):
        el_color_by_id[el] = color


class Window(Tk):
    def __init__(self, state_queue):
        Tk.__init__(self, className="MyCreatorWindow")
        self.canvas = Canvas(master=self, width=10 * block_size * 2 + 500, height=10 * block_size)
        self.canvas.pack()
        self.Frame = Frame(self)
        self.element_to_add = elements[0]
        self.data = create_void_data()
        self.canvas.bind("<ButtonPress-1>", self.add_element)
        self.canvas.bind("<ButtonPress-3>", self.clear_tile)
        self.canvas.bind("<B1-Motion>", self.add_element)
        self.canvas.bind("<B3-Motion>", self.clear_tile)
        self.canvas.bind_all('<MouseWheel>', self.on_scroll)
        self.add_buttons()
        self.after(100, self.draw)
        self.state_queue = state_queue
        self.mainloop()

    def draw(self):
        data = self.data
        canvas = self.canvas
        canvas.delete("all")
        board = data['board']
        height = board['height']
        width = board['width']
        snakes = board['snakes']
        food_locations = board['food']

        for x in range(width):
            for y in range(height):
                canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                        fill='white')

        y = 2
        for x in range(width, width + 9):
            bd_width = 2
            if elements[x - width] == self.element_to_add:
                bd_width = 10
            canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                    fill=el_color_by_id[elements[x - width]], width=bd_width)

        for food in food_locations:
            x = food['x']
            y = food['y']
            canvas.create_rectangle((x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size),
                                    fill='red', outline='black')

        for snake in snakes:
            color = el_color_by_id[snake['id']]
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
        self.after(100, self.draw)

    def add_element(self, *args):
        event = args[0]
        x, y = event.x/block_size, event.y/block_size
        if self.empty(x, y):
            if self.element_to_add == "food":
                self.add_food(x, y)
            elif self.element_to_add is not None:
                self.add_snake_part(self.element_to_add, x, y)

    def clear_tile(self, *args):
        event = args[0]
        x, y = event.x / block_size, event.y / block_size
        data = self.data
        tile = to_dic((x, y))
        if tile in data['board']['food']:
            data['board']['food'].remove(tile)
        for snake in data['board']['snakes']:
            while tile in snake['body']:
                snake['body'].remove(tile)
            if not snake['body']:
                data['board']['snakes'].remove(snake)

    def add_food(self, *coord):
        self.data['board']['food'].append(to_dic(coord))

    def add_snake_part(self, snake_id, *coord):
        data = self.data
        for snake in data['board']['snakes']:
            if snake['id'] == snake_id:
                for d in directions:
                    if next_field(d, snake['body'][-1]) == to_dic(coord):
                        snake['body'].append(to_dic(coord))
                    #TODO iff snake length 3
                return
        # if snake not found
        snake = create_void_snake(snake_id)
        for i in range(3):
            snake['body'].append(to_dic(coord))
        data['board']['snakes'].append(snake)

    def empty(self, *coord):
        data = self.data
        tile = to_dic(coord)
        empty_tiles = []
        for x in range(data['board']['width']):
            for y in range(data['board']['height']):
                empty_tiles.append({'x': x, 'y': y})
        for location in data['board']['food']:
            empty_tiles.remove(location)
        for snake in data['board']['snakes']:
            for location in snake['body']:
                if location in empty_tiles:
                    empty_tiles.remove(location)
        return tile in empty_tiles

    def set_el(self, e):
        self.element_to_add = e

    def add_buttons(self):
        for e in elements:
            button = Button(master=self, text=str(e), command=partial(self.set_el, e))
            button.pack()
        run = Button(master=self, text="Run", command=self.run_game)
        run.pack()
        self.bind("<r>", self.run_game)

    def on_scroll(self, *args):
        event = args[0]
        if event.delta < 0:
            self.element_to_add = elements[(elements.index(self.element_to_add) + 1) % 9]
        else:
            self.element_to_add = elements[(elements.index(self.element_to_add) - 1) % 9]

    def run_game(self, *args):
        self.data['you'] = self.data['board']['snakes'][0]
        # thread.start_new_thread(local_game_master.run_game_from_drawing, (self.data, self))
        self.state_queue.put(self.data)
        self.destroy()

def to_dic(coord):
    return {'x': coord[0], 'y': coord[1]}


def create_void_data():
    data = {"turn": 0,
            'game': {'id': 'ID_FILLER'},
            'board': {'food': [],
                      'width': 11,
                      'height': 11,
                      'snakes': []},
            'you': None}
    return data


def create_void_snake(snake_id):
    snake = {"id": snake_id,
             "name": snake_id,
             "health": 100,
             "body": []}
    return snake


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

