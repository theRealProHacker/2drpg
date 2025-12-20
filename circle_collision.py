import pygame as pg
from StateManager import State


class CircleCollisionState(State):
    def __init__(self):
        self.circle1_pos = pg.Vector2(200, 200)
        self.circle1_radius = 50

        self.inside = False

    def update(self, events, dt):
        mouse_pos = pg.Vector2(pg.mouse.get_pos())
        self.inside = mouse_pos.distance_to(self.circle1_pos)<=self.circle1_radius

    def draw(self, s):
        pg.draw.circle(s, "black", self.circle1_pos, self.circle1_radius, 2)

        if self.inside:
            pg.draw.circle(s, "red", self.circle1_pos, 1)
