
from tkinter import Tk, Label, Button, Canvas, Frame
import time
block_size = 20


class Window(Tk):
    def __init__(self, data, state_queue):
        Tk.__init__(self, className="MySnakeWindow")
        height = data['board']['height']
        width = data['board']['width']
        self.state_queue = state_queue
        self.canvas = Canvas(master=self, width=width * block_size * 2, height=height * block_size)
        self.canvas.pack()
        self.Frame = Frame(self)
        self.after(10, self.draw_next_state)
        self.mainloop()

    def draw_next_state(self):
        data = self.state_queue.get()
        if data == "GAME DONE":
            print("ebgf")
            time.sleep(5)
            for i in range(5):
                print(i)
                time.sleep(1)
            self.destroy()
        elif data:
            self.draw_on_canvas(data)
        self.after(10, self.draw_next_state)

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

