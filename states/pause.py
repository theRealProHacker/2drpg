from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast

import pygame as pg
import math
from StateManager import State

if TYPE_CHECKING:
    from states.play import PlayState

pg.font.init()

# Pirate farewell lines
PIRATE_FAREWELL_LINES = [
    "Arr! Come back tomorrow,\nye landlubber!",
    "Hey! Don't forget\nto come aboard again\ntomorrow, sailor!",
    "By Davy Jones!\nI'll be expectin' ye\nback here tomorrow!",
    "Yo ho ho! Until tomorrow,\nmatey! The sea\nawaits ye!",
    "Don't sail too far away!\nTomorrow we set sail\nonce more!",
    "Avast! A true pirate\nalways comes back.\nPromise?",
]


class PauseState(State):
    def __init__(self):
        self.font_title = pg.font.SysFont("Arial", 52, bold=True)
        self.font_heading = pg.font.SysFont("Arial", 26, bold=True)
        self.font_main = pg.font.SysFont("Arial", 20)
        self.font_small = pg.font.SysFont("Arial", 16)
        self.font_key = pg.font.SysFont("Arial", 14, bold=True)
        self.timer = 0
        self.selected_button = 0  # 0=Resume, 1=Quit
        self.mouse_hover = -1
        self.effect_hover = -1
        self.last_mouse_pos = (0, 0)
        self._effect_rects = []

    def on_enter(self, frm):
        print("Pausing")
        self.timer = 0
        self.selected_button = 0
        self.mouse_hover = -1
        self.effect_hover = -1
        self._effect_rects = []

    def _get_play_state(self) -> PlayState | None:
        """Holt den PlayState für Stats-Anzeige"""
        try:
            return cast("PlayState", self.manager["play"])
        except Exception:
            return None

    def _do_actual_quit(self):
        """Wirklich zum Menü wechseln"""
        play = self._get_play_state()
        if play and hasattr(play, 'sfx'):
            play.sfx.stop_ocean_ambience()
            play.sfx.stop_battle_music()
        self.exit("menu")

    def update(self, events, dt):
        dt_seconds = dt / 1000.0
        self.timer += dt_seconds

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_p, pg.K_ESCAPE):
                    self.exit("play")
                elif event.key == pg.K_q:
                    self._do_actual_quit()
                elif event.key == pg.K_UP or event.key == pg.K_w:
                    self.selected_button = 0
                elif event.key == pg.K_DOWN or event.key == pg.K_s:
                    self.selected_button = 1
                elif event.key == pg.K_RETURN:
                    if self.selected_button == 0:
                        self.exit("play")
                    else:
                        self._do_actual_quit()
            elif event.type == pg.MOUSEMOTION:
                self._check_hover(event.pos)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if self.mouse_hover >= 0:
                    if self.mouse_hover == 0:
                        self.exit("play")
                    elif self.mouse_hover == 1:
                        self._do_actual_quit()

    def _check_hover(self, mouse_pos):
        """Prüft ob Maus über einem Button ist"""
        self.last_mouse_pos = mouse_pos
        self.mouse_hover = -1
        self.effect_hover = -1
        # Buttons werden in draw berechnet, hier cachen wir die Rects
        if hasattr(self, '_button_rects'):
            for i, rect in enumerate(self._button_rects):
                if rect.collidepoint(mouse_pos):
                    self.mouse_hover = i
                    self.selected_button = i

        for i, rect in enumerate(getattr(self, '_effect_rects', [])):
            if rect.collidepoint(mouse_pos):
                self.effect_hover = i
                break

    def _draw_rounded_panel(self, surface, rect, bg_color, border_color, border_width=2, radius=12):
        """Zeichnet ein abgerundetes Panel mit Hintergrund und Rahmen"""
        panel = pg.Surface((rect[2], rect[3]), pg.SRCALPHA)
        pg.draw.rect(panel, bg_color, (0, 0, rect[2], rect[3]), border_radius=radius)
        pg.draw.rect(panel, border_color, (0, 0, rect[2], rect[3]), border_width, border_radius=radius)
        surface.blit(panel, (rect[0], rect[1]))

    def _draw_stat_row(self, surface, x, y, icon_color, label, value, value_color=(220, 220, 240)):
        """Zeichnet eine Stat-Zeile mit farbigem Punkt"""
        pg.draw.circle(surface, icon_color, (x + 8, y + 10), 6)
        pg.draw.circle(surface, (255, 255, 255, 80), (x + 8, y + 10), 6, 1)
        label_surf = self.font_main.render(label, True, (170, 180, 200))
        surface.blit(label_surf, (x + 22, y))
        val_surf = self.font_main.render(str(value), True, value_color)
        surface.blit(val_surf, (x + 180, y))

    def _draw_upgrade_bar(self, surface, x, y, w_bar, label, level, color, key_num):
        """Zeichnet eine Upgrade-Zeile mit Fortschrittsbalken"""
        # Key Badge
        key_bg = pg.Surface((22, 22), pg.SRCALPHA)
        pg.draw.rect(key_bg, (40, 50, 80, 200), (0, 0, 22, 22), border_radius=4)
        pg.draw.rect(key_bg, (80, 100, 140), (0, 0, 22, 22), 1, border_radius=4)
        key_text = self.font_key.render(str(key_num), True, (200, 210, 230))
        key_bg.blit(key_text, (11 - key_text.get_width() // 2, 3))
        surface.blit(key_bg, (x, y))
        # Label
        label_surf = self.font_small.render(label, True, (180, 190, 210))
        surface.blit(label_surf, (x + 28, y + 2))
        # Bar background
        bar_x = x + 110
        bar_w = w_bar - 120
        bar_h = 14
        pg.draw.rect(surface, (20, 25, 40), (bar_x, y + 4, bar_w, bar_h), border_radius=4)
        # Filled segments (max 20)
        max_segs = 20
        seg_w = (bar_w - 4) / max_segs
        for i in range(min(level, max_segs)):
            sx = bar_x + 2 + i * seg_w
            pg.draw.rect(surface, color, (int(sx), y + 6, max(1, int(seg_w - 1)), bar_h - 4), border_radius=2)
        # Border
        pg.draw.rect(surface, (*color[:3], 120), (bar_x, y + 4, bar_w, bar_h), 1, border_radius=4)
        # Level text
        lvl_text = self.font_small.render(f"Lv {level}", True, color)
        surface.blit(lvl_text, (bar_x + bar_w + 6, y + 1))

    def draw(self, s):
        """Zeichnet den aufgewerteten Pause-Screen"""
        w, h = s.get_size()
        play = self._get_play_state()

        # --- Hintergrund: Spiel zeichnen (eingefroren) ---
        if play:
            play.draw(s)

        # --- Dunkler Overlay mit leichtem Vignette-Effekt ---
        overlay = pg.Surface((w, h), pg.SRCALPHA)
        overlay.fill((5, 10, 25, 170))
        s.blit(overlay, (0, 0))

        # Subtile animierte Wellen-Linien oben und unten
        wave_alpha_surf = pg.Surface((w, 4), pg.SRCALPHA)
        for wx in range(0, w, 3):
            wy_top = int(math.sin(wx * 0.02 + self.timer * 1.5) * 2)
            wy_bot = int(math.sin(wx * 0.02 + self.timer * 1.5 + 1) * 2)
            pg.draw.rect(wave_alpha_surf, (60, 120, 180, 40), (wx, 0, 2, 4))
        s.blit(wave_alpha_surf, (0, 4 + int(math.sin(self.timer) * 2)))
        s.blit(wave_alpha_surf, (0, h - 8 + int(math.sin(self.timer + 1) * 2)))

        # ==================== LAYOUT ====================
        # Zentrales Panel
        panel_w = min(520, w - 40)
        panel_h = min(460, h - 40)
        panel_x = w // 2 - panel_w // 2
        panel_y = h // 2 - panel_h // 2

        # Hauptpanel Hintergrund
        main_panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        # Gradient-ähnlicher Hintergrund
        for py_row in range(panel_h):
            t = py_row / panel_h
            r = int(8 + 12 * t)
            g = int(14 + 16 * t)
            b = int(32 + 20 * t)
            pg.draw.line(main_panel, (r, g, b, 230), (0, py_row), (panel_w, py_row))
        pg.draw.rect(main_panel, (60, 90, 140, 150), (0, 0, panel_w, panel_h), 2, border_radius=14)
        # Gold-Akzent oben
        pg.draw.line(main_panel, (180, 150, 60, 180), (20, 2), (panel_w - 20, 2), 2)
        s.blit(main_panel, (panel_x, panel_y))

        # --- Titel: PAUSED ---
        pulse = abs(math.sin(self.timer * 2)) * 0.2 + 0.8
        title_color = (int(220 * pulse), int(200 * pulse), int(140 * pulse))
        title_shadow = self.font_title.render("⚓ PAUSED", True, (10, 8, 2))
        title_text = self.font_title.render("⚓ PAUSED", True, title_color)
        title_rect = title_text.get_rect(centerx=w // 2, top=panel_y + 14)
        s.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        s.blit(title_text, title_rect)

        # Trennlinie
        line_y = panel_y + 72
        pg.draw.line(s, (60, 80, 120, 120), (panel_x + 20, line_y), (panel_x + panel_w - 20, line_y), 1)
        pg.draw.line(s, (180, 150, 80, 80), (panel_x + panel_w // 4, line_y + 1), (panel_x + panel_w * 3 // 4, line_y + 1), 1)

        # ==================== STATS PANEL (links) ====================
        content_y = line_y + 12
        half_w = (panel_w - 40) // 2

        if play:
            # --- Linke Seite: Game Stats ---
            stats_x = panel_x + 16
            section_heading = self.font_heading.render("Stats", True, (180, 200, 240))
            s.blit(section_heading, (stats_x + 4, content_y))

            sy = content_y + 32
            survival_min = int(play.survival_time // 60)
            survival_sec = int(play.survival_time % 60)
            current_max_hp = play.base_max_health + play.max_health_level * 20
            difficulty = play.get_difficulty()

            # HP
            hp_color = (50, 200, 50) if play.health > 60 else ((200, 200, 50) if play.health > 30 else (200, 50, 50))
            self._draw_stat_row(s, stats_x, sy, (200, 60, 60), "Health", f"{int(play.health)}/{current_max_hp}", hp_color)
            sy += 28
            # Level
            self._draw_stat_row(s, stats_x, sy, (80, 140, 255), "Level", f"{play.level}", (120, 180, 255))
            sy += 28
            # Kills
            self._draw_stat_row(s, stats_x, sy, (200, 80, 80), "Kills", f"{play.kills}", (255, 120, 120))
            sy += 28
            # Time
            self._draw_stat_row(s, stats_x, sy, (100, 200, 255), "Time", f"{survival_min}:{survival_sec:02d}", (160, 210, 255))
            sy += 28
            # Gems
            self._draw_stat_row(s, stats_x, sy, (255, 200, 50), "Gems", f"{play.total_gems}", (255, 220, 100))
            sy += 28
            # Difficulty
            diff_r = min(255, 100 + int(difficulty * 30))
            diff_g = max(80, 255 - int(difficulty * 40))
            diff_color = (diff_r, diff_g, 100)
            self._draw_stat_row(s, stats_x, sy, diff_color, "Difficulty", f"x{difficulty:.1f}", diff_color)
            sy += 28
            # Skill Points
            if play.skill_points > 0:
                self._draw_stat_row(s, stats_x, sy, (255, 220, 50), "Skill Pts", f"{play.skill_points}", (255, 240, 100))

            # --- Rechte Seite: Upgrades ---
            upgrades_x = panel_x + half_w + 30
            up_heading = self.font_heading.render("Upgrades", True, (180, 200, 240))
            s.blit(up_heading, (upgrades_x + 4, content_y))

            uy = content_y + 34
            bar_w = half_w - 16
            self._draw_upgrade_bar(s, upgrades_x, uy, bar_w, "Speed", play.speed_level, (50, 200, 120), 1)
            uy += 28
            self._draw_upgrade_bar(s, upgrades_x, uy, bar_w, "Fire Rate", play.fire_rate_level, (255, 150, 50), 2)
            uy += 28
            self._draw_upgrade_bar(s, upgrades_x, uy, bar_w, "Repair", play.regen_level, (50, 200, 50), 3)
            uy += 28
            self._draw_upgrade_bar(s, upgrades_x, uy, bar_w, "Health", play.max_health_level, (200, 60, 60), 4)
            uy += 28
            self._draw_upgrade_bar(s, upgrades_x, uy, bar_w, "Damage", play.damage_level, (200, 100, 255), 5)

            # Vertikale Trennlinie zwischen Stats und Upgrades
            vline_x = panel_x + half_w + 18
            pg.draw.line(s, (50, 70, 110, 100), (vline_x, content_y + 8), (vline_x, content_y + 210), 1)

            # --- Run-Effekte aus Kisten ---
            self._effect_rects = []
            effects = getattr(play, 'active_crate_effects', [])
            fx_x = upgrades_x
            fx_y = content_y + 182
            fx_heading = self.font_small.render("Crate Effects", True, (180, 200, 240))
            s.blit(fx_heading, (fx_x + 4, fx_y))

            if effects:
                row_y = fx_y + 22
                max_rows = 3
                for idx, eff in enumerate(effects[:max_rows]):
                    rect = pg.Rect(fx_x, row_y + idx * 22, bar_w + 12, 20)
                    self._effect_rects.append(rect)
                    is_hover = self.effect_hover == idx

                    bg = (25, 35, 58, 190) if not is_hover else (40, 55, 86, 230)
                    pg.draw.rect(s, bg, rect, border_radius=6)
                    pg.draw.rect(s, (*eff['color'], 180), rect, 1, border_radius=6)

                    label = f"{eff['name']} x{eff['stacks']}"
                    txt = self.font_small.render(label, True, (220, 230, 250))
                    s.blit(txt, (rect.x + 8, rect.y + 2))

                if self.effect_hover >= 0 and self.effect_hover < len(effects[:max_rows]):
                    hover_eff = effects[self.effect_hover]
                    mx, my = self.last_mouse_pos
                    tip = f"{hover_eff['desc']} (Stacks: {hover_eff['stacks']})"
                    tip_surf = self.font_small.render(tip, True, (245, 235, 210))
                    tip_box = pg.Rect(mx + 14, my - 26, tip_surf.get_width() + 12, tip_surf.get_height() + 8)
                    pg.draw.rect(s, (18, 24, 38, 240), tip_box, border_radius=6)
                    pg.draw.rect(s, (*hover_eff['color'], 190), tip_box, 1, border_radius=6)
                    s.blit(tip_surf, (tip_box.x + 6, tip_box.y + 4))
            else:
                none_txt = self.font_small.render("No active effects", True, (130, 145, 170))
                s.blit(none_txt, (fx_x + 6, fx_y + 25))

        # ==================== BUTTONS ====================
        btn_y = panel_y + panel_h - 100
        btn_w = 180
        btn_h = 42
        btn_gap = 24
        total_btns_w = btn_w * 2 + btn_gap
        btn_start_x = w // 2 - total_btns_w // 2

        buttons = [
            ("Resume", (40, 120, 80), (60, 180, 100), "ESC"),
            ("Quit to Menu", (120, 40, 40), (180, 60, 60), "Q"),
        ]
        self._button_rects = []

        for i, (label, color, hover_color, key) in enumerate(buttons):
            bx = btn_start_x + i * (btn_w + btn_gap)
            rect = pg.Rect(bx, btn_y, btn_w, btn_h)
            self._button_rects.append(rect)

            is_selected = (self.selected_button == i)
            is_hover = (self.mouse_hover == i)

            # Button background
            btn_surf = pg.Surface((btn_w, btn_h), pg.SRCALPHA)
            if is_selected or is_hover:
                bg = (*hover_color, 220)
                border = (255, 255, 255, 200)
                text_col = (255, 255, 255)
            else:
                bg = (*color, 160)
                border = (140, 140, 160, 120)
                text_col = (200, 200, 210)
            pg.draw.rect(btn_surf, bg, (0, 0, btn_w, btn_h), border_radius=8)
            pg.draw.rect(btn_surf, border, (0, 0, btn_w, btn_h), 2, border_radius=8)

            # Selection indicator
            if is_selected:
                indicator_pulse = abs(math.sin(self.timer * 4)) * 0.4 + 0.6
                ind_color = (255, 255, 255, int(indicator_pulse * 180))
                pg.draw.rect(btn_surf, ind_color, (4, 4, 3, btn_h - 8), border_radius=2)

            s.blit(btn_surf, (bx, btn_y))

            # Button text
            btn_text = self.font_main.render(label, True, text_col)
            text_rect = btn_text.get_rect(center=(bx + btn_w // 2, btn_y + btn_h // 2))
            s.blit(btn_text, text_rect)

            # Key hint (kleine Badge rechts oben am Button)
            key_surf = pg.Surface((26, 18), pg.SRCALPHA)
            pg.draw.rect(key_surf, (20, 30, 50, 200), (0, 0, 26, 18), border_radius=4)
            pg.draw.rect(key_surf, (70, 90, 120), (0, 0, 26, 18), 1, border_radius=4)
            key_text = self.font_key.render(key, True, (160, 180, 210))
            key_surf.blit(key_text, (13 - key_text.get_width() // 2, 1))
            s.blit(key_surf, (bx + btn_w - 30, btn_y - 6))

        # ==================== BOTTOM HINTS ====================
        hint_y = panel_y + panel_h - 30
        hints = "↑↓ Navigate  ·  Enter Select  ·  ESC Resume  ·  Q Quit"
        hint_surf = self.font_small.render(hints, True, (100, 110, 140))
        hint_rect = hint_surf.get_rect(centerx=w // 2, top=hint_y)
        s.blit(hint_surf, hint_rect)

        # Dekorative Ecken (Anker-Ornamente)
        corner_color = (100, 130, 170, 80)
        # Oben links
        corner_size = 16
        cx, cy = panel_x + 8, panel_y + 8
        pg.draw.line(s, corner_color, (cx, cy), (cx + corner_size, cy), 2)
        pg.draw.line(s, corner_color, (cx, cy), (cx, cy + corner_size), 2)
        # Oben rechts
        cx2 = panel_x + panel_w - 8
        pg.draw.line(s, corner_color, (cx2, cy), (cx2 - corner_size, cy), 2)
        pg.draw.line(s, corner_color, (cx2, cy), (cx2, cy + corner_size), 2)
        # Unten links
        cy2 = panel_y + panel_h - 8
        pg.draw.line(s, corner_color, (cx, cy2), (cx + corner_size, cy2), 2)
        pg.draw.line(s, corner_color, (cx, cy2), (cx, cy2 - corner_size), 2)
        # Unten rechts
        pg.draw.line(s, corner_color, (cx2, cy2), (cx2 - corner_size, cy2), 2)
        pg.draw.line(s, corner_color, (cx2, cy2), (cx2, cy2 - corner_size), 2)
