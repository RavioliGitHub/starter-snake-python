from tkinter import Tk, Label, Button
import tkinter
import pyautogui
import json
import urllib


root = Tk()
i = 0
log_read = open('log.txt', 'r')
content = log_read.read()
split_content = content.split('\n')
log_read.close()


def represent_line():
    global i
    line = split_content[i]
    represent(json.loads(line))
    i += 1
    root.after(30, represent_line)
    root.update()


def represent(data):
    board = data['board']
    height = board['height']
    width = board['width']
    snakes = board['snakes']
    food_locations = board['food']
    you = data['you']
    you_head = you['body'][0]
    snake_colors = ['green', 'blue', 'yellow', 'gray', 'brown', 'purple', 'black', 'orange']
    block_size = 20

    canvas = tkinter.Canvas(width=width*block_size, height=height*block_size)


    for x in range(width):
        for y in range(height):
            canvas = tkinter.Canvas(width=30, height=30, bd=3)
            canvas.create_rectangle((0, 0, 200, 200), fill='white')
            canvas.grid(row=y, column=x)

    for food in food_locations:
        canvas = tkinter.Canvas(width=30, height=30, bd=3)
        canvas.create_rectangle((0, 0, 200, 200), fill='red')
        canvas.grid(row=food['y'], column=food['x'])

    for snake, color in zip(snakes, snake_colors):
        for body_part in snake['body']:
            canvas = tkinter.Canvas(width=30, height=30, bd=3)
            canvas.create_rectangle((0, 0, 200, 200), fill=color)
            canvas.grid(row=body_part['y'], column=body_part['x'])


test_data = json.loads('{"game": {"id": "3553defc-bfab-4dc2-8ccf-fcb8a150b90b"}, "turn": 0, "board": {"height": 15, "width": 15, "food": [{"x": 14, "y": 1}, {"x": 5, "y": 4}, {"x": 9, "y": 4}, {"x": 12, "y": 2}, {"x": 14, "y": 13}, {"x": 9, "y": 8}, {"x": 6, "y": 12}, {"x": 13, "y": 13}, {"x": 0, "y": 0}, {"x": 12, "y": 3}], "snakes": [{"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}]}, "you": {"id": "23123a2d-c77d-499e-8d34-c6a25176c1e1", "name": "1", "health": 100, "body": [{"x": 7, "y": 2}, {"x": 7, "y": 2}, {"x": 7, "y": 2}]}}')
root.after(500, represent_line)
root.mainloop()
