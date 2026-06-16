import pygame as pg
import math
import random
import os
import json
from StateManager import State
from sounds import get_sound_manager

# ==================== PERSISTENTE PROFIL-DATEN ====================
GEM_SAVE_FILE = "gems_save.json"


def _load_full_save():
    if os.path.exists(GEM_SAVE_FILE):
        try:
            with open(GEM_SAVE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def load_profile():
    """Lädt das Profil aus der Save-Datei"""
    data = _load_full_save()
    return data.get('profile', {
        'profile_xp': 0,
        'profile_level': 1,
        'talent_points': 0,
        'total_kills': 0,
        'total_playtime': 0,
        'games_played': 0,
        'talents': {},
    })


def save_profile(profile):
    """Speichert das Profil"""
    data = _load_full_save()
    data['profile'] = profile
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_achievement_state():
    """Lädt globalen Achievement-Fortschritt aus der Save-Datei."""
    data = _load_full_save()
    ach = data.get('achievements', {})
    return {
        'total_kills': int(ach.get('total_kills', 0)),
        'total_playtime_seconds': float(ach.get('total_playtime_seconds', 0.0)),
        'unlocked': list(ach.get('unlocked', [])),
    }


def load_unlocked_pirates():
    """Lädt freigeschaltete Piratenklassen."""
    data = _load_full_save()
    base = {'balanced', 'berserker', 'navigator', 'engineer'}
    unlocked = data.get('unlocked_pirates', list(base))
    if not isinstance(unlocked, list):
        return set(base)
    return set(unlocked) | base


def add_profile_xp(xp_amount, kills=0, playtime=0.0):
    """Fügt Profil-XP hinzu und berechnet Level-Ups. Gibt (neues_level, level_ups) zurück."""
    profile = load_profile()
    profile['profile_xp'] = profile.get('profile_xp', 0) + xp_amount
    profile['total_kills'] = profile.get('total_kills', 0) + kills
    profile['total_playtime'] = profile.get('total_playtime', 0) + playtime
    profile['games_played'] = profile.get('games_played', 0) + 1

    level = profile.get('profile_level', 1)
    talent_points = profile.get('talent_points', 0)
    level_ups = 0

    while profile['profile_xp'] >= xp_for_level(level):
        profile['profile_xp'] -= xp_for_level(level)
        level += 1
        talent_points += 1
        level_ups += 1

    profile['profile_level'] = level
    profile['talent_points'] = talent_points
    save_profile(profile)
    return level, level_ups


def xp_for_level(level):
    """XP benötigt für das nächste Level (steigende Kurve)"""
    return int(100 + (level - 1) * 50 + (level - 1) ** 1.5 * 10)


# ==================== TALENT-BAUM DEFINITIONEN ====================
# Jeder Talent-Pfad hat 3 Stufen
TALENT_PATHS = [
    {
        "id": "schatzjaeger",
        "name": "Treasure Hunter",
        "icon_color": (255, 220, 50),
        "tiers": [
            {"name": "Gold Nose", "desc": "+1 Gem per Run", "cost": 1},
            {"name": "Plunderer", "desc": "+2 Gems per Run", "cost": 2},
            {"name": "Treasurer", "desc": "+5 Gems per Run + 25% Gem Chance", "cost": 3},
        ],
    },
    {
        "id": "kanonier",
        "name": "Cannoneer",
        "icon_color": (255, 80, 50),
        "tiers": [
            {"name": "Powder Keg", "desc": "+10% Damage", "cost": 1},
            {"name": "Broadside", "desc": "+15% Fire Rate", "cost": 2},
            {"name": "Devastator", "desc": "Explosions 50% bigger", "cost": 3},
        ],
    },
    {
        "id": "navigator",
        "name": "Navigator",
        "icon_color": (50, 200, 255),
        "tiers": [
            {"name": "Current", "desc": "+10% Speed", "cost": 1},
            {"name": "Compass", "desc": "Minimap shows enemies", "cost": 2},
            {"name": "Ghost Ship", "desc": "+20% Speed + Dodge", "cost": 3},
        ],
    },
    {
        "id": "seebaer",
        "name": "Sea Dog",
        "icon_color": (50, 255, 100),
        "tiers": [
            {"name": "Toughness", "desc": "+20 Max HP", "cost": 1},
            {"name": "Iron Skin", "desc": "+2 HP/s Regen", "cost": 2},
            {"name": "Unstoppable", "desc": "+50 Max HP + Damage Reduction", "cost": 3},
        ],
    },
    {
        "id": "piratenkapitaen",
        "name": "Pirate Captain",
        "icon_color": (200, 100, 255),
        "tiers": [
            {"name": "Experienced", "desc": "+20% more XP", "cost": 2},
            {"name": "Notorious", "desc": "NPCs drop 2x XP", "cost": 3},
            {"name": "Legend", "desc": "All +10%, double Gems", "cost": 4},
        ],
    },
]


ACHIEVEMENTS = [
    {
        'id': 'kill_250',
        'name': 'Deck Cleaner',
        'description': 'Get 250 total kills',
        'type': 'kills',
        'target': 250,
        'reward_gems': 10,
        'unlock_pirate': None,
    },
    {
        'id': 'kill_1000',
        'name': 'Butcher of the Sea',
        'description': 'Get 1000 total kills',
        'type': 'kills',
        'target': 1000,
        'reward_gems': 25,
        'unlock_pirate': 'reaper',
    },
    {
        'id': 'play_60_min',
        'name': 'Veteran Sailor',
        'description': 'Play for 60 total minutes',
        'type': 'playtime',
        'target': 3600,
        'reward_gems': 20,
        'unlock_pirate': 'old_salt',
    },
    {
        'id': 'kill_5000',
        'name': 'Kraken Bane',
        'description': 'Get 5000 total kills',
        'type': 'kills',
        'target': 5000,
        'reward_gems': 60,
        'unlock_pirate': None,
    },
    {
        'id': 'play_180_min',
        'name': 'Sea Legend',
        'description': 'Play for 180 total minutes',
        'type': 'playtime',
        'target': 10800,
        'reward_gems': 40,
        'unlock_pirate': None,
    },
]


PIRATE_CLASS_NAMES = {
    'balanced': 'Balanced Captain',
    'berserker': 'Berserker Raider',
    'navigator': 'Storm Navigator',
    'engineer': 'Iron Engineer',
    'reaper': 'Reaper Corsair',
    'old_salt': 'Old Salt Veteran',
}


def get_talent_level(talent_id):
    """Gibt das aktuelle Level eines Talents zurück (0-3)"""
    profile = load_profile()
    talents = profile.get('talents', {})
    return talents.get(talent_id, 0)


def get_all_talent_bonuses():
    """Berechnet alle aktiven Talent-Boni"""
    profile = load_profile()
    talents = profile.get('talents', {})
    bonuses = {
        'extra_gems_per_run': 0,
        'gem_chance_bonus': 0,
        'damage_bonus': 0,
        'fire_rate_bonus': 0,
        'explosion_size_bonus': 0,
        'speed_bonus': 0,
        'show_enemies_minimap': False,
        'dodge_chance': 0,
        'max_hp_bonus': 0,
        'regen_bonus': 0,
        'damage_reduction': 0,
        'xp_bonus': 0,
        'double_xp_drops': False,
        'all_stats_bonus': 0,
        'double_gems': False,
    }

    # Schatzjäger
    lvl = talents.get('schatzjaeger', 0)
    if lvl >= 1:
        bonuses['extra_gems_per_run'] += 1
    if lvl >= 2:
        bonuses['extra_gems_per_run'] += 2
    if lvl >= 3:
        bonuses['extra_gems_per_run'] += 5
        bonuses['gem_chance_bonus'] += 0.25

    # Kanonier
    lvl = talents.get('kanonier', 0)
    if lvl >= 1:
        bonuses['damage_bonus'] += 0.10
    if lvl >= 2:
        bonuses['fire_rate_bonus'] += 0.15
    if lvl >= 3:
        bonuses['explosion_size_bonus'] += 0.50

    # Navigator
    lvl = talents.get('navigator', 0)
    if lvl >= 1:
        bonuses['speed_bonus'] += 0.10
    if lvl >= 2:
        bonuses['show_enemies_minimap'] = True
    if lvl >= 3:
        bonuses['speed_bonus'] += 0.20
        bonuses['dodge_chance'] += 0.15

    # Seebär
    lvl = talents.get('seebaer', 0)
    if lvl >= 1:
        bonuses['max_hp_bonus'] += 20
    if lvl >= 2:
        bonuses['regen_bonus'] += 2
    if lvl >= 3:
        bonuses['max_hp_bonus'] += 50
        bonuses['damage_reduction'] += 0.15

    # Piratenkapitän
    lvl = talents.get('piratenkapitaen', 0)
    if lvl >= 1:
        bonuses['xp_bonus'] += 0.20
    if lvl >= 2:
        bonuses['double_xp_drops'] = True
    if lvl >= 3:
        bonuses['all_stats_bonus'] += 0.10
        bonuses['double_gems'] = True

    return bonuses


# ==================== PARTIKEL FÜR PROFIL ====================
class ProfileParticle:
    """Funkelnde Partikel für den Hintergrund"""
    def __init__(self, w, h):
        self.pos = pg.Vector2(random.randint(0, w), random.randint(0, h))
        self.velocity = pg.Vector2(random.uniform(-15, 15), random.uniform(-30, -5))
        self.size = random.uniform(1.5, 4)
        self.alpha = random.randint(80, 200)
        self.lifetime = random.uniform(3, 8)
        self.max_lifetime = self.lifetime
        self.color = random.choice([
            (255, 220, 100), (200, 180, 255), (150, 220, 255), (255, 180, 150)
        ])
        self.w = w
        self.h = h
        self.twinkle_speed = random.uniform(2, 6)

    def update(self, dt):
        self.pos += self.velocity * dt
        self.lifetime -= dt
        if self.pos.y < -10 or self.lifetime <= 0:
            self.pos = pg.Vector2(random.randint(0, self.w), self.h + 10)
            self.lifetime = self.max_lifetime

    def draw(self, surface, timer):
        twinkle = abs(math.sin(timer * self.twinkle_speed + self.pos.x * 0.01))
        alpha = int(self.alpha * twinkle * min(1, self.lifetime / 1.0))
        if alpha > 10:
            size = max(1, int(self.size * (0.5 + twinkle * 0.5)))
            surf = pg.Surface((size * 2 + 2, size * 2 + 2), pg.SRCALPHA)
            pg.draw.circle(surf, (*self.color, alpha), (size + 1, size + 1), size)
            # Kleiner Glow
            if size > 2:
                pg.draw.circle(surf, (*self.color, alpha // 3), (size + 1, size + 1), size + 1)
            surface.blit(surf, (int(self.pos.x) - size - 1, int(self.pos.y) - size - 1))


# ==================== TALENT-ICON SYMBOLE ====================
TALENT_ICONS = {
    "schatzjaeger": "coin",      # Münze
    "kanonier": "cannon",        # Kanone
    "navigator": "compass",      # Kompass
    "seebaer": "shield",         # Schild
    "piratenkapitaen": "crown",  # Krone
}


def _draw_talent_icon(surface, icon_type, cx, cy, radius, color, timer: float = 0):
    """Zeichnet ein stilisiertes Talent-Icon"""
    r = radius
    if icon_type == "coin":
        # Münze mit Stern
        pg.draw.circle(surface, color, (cx, cy), r)
        pg.draw.circle(surface, (255, 255, 220), (cx, cy), r, 2)
        # Stern in der Mitte
        for i in range(5):
            angle = math.radians(i * 72 - 90 + math.sin(timer * 2) * 5)
            inner_angle = math.radians(i * 72 + 36 - 90 + math.sin(timer * 2) * 5)
            outer = (cx + int(math.cos(angle) * r * 0.6), cy + int(math.sin(angle) * r * 0.6))
            inner = (cx + int(math.cos(inner_angle) * r * 0.25), cy + int(math.sin(inner_angle) * r * 0.25))
            pg.draw.line(surface, (255, 255, 220), (cx, cy), outer, 2)
    elif icon_type == "cannon":
        # Kanone
        pg.draw.circle(surface, color, (cx, cy), r)
        pg.draw.circle(surface, (255, 200, 180), (cx, cy), r, 2)
        # Kanonrohr
        pg.draw.rect(surface, (255, 220, 200), (cx - 2, cy - r + 4, 4, r - 2))
        pg.draw.circle(surface, (255, 240, 200), (cx, cy + 2), r // 3)
    elif icon_type == "compass":
        # Kompass
        pg.draw.circle(surface, color, (cx, cy), r)
        pg.draw.circle(surface, (200, 230, 255), (cx, cy), r, 2)
        # Nadel (rotierend)
        angle = timer * 0.5
        dx = int(math.cos(angle) * r * 0.6)
        dy = int(math.sin(angle) * r * 0.6)
        pg.draw.line(surface, (255, 80, 80), (cx, cy), (cx + dx, cy + dy), 3)
        pg.draw.line(surface, (220, 230, 255), (cx, cy), (cx - dx, cy - dy), 2)
        pg.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
    elif icon_type == "shield":
        # Schild
        pg.draw.circle(surface, color, (cx, cy), r)
        pg.draw.circle(surface, (180, 255, 200), (cx, cy), r, 2)
        # Kreuz
        pg.draw.rect(surface, (255, 255, 255), (cx - 2, cy - r // 2, 4, r), border_radius=2)
        pg.draw.rect(surface, (255, 255, 255), (cx - r // 2, cy - 2, r, 4), border_radius=2)
    elif icon_type == "crown":
        # Krone
        pg.draw.circle(surface, color, (cx, cy), r)
        pg.draw.circle(surface, (230, 200, 255), (cx, cy), r, 2)
        # Krone-Form
        crown_pts = [
            (cx - r // 2, cy + 3),
            (cx - r // 2, cy - 3),
            (cx - r // 3, cy - r // 2),
            (cx, cy - 2),
            (cx + r // 3, cy - r // 2),
            (cx + r // 2, cy - 3),
            (cx + r // 2, cy + 3),
        ]
        pg.draw.polygon(surface, (255, 240, 200), crown_pts)
    else:
        pg.draw.circle(surface, color, (cx, cy), r)


# ==================== PROFIL STATE ====================
class ProfileState(State):
    def __init__(self):
        pg.font.init()
        self.font_title = pg.font.SysFont("Arial", 56, bold=True)
        self.font_subtitle = pg.font.SysFont("Arial", 28)
        self.font_medium = pg.font.SysFont("Arial", 22, bold=True)
        self.font_medium_plain = pg.font.SysFont("Arial", 21)
        self.font_small = pg.font.SysFont("Arial", 18)
        self.font_tiny = pg.font.SysFont("Arial", 14)
        self.font_big_num = pg.font.SysFont("Arial", 72, bold=True)
        self.font_level_label = pg.font.SysFont("Arial", 16, bold=True)

        self.timer = 0
        self.selected_path = 0
        self.tab = 0   # 0 = Overview, 1 = Talents, 2 = Achievements
        self.error_flash = 0
        self.buy_flash = {}
        self.wave_offset = 0
        self.particles = []
        self.tab_anim = 0.0     # Smooth tab switch animation
        self.hover_path = -1    # Mouse hover auf welchem path
        self.xp_bar_anim = 0.0  # Animierter XP-Balken
        self.level_pulse = 0.0  # Puls-Animation beim Level

    def on_enter(self, frm):
        self.sfx = get_sound_manager()
        self.timer = 0
        self.error_flash = 0
        self.buy_flash = {}
        self.xp_bar_anim = 0.0
        self.level_pulse = 0.0
        w, h = pg.display.get_window_size()
        self.particles = [ProfileParticle(w, h) for _ in range(40)]

    def update(self, events, dt):
        dt_s = dt / 1000.0
        self.timer += dt_s
        self.wave_offset += dt_s * 1.5
        self.xp_bar_anim = min(1.0, self.xp_bar_anim + dt_s * 2.0)
        self.level_pulse += dt_s

        # Partikel
        for p in self.particles:
            p.update(dt_s)

        # Flash-Timer
        for key in list(self.buy_flash.keys()):
            self.buy_flash[key] -= dt_s
            if self.buy_flash[key] <= 0:
                del self.buy_flash[key]
        if self.error_flash > 0:
            self.error_flash -= dt_s

        if hasattr(self, 'sfx'):
            self.sfx.ensure_music_playing()

        w, h = pg.display.get_window_size()
        self.hover_path = -1

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE or event.key == pg.K_BACKSPACE:
                    self.exit("menu")
                elif event.key == pg.K_TAB:
                    self.tab = (self.tab + 1) % 3
                    self.tab_anim = 0.0
                    if hasattr(self, 'sfx'):
                        self.sfx.play('menu_select')
                elif self.tab == 1:
                    self._handle_talent_input(event)
            elif event.type == pg.MOUSEMOTION:
                mx, my = event.pos
                self._handle_mouse_hover(mx, my, w, h)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos, w, h)

        # Smooth tab anim
        self.tab_anim = min(1.0, self.tab_anim + dt_s * 4.0)

    def _handle_talent_input(self, event):
        if event.key in (pg.K_UP, pg.K_w):
            self.selected_path = (self.selected_path - 1) % len(TALENT_PATHS)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key in (pg.K_DOWN, pg.K_s):
            self.selected_path = (self.selected_path + 1) % len(TALENT_PATHS)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key in (pg.K_RETURN, pg.K_SPACE):
            self._try_buy_talent()

    def _handle_mouse_hover(self, mx, my, w, h):
        # Tab hover
        tab_labels = ["Overview", "Talents", "Achievements"]
        tab_w = 170
        tab_start_x = w // 2 - (len(tab_labels) * tab_w) // 2
        for i in range(len(tab_labels)):
            rect = pg.Rect(tab_start_x + i * tab_w, 85, tab_w - 10, 42)
            if rect.collidepoint(mx, my):
                pass  # Visual hover handled in draw

        if self.tab == 1:
            panel_w = min(620, w - 40)
            panel_x = w // 2 - panel_w // 2
            start_y = 178
            item_h = 72
            for i in range(len(TALENT_PATHS)):
                item_y = start_y + i * (item_h + 8)
                rect = pg.Rect(panel_x, item_y, panel_w, item_h)
                if rect.collidepoint(mx, my):
                    if self.selected_path != i:
                        self.selected_path = i
                        if hasattr(self, 'sfx'):
                            self.sfx.play('menu_select')
                    self.hover_path = i
                    return

    def _handle_click(self, pos, w, h):
        mx, my = pos

        # Tab-Buttons
        tab_labels = ["Overview", "Talents", "Achievements"]
        tab_w = 170
        tab_start_x = w // 2 - (len(tab_labels) * tab_w) // 2
        for i in range(len(tab_labels)):
            rect = pg.Rect(tab_start_x + i * tab_w, 85, tab_w - 10, 42)
            if rect.collidepoint(mx, my):
                if self.tab != i:
                    self.tab = i
                    self.tab_anim = 0.0
                    if hasattr(self, 'sfx'):
                        self.sfx.play('menu_select')
                return

        if self.tab == 1:
            panel_w = min(620, w - 40)
            panel_x = w // 2 - panel_w // 2
            start_y = 178
            item_h = 72
            for i in range(len(TALENT_PATHS)):
                item_y = start_y + i * (item_h + 8)
                rect = pg.Rect(panel_x, item_y, panel_w, item_h)
                if rect.collidepoint(mx, my):
                    self.selected_path = i
                    self._try_buy_talent()
                    return

    def _try_buy_talent(self):
        profile = load_profile()
        path = TALENT_PATHS[self.selected_path]
        talents = profile.get('talents', {})
        current_level = talents.get(path['id'], 0)

        if current_level >= len(path['tiers']):
            return

        tier = path['tiers'][current_level]
        cost = tier['cost']
        tp = profile.get('talent_points', 0)

        if tp >= cost:
            talents[path['id']] = current_level + 1
            profile['talents'] = talents
            profile['talent_points'] = tp - cost
            save_profile(profile)
            self.buy_flash[path['id']] = 0.6
            if hasattr(self, 'sfx'):
                self.sfx.play('perk_buy')
        else:
            self.error_flash = 1.2
            if hasattr(self, 'sfx'):
                self.sfx.play('error')

    # ==================== ZEICHNEN ====================
    def draw(self, s):
        w, h = s.get_size()
        self._draw_background(s, w, h)

        # Partikel (hinter allem)
        for p in self.particles:
            p.draw(s, self.timer)

        # Animierter Titel
        self._draw_animated_title(s, w)

        # Tabs
        self._draw_tabs(s, w, h)

        # Content
        alpha = min(255, int(self.tab_anim * 255))
        if self.tab == 0:
            self._draw_overview(s, w, h, alpha)
        elif self.tab == 1:
            self._draw_talents(s, w, h, alpha)
        else:
            self._draw_achievements(s, w, h, alpha)

        # Steuerungshinweise
        self._draw_controls_hint(s, w, h)

    def _draw_animated_title(self, s, w):
        title = "PROFILE"
        title_x = w // 2
        title_y = 18
        for i, char in enumerate(title):
            offset_y = math.sin(self.timer * 3 + i * 0.6) * 4
            # Gold-Farbe mit Shimmer
            gold_r = 255
            gold_g = int(200 + math.sin(self.timer * 2.5 + i * 0.8) * 40)
            gold_b = int(50 + math.sin(self.timer * 3 + i) * 50)
            char_surf = self.font_title.render(char, True, (gold_r, gold_g, gold_b))
            char_x = title_x - len(title) * 22 + i * 44
            # Schatten
            shadow = self.font_title.render(char, True, (20, 15, 5))
            s.blit(shadow, (char_x + 3, title_y + offset_y + 3))
            s.blit(char_surf, (char_x, title_y + offset_y))

    def _draw_tabs(self, s, w, h):
        tab_labels = ["Overview", "Talents", "Achievements"]
        tab_w = 170
        tab_start_x = w // 2 - (len(tab_labels) * tab_w) // 2
        mouse_pos = pg.mouse.get_pos()

        for i, label in enumerate(tab_labels):
            rect = pg.Rect(tab_start_x + i * tab_w, 85, tab_w - 10, 42)
            is_active = self.tab == i
            is_hovered = rect.collidepoint(mouse_pos)

            tab_surf = pg.Surface((rect.w, rect.h), pg.SRCALPHA)

            if is_active:
                # Gradient-Hintergrund
                for y in range(rect.h):
                    t = y / rect.h
                    r = int(35 + 30 * (1 - t))
                    g = int(55 + 30 * (1 - t))
                    b = int(100 + 40 * (1 - t))
                    pg.draw.line(tab_surf, (r, g, b, 240), (0, y), (rect.w, y))
                # Goldener Unterstrich
                pg.draw.rect(tab_surf, (255, 210, 80), (4, rect.h - 3, rect.w - 8, 3), border_radius=2)
                pg.draw.rect(tab_surf, (255, 220, 100, 200), (0, 0, rect.w, rect.h), 2, border_radius=10)
            elif is_hovered:
                pg.draw.rect(tab_surf, (25, 40, 70, 200), (0, 0, rect.w, rect.h), border_radius=10)
                pg.draw.rect(tab_surf, (120, 140, 180, 150), (0, 0, rect.w, rect.h), 1, border_radius=10)
            else:
                pg.draw.rect(tab_surf, (15, 25, 45, 160), (0, 0, rect.w, rect.h), border_radius=10)
                pg.draw.rect(tab_surf, (60, 70, 100, 100), (0, 0, rect.w, rect.h), 1, border_radius=10)

            s.blit(tab_surf, rect.topleft)

            text_color = (255, 240, 180) if is_active else (180, 190, 210) if is_hovered else (130, 140, 160)
            text = self.font_small.render(label, True, text_color)
            s.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    def _draw_background(self, s, w, h):
        # Dunkler Ozean-Gradient
        for y in range(h):
            t = y / h
            r = int(5 + 20 * t)
            g = int(12 + 35 * t)
            b = int(40 + 70 * t)
            pg.draw.line(s, (r, g, b), (0, y), (w, y))

        # Wellen (mehrere Lagen, transluzent)
        wave_surf = pg.Surface((w, h), pg.SRCALPHA)
        for i in range(4):
            wave_y = h - 40 - i * 22 + math.sin(self.wave_offset * 0.8 + i * 0.7) * 12
            a = max(0, 60 - i * 15)
            wave_color = (30 + i * 12, 60 + i * 15, 130 + i * 12, a)
            points = []
            for x in range(0, w + 20, 15):
                y_off = math.sin((x + self.wave_offset * 40 + i * 80) / 60 + i * 1.2) * (8 + i * 3)
                points.append((x, wave_y + y_off))
            points.append((w, h))
            points.append((0, h))
            if len(points) >= 3:
                pg.draw.polygon(wave_surf, wave_color, points)
        s.blit(wave_surf, (0, 0))

        # Subtile Vignette
        vignette = pg.Surface((w, h), pg.SRCALPHA)
        for border_size in range(60):
            alpha = max(0, 40 - border_size)
            pg.draw.rect(vignette, (0, 0, 0, alpha), (border_size, border_size, w - 2 * border_size, h - 2 * border_size), 1)
        s.blit(vignette, (0, 0))

    def _draw_controls_hint(self, s, w, h):
        if self.tab == 1:
            hints = [
                ("TAB", "Switch"),
                ("W/S", "Select"),
                ("ENTER", "Buy"),
                ("ESC", "Back"),
            ]
        else:
            hints = [
                ("TAB", "Switch"),
                ("ESC", "Back"),
            ]
        total_w = 0
        rendered = []
        for key, desc in hints:
            key_surf = self.font_tiny.render(f" {key} ", True, (220, 220, 240))
            desc_surf = self.font_tiny.render(f" {desc}  ", True, (120, 135, 165))
            total_w += key_surf.get_width() + desc_surf.get_width() + 8
            rendered.append((key_surf, desc_surf))

        x = w // 2 - total_w // 2
        y = h - 28
        for key_surf, desc_surf in rendered:
            # Key-Badge
            kw = key_surf.get_width() + 4
            kh = key_surf.get_height() + 2
            badge = pg.Surface((kw, kh), pg.SRCALPHA)
            pg.draw.rect(badge, (40, 50, 80, 180), (0, 0, kw, kh), border_radius=4)
            pg.draw.rect(badge, (80, 100, 140, 120), (0, 0, kw, kh), 1, border_radius=4)
            s.blit(badge, (x, y - 1))
            s.blit(key_surf, (x + 2, y))
            x += kw + 2
            s.blit(desc_surf, (x, y))
            x += desc_surf.get_width() + 6

    # ==================== ÜBERSICHT ====================
    def _draw_overview(self, s, w, h, alpha):
        profile = load_profile()
        level = profile.get('profile_level', 1)
        xp = profile.get('profile_xp', 0)
        tp = profile.get('talent_points', 0)
        total_kills = profile.get('total_kills', 0)
        total_playtime = profile.get('total_playtime', 0)
        games_played = profile.get('games_played', 0)
        xp_needed = xp_for_level(level)

        # Hauptkarte
        panel_w = min(520, w - 60)
        panel_h = 360
        panel_x = w // 2 - panel_w // 2
        panel_y = 145

        # Panel mit Gradient-Hintergrund
        panel_surf = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        for y in range(panel_h):
            t = y / panel_h
            r = int(12 + 15 * t)
            g = int(20 + 20 * t)
            b = int(45 + 25 * t)
            a = 220
            pg.draw.line(panel_surf, (r, g, b, a), (0, y), (panel_w, y))
        pg.draw.rect(panel_surf, (70, 110, 170, 80), (0, 0, panel_w, panel_h), 2, border_radius=18)
        # Oberer Highlight
        highlight = pg.Surface((panel_w - 4, 2), pg.SRCALPHA)
        highlight.fill((255, 255, 255, 30))
        panel_surf.blit(highlight, (2, 2))
        s.blit(panel_surf, (panel_x, panel_y))

        # === Level-Badge (zentriert, kreisförmig) ===
        badge_cx = w // 2
        badge_cy = panel_y + 65
        badge_r = 45

        # Äußerer Glow
        pulse = abs(math.sin(self.level_pulse * 1.5)) * 0.3 + 0.7
        glow_r = int(badge_r + 15 * pulse)
        glow_surf = pg.Surface((glow_r * 2 + 10, glow_r * 2 + 10), pg.SRCALPHA)
        pg.draw.circle(glow_surf, (255, 200, 50, int(25 * pulse)), (glow_r + 5, glow_r + 5), glow_r)
        s.blit(glow_surf, (badge_cx - glow_r - 5, badge_cy - glow_r - 5))

        # Ring
        pg.draw.circle(s, (40, 55, 90), (badge_cx, badge_cy), badge_r)
        # XP-Fortschritt als Ring
        if xp_needed > 0:
            progress = min(1.0, xp / xp_needed) * self.xp_bar_anim
        else:
            progress = 1.0
        if progress > 0:
            start_angle = math.pi / 2
            end_angle = start_angle - progress * 2 * math.pi
            # Gezeichnet als Bogensegmente
            steps = max(3, int(progress * 60))
            for step in range(steps):
                t = step / max(1, steps - 1)
                a = start_angle - t * progress * 2 * math.pi
                x1 = badge_cx + int(math.cos(a) * (badge_r - 2))
                y1 = badge_cy - int(math.sin(a) * (badge_r - 2))
                x2 = badge_cx + int(math.cos(a) * badge_r)
                y2 = badge_cy - int(math.sin(a) * badge_r)
                color_t = t
                gold = (
                    int(255 * (1 - color_t * 0.2)),
                    int(200 + 30 * color_t),
                    int(50 + 80 * color_t),
                )
                pg.draw.line(s, gold, (x1, y1), (x2, y2), 4)

        pg.draw.circle(s, (80, 120, 180, 120), (badge_cx, badge_cy), badge_r, 2)

        # Level-Zahl
        level_text = str(level)
        level_surf = self.font_big_num.render(level_text, True, (255, 225, 100))
        shadow = self.font_big_num.render(level_text, True, (15, 10, 0))
        lx = badge_cx - level_surf.get_width() // 2
        ly = badge_cy - level_surf.get_height() // 2 - 2
        s.blit(shadow, (lx + 2, ly + 2))
        s.blit(level_surf, (lx, ly))

        # Label unter dem Badge
        label_surf = self.font_level_label.render("PIRATE LEVEL", True, (180, 195, 220))
        s.blit(label_surf, (badge_cx - label_surf.get_width() // 2, badge_cy + badge_r + 8))

        # === XP-Balken ===
        bar_w = panel_w - 80
        bar_h = 18
        bar_x = panel_x + 40
        bar_y = badge_cy + badge_r + 35

        # Hintergrund
        bar_bg = pg.Surface((bar_w, bar_h), pg.SRCALPHA)
        pg.draw.rect(bar_bg, (20, 30, 50, 200), (0, 0, bar_w, bar_h), border_radius=9)
        s.blit(bar_bg, (bar_x, bar_y))

        # Füllung (animiert)
        if xp_needed > 0:
            fill_ratio = min(1.0, xp / xp_needed) * self.xp_bar_anim
        else:
            fill_ratio = 1.0
        fill_w = max(0, int(bar_w * fill_ratio))
        if fill_w > 4:
            fill_surf = pg.Surface((fill_w, bar_h), pg.SRCALPHA)
            for fy in range(bar_h):
                t = fy / bar_h
                fr = int(255 * (1 - t * 0.3))
                fg = int(200 + 30 * (1 - t))
                fb = int(50 + 100 * t)
                pg.draw.line(fill_surf, (fr, fg, fb, 245), (0, fy), (fill_w, fy))
            # Glanz-Effekt oben
            shine = pg.Surface((fill_w, bar_h // 3), pg.SRCALPHA)
            shine.fill((255, 255, 255, 50))
            fill_surf.blit(shine, (0, 1))
            # Rundung via Clipping: einfach abgerundeten Balken zeichnen
            s.blit(fill_surf, (bar_x, bar_y))
            # Glow am Ende des Balkens
            if fill_w > 6:
                end_glow = pg.Surface((12, bar_h + 8), pg.SRCALPHA)
                pg.draw.ellipse(end_glow, (255, 240, 150, 80), (0, 0, 12, bar_h + 8))
                s.blit(end_glow, (bar_x + fill_w - 6, bar_y - 4))

        pg.draw.rect(s, (70, 100, 150, 150), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=9)

        # XP-Text
        xp_text = f"{xp} / {xp_needed} XP"
        xp_surf = self.font_tiny.render(xp_text, True, (200, 210, 230))
        s.blit(xp_surf, (bar_x + bar_w // 2 - xp_surf.get_width() // 2, bar_y + bar_h + 4))

        # === Talent-Punkte ===
        tp_y = bar_y + bar_h + 28
        if tp > 0:
            tp_pulse = abs(math.sin(self.timer * 3)) * 0.3 + 0.7
            tp_glow = pg.Surface((200, 30), pg.SRCALPHA)
            pg.draw.rect(tp_glow, (50, 255, 150, int(30 * tp_pulse)), (0, 0, 200, 30), border_radius=8)
            s.blit(tp_glow, (w // 2 - 100, tp_y - 3))

        tp_icon = "★" if tp > 0 else "☆"
        tp_text = f" {tp} Talent Points available"
        tp_color = (80, 255, 170) if tp > 0 else (100, 110, 130)
        tp_surf = self.font_medium.render(tp_text, True, tp_color)
        s.blit(tp_surf, (w // 2 - tp_surf.get_width() // 2, tp_y))

        # === Statistiken (als schicke Karten) ===
        stat_y = tp_y + 42
        stats = [
            ("Games", str(games_played), (100, 160, 255), "⚓"),
            ("Kills", str(total_kills), (255, 90, 80), "☠"),
            ("Playtime", f"{int(total_playtime // 60)}m {int(total_playtime % 60)}s", (80, 200, 255), "⏱"),
        ]

        card_w = (panel_w - 60) // 3
        card_h = 60
        card_x_start = panel_x + 30

        for i, (label, value, color, icon) in enumerate(stats):
            cx = card_x_start + i * (card_w + 10)
            cy = stat_y

            # Karte
            card = pg.Surface((card_w, card_h), pg.SRCALPHA)
            pg.draw.rect(card, (20, 30, 55, 190), (0, 0, card_w, card_h), border_radius=10)
            pg.draw.rect(card, (*color, 60), (0, 0, card_w, card_h), 1, border_radius=10)
            # Farbiger Akzent oben
            accent = pg.Surface((card_w - 8, 2), pg.SRCALPHA)
            accent.fill((*color, 100))
            card.blit(accent, (4, 3))
            s.blit(card, (cx, cy))

            # Wert (groß)
            val_surf = self.font_medium.render(value, True, color)
            s.blit(val_surf, (cx + card_w // 2 - val_surf.get_width() // 2, cy + 8))
            # Label (klein)
            lbl_surf = self.font_tiny.render(label, True, (140, 150, 175))
            s.blit(lbl_surf, (cx + card_w // 2 - lbl_surf.get_width() // 2, cy + 35))

    # ==================== TALENTE ====================
    def _draw_talents(self, s, w, h, alpha):
        profile = load_profile()
        talents = profile.get('talents', {})
        tp = profile.get('talent_points', 0)

        # Talent-Punkte Header
        if tp > 0:
            tp_pulse = abs(math.sin(self.timer * 3)) * 0.3 + 0.7
            tp_bg = pg.Surface((280, 32), pg.SRCALPHA)
            pg.draw.rect(tp_bg, (40, 80, 60, int(120 * tp_pulse)), (0, 0, 280, 32), border_radius=8)
            s.blit(tp_bg, (w // 2 - 140, 138))
        tp_text = f"★ {tp} Talent Points"
        tp_color = (80, 255, 170) if tp > 0 else (100, 110, 130)
        tp_surf = self.font_medium.render(tp_text, True, tp_color)
        s.blit(tp_surf, (w // 2 - tp_surf.get_width() // 2, 142))

        panel_w = min(620, w - 40)
        panel_x = w // 2 - panel_w // 2
        start_y = 178
        item_h = 72

        mouse_pos = pg.mouse.get_pos()

        for i, path in enumerate(TALENT_PATHS):
            is_selected = i == self.selected_path
            current_level = talents.get(path['id'], 0)
            is_maxed = current_level >= len(path['tiers'])
            icon_type = TALENT_ICONS.get(path['id'], 'coin')
            icon_color = path['icon_color']

            item_y = start_y + i * (item_h + 8)
            item_rect = pg.Rect(panel_x, item_y, panel_w, item_h)
            is_hovered = item_rect.collidepoint(mouse_pos)

            # === Box Hintergrund ===
            box_surf = pg.Surface((panel_w, item_h), pg.SRCALPHA)

            # Kauf-Flash (grünes Leuchten)
            if path['id'] in self.buy_flash:
                flash_t = self.buy_flash[path['id']] / 0.6
                flash_alpha = int(120 * flash_t)
                pg.draw.rect(box_surf, (80, 255, 120, flash_alpha), (0, 0, panel_w, item_h), border_radius=12)

            if is_selected:
                # Gradient-Hintergrund für ausgewählt
                for y in range(item_h):
                    t = y / item_h
                    r = int(25 + 20 * (1 - t))
                    g = int(35 + 25 * (1 - t))
                    b = int(70 + 30 * (1 - t))
                    pg.draw.line(box_surf, (r, g, b, 235), (0, y), (panel_w, y))
                # Runde Ecken maskieren
                mask = pg.Surface((panel_w, item_h), pg.SRCALPHA)
                pg.draw.rect(mask, (255, 255, 255, 255), (0, 0, panel_w, item_h), border_radius=12)

                border_color = (255, 215, 80) if not is_maxed else (80, 255, 130)
                pg.draw.rect(box_surf, border_color, (0, 0, panel_w, item_h), 2, border_radius=12)

                # Farbiger Akzent links
                accent = pg.Surface((4, item_h - 12), pg.SRCALPHA)
                accent.fill((*icon_color, 200))
                box_surf.blit(accent, (4, 6))
            elif is_hovered:
                pg.draw.rect(box_surf, (22, 32, 58, 220), (0, 0, panel_w, item_h), border_radius=12)
                pg.draw.rect(box_surf, (90, 110, 150, 120), (0, 0, panel_w, item_h), 1, border_radius=12)
            else:
                pg.draw.rect(box_surf, (14, 22, 45, 200), (0, 0, panel_w, item_h), border_radius=12)
                pg.draw.rect(box_surf, (50, 60, 90, 100), (0, 0, panel_w, item_h), 1, border_radius=12)

            s.blit(box_surf, (panel_x, item_y))

            # === Icon ===
            icon_cx = panel_x + 38
            icon_cy = item_y + item_h // 2
            icon_r = 22

            # Glow für ausgewählt
            if is_selected or is_hovered:
                glow = pg.Surface((icon_r * 3, icon_r * 3), pg.SRCALPHA)
                glow_alpha = 50 if is_selected else 30
                pg.draw.circle(glow, (*icon_color, glow_alpha), (icon_r * 3 // 2, icon_r * 3 // 2), icon_r * 3 // 2)
                s.blit(glow, (icon_cx - icon_r * 3 // 2, icon_cy - icon_r * 3 // 2))

            _draw_talent_icon(s, icon_type, icon_cx, icon_cy, icon_r, icon_color, self.timer)

            # Level-Badge (kleiner Kreis rechts unten am Icon)
            badge_x = icon_cx + icon_r - 4
            badge_y = icon_cy + icon_r - 4
            badge_color = (80, 255, 130) if current_level > 0 else (60, 70, 90)
            pg.draw.circle(s, badge_color, (badge_x, badge_y), 9)
            pg.draw.circle(s, (255, 255, 255), (badge_x, badge_y), 9, 1)
            lvl_surf = self.font_tiny.render(str(current_level), True, (255, 255, 255))
            s.blit(lvl_surf, (badge_x - lvl_surf.get_width() // 2, badge_y - lvl_surf.get_height() // 2))

            # === Pfad-Name ===
            name_color = (255, 255, 255) if not is_maxed else (80, 255, 130)
            name_surf = self.font_medium.render(path['name'], True, name_color)
            s.blit(name_surf, (panel_x + 70, item_y + 10))

            # === Beschreibung ===
            if is_maxed:
                desc_text = "✦ All talents unlocked!"
                desc_color = (80, 255, 130)
            else:
                tier = path['tiers'][current_level]
                desc_text = f"{tier['name']} — {tier['desc']}"
                desc_color = (160, 175, 210)
            desc_surf = self.font_small.render(desc_text, True, desc_color)
            s.blit(desc_surf, (panel_x + 70, item_y + 38))

            # === Tier-Pips (verbundene Punkte rechts) ===
            pip_start_x = panel_x + panel_w - 145
            pip_y_center = item_y + 16
            num_tiers = len(path['tiers'])

            # Verbindungslinien
            for t in range(num_tiers - 1):
                px1 = pip_start_x + t * 34 + 12
                px2 = pip_start_x + (t + 1) * 34
                line_color = icon_color if t < current_level - 1 else (50, 60, 80)
                pg.draw.line(s, line_color, (px1, pip_y_center), (px2, pip_y_center), 2)

            # Punkte
            for t in range(num_tiers):
                px = pip_start_x + t * 34
                py = pip_y_center
                pip_r = 8
                if t < current_level:
                    # Gefüllt mit Glow
                    glow = pg.Surface((pip_r * 3, pip_r * 3), pg.SRCALPHA)
                    pg.draw.circle(glow, (*icon_color, 40), (pip_r * 3 // 2, pip_r * 3 // 2), pip_r * 3 // 2)
                    s.blit(glow, (px + 6 - pip_r * 3 // 2, py - pip_r * 3 // 2))
                    pg.draw.circle(s, icon_color, (px + 6, py), pip_r)
                    pg.draw.circle(s, (255, 255, 255), (px + 6, py), pip_r, 2)
                    # Häkchen
                    pg.draw.line(s, (255, 255, 255), (px + 2, py), (px + 5, py + 3), 2)
                    pg.draw.line(s, (255, 255, 255), (px + 5, py + 3), (px + 10, py - 3), 2)
                elif t == current_level and not is_maxed:
                    # Nächster Stufe (pulsierend wenn ausgewählt)
                    if is_selected:
                        pulse = abs(math.sin(self.timer * 4)) * 0.4 + 0.6
                        ring_color = tuple(int(c * pulse) for c in icon_color)
                    else:
                        ring_color = (80, 90, 120)
                    pg.draw.circle(s, (30, 40, 60), (px + 6, py), pip_r)
                    pg.draw.circle(s, ring_color, (px + 6, py), pip_r, 2)
                else:
                    # Gesperrt
                    pg.draw.circle(s, (25, 30, 45), (px + 6, py), pip_r)
                    pg.draw.circle(s, (50, 55, 70), (px + 6, py), pip_r, 1)

            # === Kosten / MAX ===
            if is_maxed:
                max_surf = self.font_small.render("MAX", True, (80, 255, 130))
                max_bg = pg.Surface((max_surf.get_width() + 14, max_surf.get_height() + 6), pg.SRCALPHA)
                pg.draw.rect(max_bg, (30, 80, 50, 150), (0, 0, max_bg.get_width(), max_bg.get_height()), border_radius=6)
                s.blit(max_bg, (panel_x + panel_w - 60, item_y + 44))
                s.blit(max_surf, (panel_x + panel_w - 53, item_y + 47))
            else:
                cost = path['tiers'][current_level]['cost']
                can_afford = tp >= cost
                cost_color = (80, 255, 170) if can_afford else (220, 70, 70)
                cost_bg_color = (30, 70, 50, 160) if can_afford else (70, 30, 30, 160)
                cost_text = f"★ {cost}"
                cost_surf = self.font_small.render(cost_text, True, cost_color)
                cost_bg = pg.Surface((cost_surf.get_width() + 14, cost_surf.get_height() + 6), pg.SRCALPHA)
                pg.draw.rect(cost_bg, cost_bg_color, (0, 0, cost_bg.get_width(), cost_bg.get_height()), border_radius=6)
                pg.draw.rect(cost_bg, (*cost_color, 80), (0, 0, cost_bg.get_width(), cost_bg.get_height()), 1, border_radius=6)
                s.blit(cost_bg, (panel_x + panel_w - 65, item_y + 44))
                s.blit(cost_surf, (panel_x + panel_w - 58, item_y + 47))

        # === Error Flash ===
        if self.error_flash > 0:
            progress = min(1.0, self.error_flash / 1.2)
            shake_x = int(math.sin(self.timer * 30) * 3 * progress)
            alpha_val = min(255, int(progress * 255))

            err_text = "Not enough Talent Points!"
            err_surf = self.font_medium.render(err_text, True, (255, 80, 80))
            err_w = err_surf.get_width() + 36
            err_h = err_surf.get_height() + 14
            err_bg = pg.Surface((err_w, err_h), pg.SRCALPHA)
            pg.draw.rect(err_bg, (100, 20, 20, min(210, alpha_val)), (0, 0, err_w, err_h), border_radius=10)
            pg.draw.rect(err_bg, (255, 80, 80, min(150, alpha_val)), (0, 0, err_w, err_h), 2, border_radius=10)
            ex = w // 2 - err_w // 2 + shake_x
            ey = h - 75
            s.blit(err_bg, (ex, ey))
            err_surf.set_alpha(alpha_val)
            s.blit(err_surf, (ex + 18, ey + 7))

    # ==================== ACHIEVEMENTS ====================
    def _draw_achievements(self, s, w, h, alpha):
        achievement_state = load_achievement_state()
        unlocked_ids = set(achievement_state.get('unlocked', []))
        unlocked_pirates = load_unlocked_pirates()

        total_kills = int(achievement_state.get('total_kills', 0))
        total_playtime_seconds = float(achievement_state.get('total_playtime_seconds', 0.0))
        total_playtime_minutes = int(total_playtime_seconds // 60)

        panel_w = min(780, w - 50)
        panel_x = w // 2 - panel_w // 2
        row_h = 92
        row_gap = 10
        start_y = 150

        for i, ach in enumerate(ACHIEVEMENTS):
            row_y = start_y + i * (row_h + row_gap)
            row_rect = pg.Rect(panel_x, row_y, panel_w, row_h)

            # Card background
            row_surf = pg.Surface((row_rect.w, row_rect.h), pg.SRCALPHA)
            unlocked = ach['id'] in unlocked_ids

            if unlocked:
                pg.draw.rect(row_surf, (24, 52, 42, 220), (0, 0, row_rect.w, row_rect.h), border_radius=12)
                pg.draw.rect(row_surf, (90, 210, 145, 110), (0, 0, row_rect.w, row_rect.h), 2, border_radius=12)
            else:
                pg.draw.rect(row_surf, (16, 25, 45, 215), (0, 0, row_rect.w, row_rect.h), border_radius=12)
                pg.draw.rect(row_surf, (70, 90, 130, 110), (0, 0, row_rect.w, row_rect.h), 1, border_radius=12)

            s.blit(row_surf, row_rect.topleft)

            # Progress values
            if ach['type'] == 'kills':
                current = total_kills
                progress_text = f"{current} / {ach['target']} kills"
            else:
                current = total_playtime_seconds
                cur_m = int(total_playtime_seconds // 60)
                tgt_m = int(ach['target'] // 60)
                progress_text = f"{cur_m} / {tgt_m} minutes"

            ratio = min(1.0, float(current) / float(max(1, ach['target'])))

            # Title and description
            title_color = (200, 255, 220) if unlocked else (220, 230, 250)
            title = self.font_medium.render(ach['name'], True, title_color)
            desc = self.font_small.render(ach['description'], True, (150, 170, 205))
            s.blit(title, (panel_x + 16, row_y + 10))
            s.blit(desc, (panel_x + 16, row_y + 38))

            # Progress bar
            bar_w = 280
            bar_h = 14
            bar_x = panel_x + panel_w - bar_w - 180
            bar_y = row_y + 20
            pg.draw.rect(s, (20, 28, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=7)
            fill_w = int(bar_w * ratio)
            if fill_w > 0:
                fill_color = (90, 230, 160) if unlocked else (95, 165, 255)
                pg.draw.rect(s, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=7)
            pg.draw.rect(s, (75, 95, 130), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=7)

            prog_surf = self.font_tiny.render(progress_text, True, (190, 205, 230))
            s.blit(prog_surf, (bar_x, bar_y + 18))

            # Reward text
            reward_text = f"Reward: +{ach['reward_gems']} gems"
            reward_surf = self.font_tiny.render(reward_text, True, (255, 210, 110))
            s.blit(reward_surf, (bar_x, bar_y + 36))

            if ach.get('unlock_pirate'):
                pirate_id = ach['unlock_pirate']
                pirate_name = PIRATE_CLASS_NAMES.get(pirate_id, pirate_id.title())
                if pirate_id in unlocked_pirates:
                    unlock_text = f"Class: {pirate_name} unlocked"
                    unlock_color = (110, 240, 160)
                else:
                    unlock_text = f"Unlocks class: {pirate_name}"
                    unlock_color = (160, 180, 210)
                unlock_surf = self.font_tiny.render(unlock_text, True, unlock_color)
                s.blit(unlock_surf, (bar_x, bar_y + 52))

            # Status badge
            badge_text = "UNLOCKED" if unlocked else "LOCKED"
            badge_color = (80, 230, 150) if unlocked else (150, 160, 185)
            badge = self.font_small.render(badge_text, True, badge_color)
            s.blit(badge, (panel_x + panel_w - badge.get_width() - 16, row_y + row_h - badge.get_height() - 10))

        # Footer summary
        summary_text = f"Total Achievement Progress: {len(unlocked_ids)} / {len(ACHIEVEMENTS)}   |   Total tracked playtime: {total_playtime_minutes} minutes"
        summary_surf = self.font_tiny.render(summary_text, True, (150, 170, 205))
        s.blit(summary_surf, (w // 2 - summary_surf.get_width() // 2, h - 54))

