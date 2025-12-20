import pygame as pg

pg.init()

from StateManager import StateManager

from states.play import PlayState
from states.pause import PauseState
from circle_collision import CircleCollisionState

pg.display.set_caption("Pirates")
screen = pg.display.set_mode((960, 540), pg.RESIZABLE)

sm = StateManager({"play": PlayState(), "pause": PauseState(),}, start="play")

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
