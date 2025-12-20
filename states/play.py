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
        # text
        self.text: pg.Surface = font.render("Play", True, "black")
        self.col_text: pg.Surface = font.render("Collision", True, "black")
        self.ncol_text: pg.Surface = font.render("No Collision", True, "black")
        
        # Weltgröße
        self.world_size = pg.Vector2(4000, 4000)
        
        # load insel
        self.insel = pg.image.load("assets/Insel.png")
        self.insel = pg.transform.scale2x(self.insel)
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

        # Ozean
        self.spritesheet = spritesheet("assets/Ocean_SpriteSheet.png")
        self.tiles = self.spritesheet.images_at(
            [pg.Rect(i * 64, 0, 64, 64) for i in range(4)]
        )
        # [
        #     pg.Rect(0,0,64,64),
        #     pg.Rect(64,0,64,64),
        #     pg.Rect(128,0,64,64),
        #     pg.Rect(192,0,64,64),
        # ]

        # Steine
        self.rock_img = pg.image.load("assets/Stein.png").convert_alpha()
        self.rock_img = pg.transform.scale_by(self.rock_img, 0.5)
        self.rock_mask = pg.mask.from_surface(self.rock_img)
    
        # camera
        self.camera_pos = pg.Vector2(self.cords_schiff1)
        self.zoom = 1.0
        self.base_zoom = 1.0
        self.move_zoom = 1.1
        self.zoom_speed = 5.0
        self.cam_lerp = 8.0


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
        
        # camera follows ship (smooth)
        self.camera_pos += (self.cords_schiff1 - self.camera_pos) * min(1, dt * self.cam_lerp)

        # zoom logic
        target_zoom = self.move_zoom if self.moving else self.base_zoom
        self.zoom += (target_zoom - self.zoom) * min(1, dt * self.zoom_speed)

        

    def draw(self, s):
        """
        Whatever you want to draw
        s is the surface or screen you may draw to
        """
        w,h = pg.display.get_window_size()
        # rect = self.text.get_rect(center = (w//2, h//2))

        w, h = s.get_size()
        camera_surface = pg.Surface((w, h), pg.SRCALPHA)

        sx, sy = self.schiff_rect.center

        # ocean
        tile = int(time() * 2)
        for i in range(25):
            for j in range(20):
                pos = pg.Vector2(64 * i, 64 * j) - (sx % 64, sy%64)
                camera_surface.blit(self.tiles[(tile + i) % 4], pos)

        # island
        insel_pos = pg.Vector2(0, 0) - self.camera_pos + pg.Vector2(w // 2, h // 2)
        camera_surface.blit(self.insel, insel_pos)

        # ship
        ship_pos = self.schiff_rect.topleft - self.camera_pos + pg.Vector2(w // 2, h // 2)
        camera_surface.blit(self.schiff, ship_pos)

        # zoom
        scaled = pg.transform.smoothscale(
            camera_surface,
            (int(w * self.zoom), int(h * self.zoom))
        )

        zoom_rect = scaled.get_rect(center=(w // 2, h // 2))
        s.blit(scaled, zoom_rect)


    
