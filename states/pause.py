import pygame as pg
from StateManager import State

pg.font.init()


class PauseState(State):
    def on_enter(self, frm):
        print("Pausing")

    def update(self, events, dt):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                self.exit("play")

    def draw(self, s):
        """Zeichnet den Pause-Screen mit Logo"""
        w, h = s.get_size()
        
        # Halbtransparenter schwarzer Overlay
        overlay = pg.Surface((w, h), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        s.blit(overlay, (0, 0))
        
        # Pause-Symbol (zwei Balken)
        bar_width = 40
        bar_height = 120
        bar_gap = 30
        bar_color = (255, 255, 255)
        
        # Linker Balken
        left_bar_x = w // 2 - bar_gap // 2 - bar_width
        bar_y = h // 2 - bar_height // 2
        pg.draw.rect(s, bar_color, (left_bar_x, bar_y, bar_width, bar_height), border_radius=10)
        
        # Rechter Balken
        right_bar_x = w // 2 + bar_gap // 2
        pg.draw.rect(s, bar_color, (right_bar_x, bar_y, bar_width, bar_height), border_radius=10)
        
        # "PAUSE" Text
        font = pg.font.SysFont("Arial", 60, bold=True)
        pause_text = font.render("PAUSE", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(w // 2, h // 2 + bar_height // 2 + 50))
        s.blit(pause_text, text_rect)
        
        # Hinweis-Text
        hint_font = pg.font.SysFont("Arial", 24)
        hint_text = hint_font.render("Drücke P zum Fortsetzen", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(w // 2, h // 2 + bar_height // 2 + 100))
        s.blit(hint_text, hint_rect)
