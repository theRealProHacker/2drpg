import sys
import os

# When running as a PyInstaller exe, change to the exe's directory
# so relative paths (assets/, gems_save.json) still work.
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

import pygame as pg

pg.init()

from StateManager import StateManager

from states.play import PlayState
from states.pause import PauseState
from states.menu import MenuState
from states.profile import ProfileState
from circle_collision import CircleCollisionState

pg.display.set_caption("Pirates")
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN | pg.RESIZABLE)

sm = StateManager({"play": PlayState(), "pause": PauseState(), "menu": MenuState(), "profile": ProfileState()}, start="menu")

clock = pg.time.Clock()


def main():
    while True:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return

        dt = clock.tick(60)
        sm.update(events, dt)

        screen.fill("white")

        sm.draw(screen)

        pg.display.flip()


main()
