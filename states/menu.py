import pygame as pg
from StateManager import State


class MenuState(State):
    def update(self, events, dt):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                self.exit("play")

    def draw(self, s):
        """Whatever you want to draw"""
