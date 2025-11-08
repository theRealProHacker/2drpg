from time import time

import pygame as pg
from StateManager import State

from spritesheet import spritesheet

pg.font.init()

font: pg.font.FontType = pg.font.SysFont("Arial", 100)


def white2transparent(surf: pg.Surface):
    w, h = surf.get_size()

    for x in range(w):
        for y in range(h):
            if surf.get_at((x, y)) == pg.Color("white"):
                surf.set_at((x, y), pg.Color(0, 0, 0, 0))


richtungen = [
    pg.Vector2(x).normalize()
    for x in [
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]
]


class PlayState(State):
    def __init__(self):
        self.text: pg.Surface = font.render("Play", True, "black")
        
        self.col_text: pg.Surface = font.render("Collision", True, "black")
        self.ncol_text: pg.Surface = font.render("No Collision", True, "black")
        self.spritesheet = spritesheet("assets/Ocean_SpriteSheet.png")

        # load insel
        self.insel = pg.image.load("assets/Insel.png")
        self.insel = pg.transform.scale2x(self.insel)
        self.insel = pg.transform.scale2x(self.insel)
        self.mask_insel=pg.mask.from_surface(surface=self.insel)

        # load schiff
        self.schiff1 = pg.image.load("assets/Schiff 1.png").convert_alpha()
        white2transparent(self.schiff1)
        self.schiff1 = pg.transform.scale2x(self.schiff1)

        # mit Segel
        self.schiff2 = pg.image.load("assets/Schiff 2.png").convert_alpha()
        white2transparent(self.schiff2)
        self.schiff2 = pg.transform.scale2x(self.schiff2)
        self.mask_schiff2=pg.mask.from_surface(surface=self.schiff2)

        self.cords_schiff1 = pg.Vector2(600, 100)
        self.schiff_richtung = 0
        self.moving = False
        self.clock = pg.time.Clock()
        # [
        #     pg.Rect(0,0,64,64),
        #     pg.Rect(64,0,64,64),
        #     pg.Rect(128,0,64,64),
        #     pg.Rect(192,0,64,64),
        # ]

        self.tiles = self.spritesheet.images_at(
            [pg.Rect(i * 64, 0, 64, 64) for i in range(4)]
        )
    # def collide(self, other):
    #     ...
        
    def on_enter(self, frm):
        print("Playing")

    def update(self, events, dt):
        # This is an example for handling events
        # and changing states
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.exit("pause")
                elif event.key == pg.K_a:
                    self.schiff_richtung -= 1
                    self.schiff_richtung %= 8
                elif event.key == pg.K_d:
                    self.schiff_richtung += 1
                    self.schiff_richtung %= 8
        
        self.schiff = pg.transform.rotate(
            self.schiff1 if not self.moving else self.schiff2,
            self.schiff_richtung * -45,
        )

        # movement
        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff=pg.mask.from_surface(surface=self.schiff)

        # save old values for undo
        old_collision_area = self.mask_insel.overlap_area(mask_schiff, self.schiff_rect.topleft)
        old_cords = self.cords_schiff1.copy()

        # actual movement with w and s
        if pg.key.get_pressed()[pg.K_w]:
            self.cords_schiff1 += richtungen[self.schiff_richtung] / dt * 50
            self.moving = True
        else:
            self.moving = False

        if pg.key.get_pressed()[pg.K_s]:
            self.cords_schiff1 -= richtungen[self.schiff_richtung] / dt * 25

        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff=pg.mask.from_surface(surface=self.schiff)

        new_collision_area = self.mask_insel.overlap_area(mask_schiff, self.schiff_rect.topleft)

        # if new collision area is greater than old collision area, undo movement
        if new_collision_area > old_collision_area:
            self.cords_schiff1 = old_cords
            
        

    def draw(self, s):
        """
        Whatever you want to draw
        s is the surface or screen you may draw to
        """
        # w,h = pg.display.get_window_size()
        # rect = self.text.get_rect(center = (w//2, h//2))

        # s.blit(self.text, rect)

        # Ozean
        tile = int(time() * 2)

        for i in range(25):
            for j in range(20):
                s.blit(self.tiles[(tile + i) % 4], (64 * i, 64 * j))

        # Insel
        s.blit(self.insel, (0, 0))
        
        # schiff1
        s.blit(self.schiff, self.schiff_rect)

    
