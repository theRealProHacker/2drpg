import pygame as pg
import math
import random
import os
import json
from datetime import date
from StateManager import State
from sounds import get_sound_manager

# Gem-Datei für Anzeige im Menü
GEM_SAVE_FILE = "gems_save.json"

# ==================== PERK-DEFINITIONEN ====================
PERKS = [
    {
        "id": "hull",
        "name": "Verstärkter Rumpf",
        "description": "+20 Max HP pro Level",
        "icon_color": (200, 50, 50),
        "max_level": 5,
        "cost_per_level": [5, 12, 22, 35, 55],
    },
    {
        "id": "cannons",
        "name": "Bessere Kanonen",
        "description": "+10 Schaden pro Level",
        "icon_color": (255, 150, 50),
        "max_level": 5,
        "cost_per_level": [5, 12, 22, 35, 55],
    },
    {
        "id": "sails",
        "name": "Schnellere Segel",
        "description": "+10% Geschwindigkeit pro Level",
        "icon_color": (50, 200, 100),
        "max_level": 5,
        "cost_per_level": [5, 10, 18, 28, 45],
    },
    {
        "id": "repair",
        "name": "Auto-Reparatur",
        "description": "+1 HP/s Regeneration pro Level",
        "icon_color": (50, 150, 255),
        "max_level": 5,
        "cost_per_level": [8, 15, 25, 40, 65],
    },
    {
        "id": "reload",
        "name": "Schnelles Nachladen",
        "description": "-10% Schuss-Cooldown pro Level",
        "icon_color": (200, 200, 50),
        "max_level": 5,
        "cost_per_level": [6, 14, 24, 38, 55],
    },
    {
        "id": "xp_boost",
        "name": "XP-Boost",
        "description": "+15% mehr XP pro Level",
        "icon_color": (180, 100, 255),
        "max_level": 5,
        "cost_per_level": [6, 14, 24, 38, 55],
    },
]


def load_gems():
    """Lädt die Gem-Anzahl aus der Datei"""
    if os.path.exists(GEM_SAVE_FILE):
        try:
            with open(GEM_SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('gems', 0)
        except:
            return 0
    return 0


def save_gems(gems):
    """Speichert die Gem-Anzahl in die Datei"""
    data = load_full_save()
    data['gems'] = gems
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_full_save():
    """Lädt die komplette Save-Datei"""
    if os.path.exists(GEM_SAVE_FILE):
        try:
            with open(GEM_SAVE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'gems': 0, 'perks': {}}
    return {'gems': 0, 'perks': {}}


def load_perks():
    """Lädt die Perk-Level aus der Datei"""
    data = load_full_save()
    return data.get('perks', {})


def save_perks(perks):
    """Speichert die Perk-Level in die Datei"""
    data = load_full_save()
    data['perks'] = perks
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_last_spin():
    """Lädt das Datum des letzten Glücksrad-Spins"""
    data = load_full_save()
    return data.get('last_spin', None)


def save_last_spin(date_str):
    """Speichert das Datum des letzten Spins"""
    data = load_full_save()
    data['last_spin'] = date_str
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_streak_data():
    """Lädt Login-Streak Daten"""
    data = load_full_save()
    return {
        'streak_count': data.get('streak_count', 0),
        'last_login': data.get('last_login', None),
        'free_spins': data.get('free_spins', 0),
        'xp_booster_minutes': data.get('xp_booster_minutes', 0),
    }


def save_streak_data(streak_count, last_login, free_spins=None, xp_booster_minutes=None):
    """Speichert Login-Streak Daten"""
    data = load_full_save()
    data['streak_count'] = streak_count
    data['last_login'] = last_login
    if free_spins is not None:
        data['free_spins'] = free_spins
    if xp_booster_minutes is not None:
        data['xp_booster_minutes'] = xp_booster_minutes
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_free_spins():
    """Lädt die Anzahl freier Spins"""
    data = load_full_save()
    return data.get('free_spins', 0)


def save_free_spins(count):
    """Speichert die Anzahl freier Spins"""
    data = load_full_save()
    data['free_spins'] = count
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_xp_booster():
    """Lädt verbleibende XP-Booster Minuten"""
    data = load_full_save()
    return data.get('xp_booster_minutes', 0)


def save_xp_booster(minutes):
    """Speichert XP-Booster Minuten"""
    data = load_full_save()
    data['xp_booster_minutes'] = minutes
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


# ==================== EINSTELLUNGEN ====================
DEFAULT_SETTINGS = {
    'music_volume': 80,
    'sfx_volume': 80,
}

def load_settings():
    """Lädt die Einstellungen aus der Save-Datei"""
    data = load_full_save()
    settings = data.get('settings', {})
    result = dict(DEFAULT_SETTINGS)
    result.update(settings)
    return result

def save_settings(settings):
    """Speichert die Einstellungen"""
    data = load_full_save()
    data['settings'] = settings
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


# ==================== LOGIN-STREAK BELOHNUNGEN ====================
# 7-Tage-Zyklus, wiederholt sich
STREAK_REWARDS = [
    {"day": 1, "type": "gems", "amount": 1, "label": "1 Gem", "icon_color": (255, 220, 50)},
    {"day": 2, "type": "xp_booster", "amount": 15, "label": "XP Boost 15min", "icon_color": (180, 100, 255)},
    {"day": 3, "type": "gems", "amount": 2, "label": "2 Gems", "icon_color": (255, 220, 50)},
    {"day": 4, "type": "xp_booster", "amount": 15, "label": "XP Boost 15min", "icon_color": (180, 100, 255)},
    {"day": 5, "type": "gems", "amount": 3, "label": "3 Gems", "icon_color": (255, 220, 50)},
    {"day": 6, "type": "xp_booster", "amount": 15, "label": "XP Boost 15min", "icon_color": (180, 100, 255)},
    {"day": 7, "type": "free_spins", "amount": 5, "label": "5 Free Spins!", "icon_color": (50, 255, 150)},
]


# ==================== GLÜCKSRAD SEGMENTE ====================
WHEEL_SEGMENTS = [
    {"label": "1", "gems": 1, "color": (60, 130, 200), "weight": 25},
    {"label": "3", "gems": 3, "color": (50, 180, 80), "weight": 18},
    {"label": "1", "gems": 1, "color": (100, 80, 180), "weight": 25},
    {"label": "5", "gems": 5, "color": (220, 160, 40), "weight": 12},
    {"label": "2", "gems": 2, "color": (180, 60, 60), "weight": 20},
    {"label": "3", "gems": 3, "color": (60, 160, 160), "weight": 18},
    {"label": "2", "gems": 2, "color": (200, 100, 50), "weight": 20},
    {"label": "10", "gems": 10, "color": (255, 50, 200), "weight": 5},
    {"label": "1", "gems": 1, "color": (80, 100, 60), "weight": 25},
    {"label": "5", "gems": 5, "color": (180, 180, 50), "weight": 12},
    {"label": "2", "gems": 2, "color": (50, 80, 150), "weight": 20},
    {"label": "20", "gems": 20, "color": (255, 215, 0), "weight": 2},
]


class MenuParticle:
    """Partikel für den Hintergrund"""
    def __init__(self, w, h):
        self.pos = pg.Vector2(random.randint(0, w), random.randint(0, h))
        self.velocity = pg.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
        self.size = random.randint(2, 5)
        self.alpha = random.randint(50, 150)
        self.w = w
        self.h = h
    
    def update(self, dt):
        self.pos += self.velocity * dt
        # Wrap around
        if self.pos.x < 0: self.pos.x = self.w
        if self.pos.x > self.w: self.pos.x = 0
        if self.pos.y < 0: self.pos.y = self.h
        if self.pos.y > self.h: self.pos.y = 0
    
    def draw(self, surface):
        surf = pg.Surface((self.size * 2, self.size * 2), pg.SRCALPHA)
        pg.draw.circle(surf, (255, 255, 255, self.alpha), (self.size, self.size), self.size)
        surface.blit(surf, (int(self.pos.x), int(self.pos.y)))


class MenuState(State):
    def __init__(self):
        self.timer = 0
        self.selected = 0  # 0 = Start, 1 = Perks, 2 = Quit
        self.particles = []
        self.title_wave = 0
        
        # SoundManager sofort initialisieren (on_enter wird beim ersten Start nicht aufgerufen)
        self.sfx = get_sound_manager()
        
        # Fonts
        pg.font.init()
        self.font_title = pg.font.SysFont("Arial", 72, bold=True)
        self.font_subtitle = pg.font.SysFont("Arial", 28)
        self.font_menu = pg.font.SysFont("Arial", 36)
        self.font_small = pg.font.SysFont("Arial", 20)
        self.font_perk = pg.font.SysFont("Arial", 22, bold=True)
        self.font_perk_desc = pg.font.SysFont("Arial", 18)
        
        # Menu items
        self.menu_items = ["Spiel Starten", "Perks", "Einstellungen", "Beenden"]
        
        # Perk-Shop State
        self.in_perk_shop = False
        
        # Glücksrad State
        self.in_wheel = False
        self.wheel_angle = 0  # Aktuelle Drehung in Grad
        self.wheel_spinning = False
        self.wheel_speed = 0  # Grad pro Sekunde
        self.wheel_result = None  # Ergebnis nach Spin
        self.wheel_result_timer = 0  # Timer für Ergebnis-Anzeige
        self.wheel_claimed = False  # Ob Belohnung eingesammelt wurde
        self.wheel_can_spin = True  # Ob heute schon gesponnen wurde
        self.wheel_flash_timer = 0  # Flash-Effekt beim Gewinn
        self.wheel_free_spins = 0  # Freie Spins aus Streak
        
        # Login-Streak State
        self.show_streak_popup = False
        self.streak_popup_timer = 0
        self.streak_reward_claimed = None  # Das aktuelle Reward-Dict
        self.streak_count = 0
        self.streak_popup_anim = 0  # Animation-Timer
        self.streak_already_claimed = False  # Ob Reward heute schon abgeholt wurde
        
        # Einstellungen State
        self.in_settings = False
        self.settings_selected = 0  # 0 = Musik, 1 = Sound
        self.settings_data = load_settings()
        self.settings_dragging = None  # Welcher Slider gerade gezogen wird
        
        self.perk_selected = 0
        self.perk_buy_flash = {}  # perk_id -> timer für Kauf-Animation
        self.perk_error_flash = 0  # Timer für "nicht genug Gems" Feedback
        
        # Wellen für Hintergrund
        self.wave_offset = 0
        
        # Schiff-Animation
        self.ship_x = -100
        self.ship_y = 0
        
        # Last known screen size
        self.last_w = 960
        self.last_h = 540
    
    def on_init(self):
        """Wird beim allerersten Start aufgerufen (StateManager.start)"""
        # Einstellungen anwenden und Musik starten
        self.settings_data = load_settings()
        self.sfx.set_music_volume(self.settings_data['music_volume'] / 100.0)
        self.sfx.set_sfx_volume(self.settings_data['sfx_volume'] / 100.0)
        self.sfx.start_menu_music()
        self.particles = [MenuParticle(self.last_w, self.last_h) for _ in range(50)]
        self._check_login_streak()
    
    def on_enter(self, frm):
        """Wird aufgerufen wenn man ins Menü kommt (nach dem ersten Mal)"""
        self.timer = 0
        self.selected = 0
        self.sfx = get_sound_manager()
        # Einstellungen anwenden
        self.settings_data = load_settings()
        self.sfx.set_music_volume(self.settings_data['music_volume'] / 100.0)
        self.sfx.set_sfx_volume(self.settings_data['sfx_volume'] / 100.0)
        self.sfx.start_menu_music()
        # Partikel neu erstellen
        self.particles = [MenuParticle(self.last_w, self.last_h) for _ in range(50)]
        # Login-Streak prüfen
        self._check_login_streak()
    
    def update(self, events, dt):
        dt_seconds = dt / 1000.0
        self.timer += dt_seconds
        self.wave_offset += dt_seconds * 2
        self.title_wave += dt_seconds * 3
        
        # Schiff-Animation
        self.ship_x += 30 * dt_seconds
        if self.ship_x > self.last_w + 200:
            self.ship_x = -200
            self.ship_y = random.randint(100, self.last_h - 200)
        
        # Partikel aktualisieren
        for p in self.particles:
            p.update(dt_seconds)
        
        # Kauf-Flash Timer aktualisieren
        for perk_id in list(self.perk_buy_flash.keys()):
            self.perk_buy_flash[perk_id] -= dt_seconds
            if self.perk_buy_flash[perk_id] <= 0:
                del self.perk_buy_flash[perk_id]
        if self.perk_error_flash > 0:
            self.perk_error_flash -= dt_seconds
        
        # Streak-Popup Timer
        if self.show_streak_popup:
            self.streak_popup_timer += dt_seconds
            self.streak_popup_anim += dt_seconds
        
        # Musik am Laufen halten (falls Kanal unerwartet stoppt)
        if hasattr(self, 'sfx'):
            self.sfx.ensure_music_playing()
        
        # Glücksrad Update
        if self.wheel_spinning:
            self.wheel_angle += self.wheel_speed * dt_seconds
            self.wheel_angle %= 360
            # Reibung - langsamer werden
            self.wheel_speed *= (0.985 ** (dt_seconds * 60))  # Frame-unabhängige Reibung
            
            # Tick-Sound bei jedem Segmentübergang
            num_segments = len(WHEEL_SEGMENTS)
            segment_angle = 360 / num_segments
            old_seg = int((self.wheel_angle - self.wheel_speed * dt_seconds) / segment_angle) % num_segments
            new_seg = int(self.wheel_angle / segment_angle) % num_segments
            if old_seg != new_seg and hasattr(self, 'sfx'):
                self.sfx.play('wheel_tick')
            
            if self.wheel_speed < 5:
                self.wheel_spinning = False
                self.wheel_speed = 0
                # Ergebnis berechnen
                self._calculate_wheel_result()
                if hasattr(self, 'sfx'):
                    self.sfx.play('wheel_win')
        
        if self.wheel_result_timer > 0:
            self.wheel_result_timer -= dt_seconds
        if self.wheel_flash_timer > 0:
            self.wheel_flash_timer -= dt_seconds
        
        # Input
        w, h = pg.display.get_window_size()
        for event in events:
            if event.type == pg.KEYDOWN:
                if self.show_streak_popup:
                    if event.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                        self.show_streak_popup = False
                elif self.in_settings:
                    self._handle_settings_input(event)
                elif self.in_wheel:
                    self._handle_wheel_input(event)
                elif self.in_perk_shop:
                    self._handle_perk_shop_input(event)
                else:
                    self._handle_menu_input(event)
            elif event.type == pg.MOUSEMOTION:
                mx, my = event.pos
                if self.show_streak_popup:
                    pass
                elif self.in_settings:
                    self._handle_settings_mouse_drag(mx, my, w, h)
                elif self.in_wheel:
                    pass
                elif self.in_perk_shop:
                    self._handle_perk_mouse_hover(mx, my, w, h)
                else:
                    self._handle_menu_mouse_hover(mx, my, w, h)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.show_streak_popup:
                    self.show_streak_popup = False
                elif self.in_settings:
                    self._handle_settings_click(mx, my, w, h)
                elif self.in_wheel:
                    self._handle_wheel_click(mx, my, w, h)
                elif self.in_perk_shop:
                    self._handle_perk_click(mx, my, w, h)
                else:
                    self._handle_menu_click(mx, my, w, h)
                    # Glücksrad-Icon Klick prüfen
                    if hasattr(self, '_wheel_icon_rect') and self._wheel_icon_rect.collidepoint(mx, my):
                        if hasattr(self, 'sfx'):
                            self.sfx.play('menu_confirm')
                        self._open_wheel()
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                if self.in_settings:
                    self.settings_dragging = None
    
    def _handle_menu_input(self, event):
        if event.key == pg.K_UP or event.key == pg.K_w:
            self.selected = (self.selected - 1) % len(self.menu_items)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_DOWN or event.key == pg.K_s:
            self.selected = (self.selected + 1) % len(self.menu_items)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_confirm')
            if self.selected == 0:
                if hasattr(self, 'sfx'):
                    self.sfx.stop_menu_music()
                self.exit("play")
            elif self.selected == 1:
                self.in_perk_shop = True
                self.perk_selected = 0
            elif self.selected == 2:
                self.in_settings = True
                self.settings_selected = 0
            elif self.selected == 3:
                pg.quit()
                exit()
        elif event.key == pg.K_ESCAPE:
            pg.quit()
            exit()
    
    def _handle_perk_shop_input(self, event):
        if event.key == pg.K_ESCAPE or event.key == pg.K_BACKSPACE:
            self.in_perk_shop = False
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_confirm')
        elif event.key == pg.K_UP or event.key == pg.K_w:
            self.perk_selected = (self.perk_selected - 1) % len(PERKS)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_DOWN or event.key == pg.K_s:
            self.perk_selected = (self.perk_selected + 1) % len(PERKS)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
            self._try_buy_perk()
    
    # ==================== MAUS-STEUERUNG ====================
    def _get_menu_rects(self, w, h):
        """Gibt die Hitboxen der Menü-Items zurück"""
        menu_y = h // 2 - 50
        item_spacing = 70
        box_w = 350
        box_h = 55
        box_x = w // 2 - box_w // 2
        rects = []
        for i in range(len(self.menu_items)):
            box_y = menu_y + i * item_spacing - 10
            rects.append(pg.Rect(box_x, box_y, box_w, box_h))
        return rects
    
    def _handle_menu_mouse_hover(self, mx, my, w, h):
        """Aktualisiert die Auswahl bei Maus-Hover"""
        for i, rect in enumerate(self._get_menu_rects(w, h)):
            if rect.collidepoint(mx, my):
                if self.selected != i and hasattr(self, 'sfx'):
                    self.sfx.play('menu_select')
                self.selected = i
                return
    
    def _handle_menu_click(self, mx, my, w, h):
        """Menü-Item per Mausklick aktivieren"""
        for i, rect in enumerate(self._get_menu_rects(w, h)):
            if rect.collidepoint(mx, my):
                self.selected = i
                if hasattr(self, 'sfx'):
                    self.sfx.play('menu_confirm')
                if i == 0:
                    if hasattr(self, 'sfx'):
                        self.sfx.stop_menu_music()
                    self.exit("play")
                elif i == 1:
                    self.in_perk_shop = True
                    self.perk_selected = 0
                elif i == 2:
                    self.in_settings = True
                    self.settings_selected = 0
                elif i == 3:
                    pg.quit()
                    exit()
                return
    
    def _get_perk_rects(self, w, h):
        """Gibt die Hitboxen der Perk-Items zurück"""
        panel_w = min(550, w - 60)
        panel_x = w // 2 - panel_w // 2
        start_y = 140
        item_h = 70
        rects = []
        for i in range(len(PERKS)):
            item_y = start_y + i * (item_h + 8)
            rects.append(pg.Rect(panel_x, item_y, panel_w, item_h))
        return rects
    
    def _handle_perk_mouse_hover(self, mx, my, w, h):
        """Aktualisiert die Perk-Auswahl bei Maus-Hover"""
        for i, rect in enumerate(self._get_perk_rects(w, h)):
            if rect.collidepoint(mx, my):
                if self.perk_selected != i and hasattr(self, 'sfx'):
                    self.sfx.play('menu_select')
                self.perk_selected = i
                return
    
    def _handle_perk_click(self, mx, my, w, h):
        """Perk per Mausklick kaufen"""
        for i, rect in enumerate(self._get_perk_rects(w, h)):
            if rect.collidepoint(mx, my):
                self.perk_selected = i
                self._try_buy_perk()
                return
    
    # ==================== EINSTELLUNGEN ====================
    def _get_settings_slider_rects(self, w, h):
        """Gibt die Slider-Rects für die Einstellungen zurück"""
        panel_w = min(500, w - 80)
        panel_x = w // 2 - panel_w // 2
        slider_w = panel_w - 40
        slider_h = 12
        slider_x = panel_x + 20
        rects = []
        labels = ["Musik", "Sound-Effekte"]
        for i in range(len(labels)):
            y = 220 + i * 120
            rects.append({
                'label': labels[i],
                'track': pg.Rect(slider_x, y + 40, slider_w, slider_h),
                'full_area': pg.Rect(slider_x - 15, y, slider_w + 30, 70),
            })
        return rects
    
    def _handle_settings_input(self, event):
        """Tastatur-Input für Einstellungen"""
        if event.key == pg.K_ESCAPE or event.key == pg.K_BACKSPACE:
            self.in_settings = False
            save_settings(self.settings_data)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_confirm')
        elif event.key == pg.K_UP or event.key == pg.K_w:
            self.settings_selected = (self.settings_selected - 1) % 2
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_DOWN or event.key == pg.K_s:
            self.settings_selected = (self.settings_selected + 1) % 2
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_select')
        elif event.key == pg.K_LEFT or event.key == pg.K_a:
            self._adjust_setting(self.settings_selected, -5)
        elif event.key == pg.K_RIGHT or event.key == pg.K_d:
            self._adjust_setting(self.settings_selected, 5)
    
    def _adjust_setting(self, idx, delta):
        """Ändert einen Einstellungswert"""
        keys = ['music_volume', 'sfx_volume']
        key = keys[idx]
        old_val = self.settings_data[key]
        self.settings_data[key] = max(0, min(100, old_val + delta))
        if self.settings_data[key] != old_val:
            self._apply_volume_settings()
            save_settings(self.settings_data)
    
    def _apply_volume_settings(self):
        """Wendet die aktuellen Lautstärke-Einstellungen an"""
        if hasattr(self, 'sfx'):
            self.sfx.set_music_volume(self.settings_data['music_volume'] / 100.0)
            self.sfx.set_sfx_volume(self.settings_data['sfx_volume'] / 100.0)
    
    def _handle_settings_click(self, mx, my, w, h):
        """Mausklick in den Einstellungen"""
        sliders = self._get_settings_slider_rects(w, h)
        for i, slider in enumerate(sliders):
            track = slider['track']
            # Etwas größerer Klickbereich
            click_rect = pg.Rect(track.x - 15, track.y - 15, track.w + 30, track.h + 30)
            if click_rect.collidepoint(mx, my):
                self.settings_dragging = i
                self._update_slider_from_mouse(i, mx, w, h)
                return
        
        # Zurück-Button (unten)
        back_rect = pg.Rect(w // 2 - 100, h - 100, 200, 50)
        if back_rect.collidepoint(mx, my):
            self.in_settings = False
            save_settings(self.settings_data)
            if hasattr(self, 'sfx'):
                self.sfx.play('menu_confirm')
    
    def _handle_settings_mouse_drag(self, mx, my, w, h):
        """Maus-Drag auf Slider"""
        if self.settings_dragging is not None:
            self._update_slider_from_mouse(self.settings_dragging, mx, w, h)
    
    def _update_slider_from_mouse(self, idx, mx, w, h):
        """Aktualisiert den Slider-Wert basierend auf der Mausposition"""
        sliders = self._get_settings_slider_rects(w, h)
        track = sliders[idx]['track']
        # Wert berechnen (0-100)
        rel_x = mx - track.x
        val = max(0, min(100, int(rel_x / track.w * 100)))
        keys = ['music_volume', 'sfx_volume']
        self.settings_data[keys[idx]] = val
        self._apply_volume_settings()
        save_settings(self.settings_data)
    
    def _handle_wheel_click(self, mx, my, w, h):
        """Glücksrad per Mausklick drehen / Belohnung einsammeln"""
        # Spin-Button: Mitte des Rades
        cx, cy = w // 2, h // 2 + 20
        radius = min(w, h) // 3
        dist = math.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
        if dist <= radius:
            # Innerhalb des Rades geklickt - gleiche Logik wie ENTER
            if self.wheel_can_spin and not self.wheel_spinning and self.wheel_result is None:
                self.wheel_speed = random.uniform(600, 1000)
                self.wheel_spinning = True
                self.wheel_result = None
                self.wheel_claimed = False
                if hasattr(self, 'sfx'):
                    self.sfx.play('menu_confirm')
            elif self.wheel_result is not None and not self.wheel_claimed:
                gems = load_gems()
                gems += self.wheel_result["gems"]
                save_gems(gems)
                last_spin = load_last_spin()
                today = date.today().isoformat()
                if last_spin != today:
                    save_last_spin(today)
                else:
                    self.wheel_free_spins = max(0, self.wheel_free_spins - 1)
                    save_free_spins(self.wheel_free_spins)
                self.wheel_claimed = True
                last_spin_now = load_last_spin()
                daily_left = (last_spin_now != today)
                self.wheel_can_spin = daily_left or self.wheel_free_spins > 0
                self.wheel_flash_timer = 1.0
                if hasattr(self, 'sfx'):
                    self.sfx.play('gem_pickup')
                if self.wheel_can_spin:
                    self.wheel_result = None
                    self.wheel_claimed = False
    
    def _check_login_streak(self):
        """Prüft und aktualisiert den Login-Streak"""
        streak_data = load_streak_data()
        today = date.today().isoformat()
        last_login = streak_data['last_login']
        self.streak_count = streak_data['streak_count']
        self.wheel_free_spins = streak_data['free_spins']
        
        if last_login == today:
            # Heute schon eingeloggt - Popup trotzdem zeigen (ohne neuen Reward)
            self.streak_already_claimed = True
            reward_idx = (self.streak_count - 1) % 7
            self.streak_reward_claimed = STREAK_REWARDS[reward_idx]
            self.show_streak_popup = True
            self.streak_popup_timer = 0
            self.streak_popup_anim = 0
            return
        
        if last_login is not None:
            try:
                last_date = date.fromisoformat(last_login)
                days_diff = (date.today() - last_date).days
                if days_diff == 1:
                    # Streak geht weiter!
                    self.streak_count += 1
                elif days_diff > 1:
                    # Streak gebrochen - Neustart
                    self.streak_count = 1
                else:
                    return  # Sollte nicht passieren
            except:
                self.streak_count = 1
        else:
            # Erster Login überhaupt
            self.streak_count = 1
        
        # Reward für den aktuellen Streak-Tag berechnen (7-Tage-Zyklus)
        reward_idx = (self.streak_count - 1) % 7
        reward = STREAK_REWARDS[reward_idx]
        
        # Reward anwenden
        if reward["type"] == "gems":
            gems = load_gems()
            gems += reward["amount"]
            save_gems(gems)
        elif reward["type"] == "xp_booster":
            current_booster = load_xp_booster()
            save_xp_booster(current_booster + reward["amount"])
        elif reward["type"] == "free_spins":
            self.wheel_free_spins += reward["amount"]
            save_free_spins(self.wheel_free_spins)
        
        # Streak speichern
        save_streak_data(self.streak_count, today, self.wheel_free_spins)
        
        # Popup anzeigen
        self.streak_already_claimed = False
        self.streak_reward_claimed = reward
        self.show_streak_popup = True
        self.streak_popup_timer = 0
        self.streak_popup_anim = 0
    
    def _open_wheel(self):
        """Öffnet das Glücksrad"""
        self.in_wheel = True
        self.wheel_result = None
        self.wheel_claimed = False
        self.wheel_result_timer = 0
        # Free Spins laden
        self.wheel_free_spins = load_free_spins()
        # Prüfe ob heute schon gesponnen wurde
        last_spin = load_last_spin()
        today = date.today().isoformat()
        daily_available = (last_spin != today)
        self.wheel_can_spin = daily_available or self.wheel_free_spins > 0
    
    def _handle_wheel_input(self, event):
        """Input für das Glücksrad"""
        if event.key == pg.K_ESCAPE or event.key == pg.K_BACKSPACE:
            self.in_wheel = False
        elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
            if self.wheel_can_spin and not self.wheel_spinning and self.wheel_result is None:
                # Spin starten!
                self.wheel_speed = random.uniform(600, 1000)  # Zufällige Startgeschwindigkeit
                self.wheel_spinning = True
                self.wheel_result = None
                self.wheel_claimed = False
                if hasattr(self, 'sfx'):
                    self.sfx.play('menu_confirm')
            elif self.wheel_result is not None and not self.wheel_claimed:
                # Belohnung einsammeln
                gems = load_gems()
                gems += self.wheel_result["gems"]
                save_gems(gems)
                
                # Prüfe ob Daily-Spin oder Free-Spin verbraucht wird
                last_spin = load_last_spin()
                today = date.today().isoformat()
                if last_spin != today:
                    # Daily-Spin verbrauchen
                    save_last_spin(today)
                else:
                    # Free-Spin verbrauchen
                    self.wheel_free_spins = max(0, self.wheel_free_spins - 1)
                    save_free_spins(self.wheel_free_spins)
                
                self.wheel_claimed = True
                # Prüfe ob noch Spins verfügbar
                last_spin_now = load_last_spin()
                daily_left = (last_spin_now != today)
                self.wheel_can_spin = daily_left or self.wheel_free_spins > 0
                self.wheel_flash_timer = 1.0
                if hasattr(self, 'sfx'):
                    self.sfx.play('gem_pickup')
                
                # Für nächsten Spin vorbereiten, wenn noch Spins da
                if self.wheel_can_spin:
                    self.wheel_result = None
                    self.wheel_claimed = False
    
    def _calculate_wheel_result(self):
        """Berechnet das Ergebnis basierend auf der Rad-Position"""
        num_segments = len(WHEEL_SEGMENTS)
        segment_angle = 360 / num_segments
        # Der Zeiger ist oben (bei 90°) - berechne welches Segment dort ist
        # wheel_angle dreht das Rad, der Zeiger bleibt fix oben
        pointer_angle = (90 - self.wheel_angle) % 360
        segment_idx = int(pointer_angle / segment_angle) % num_segments
        self.wheel_result = WHEEL_SEGMENTS[segment_idx]
        self.wheel_result_timer = 5.0  # 5 Sekunden Ergebnis anzeigen
    
    def _try_buy_perk(self):
        """Versucht den ausgewählten Perk zu kaufen"""
        perk = PERKS[self.perk_selected]
        perks = load_perks()
        current_level = perks.get(perk["id"], 0)
        
        if current_level >= perk["max_level"]:
            return  # Schon maxed
        
        cost = perk["cost_per_level"][current_level]
        gems = load_gems()
        
        if gems >= cost:
            # Kauf erfolgreich!
            gems -= cost
            perks[perk["id"]] = current_level + 1
            save_gems(gems)
            save_perks(perks)
            self.perk_buy_flash[perk["id"]] = 0.5  # Flash-Animation
            if hasattr(self, 'sfx'):
                self.sfx.play('perk_buy')
        else:
            self.perk_error_flash = 1.0  # Fehler-Feedback
            if hasattr(self, 'sfx'):
                self.sfx.play('error')

    def draw(self, s):
        """Zeichnet das Hauptmenü oder den Perk-Shop"""
        w, h = s.get_size()
        self.last_w = w
        self.last_h = h
        
        # Hintergrund zeichnen (gemeinsam)
        self._draw_background(s, w, h)
        
        if self.in_wheel:
            self._draw_wheel(s, w, h)
        elif self.in_perk_shop:
            self._draw_perk_shop(s, w, h)
        elif self.in_settings:
            self._draw_settings(s, w, h)
        else:
            self._draw_main_menu(s, w, h)
        
        # Streak-Popup über allem zeichnen
        if self.show_streak_popup:
            self._draw_streak_popup(s, w, h)
    
    def _draw_background(self, s, w, h):
        """Zeichnet den animierten Ozean-Hintergrund"""
        # Hintergrund - Ozean-Gradient
        for y in range(h):
            t = y / h
            # Von dunkelblau zu hellblau
            r = int(10 + 30 * t)
            g = int(30 + 60 * t)
            b = int(80 + 100 * t)
            pg.draw.line(s, (r, g, b), (0, y), (w, y))
        
        # Wellen-Effekt
        wave_surf = pg.Surface((w, h), pg.SRCALPHA)
        for i in range(5):
            wave_y = h - 100 - i * 30 + math.sin(self.wave_offset + i * 0.5) * 20
            wave_color = (50 + i * 20, 100 + i * 20, 180 + i * 15, 100 - i * 15)
            points = []
            for x in range(0, w + 20, 20):
                y_offset = math.sin((x + self.wave_offset * 50) / 50 + i) * 15
                points.append((x, wave_y + y_offset))
            points.append((w, h))
            points.append((0, h))
            pg.draw.polygon(wave_surf, wave_color, points)
        s.blit(wave_surf, (0, 0))
        
        # Partikel (Sterne/Glitzer)
        for p in self.particles:
            p.draw(s)
        
        # Schiff-Silhouette
        ship_y_offset = math.sin(self.timer * 2) * 10
        ship_surf = pg.Surface((80, 60), pg.SRCALPHA)
        # Schiffsrumpf
        pg.draw.polygon(ship_surf, (40, 30, 20, 200), [(10, 40), (70, 40), (60, 55), (20, 55)])
        # Mast
        pg.draw.line(ship_surf, (60, 45, 30, 200), (40, 40), (40, 10), 3)
        # Segel
        pg.draw.polygon(ship_surf, (200, 200, 180, 200), [(42, 15), (65, 35), (42, 35)])
        s.blit(ship_surf, (self.ship_x, self.ship_y + ship_y_offset))
    
    def _draw_title(self, s, w, h):
        """Zeichnet den animierten Titel"""
        # Titel mit Wellen-Effekt
        title = "PIRATES"
        title_x = w // 2
        title_y = 50
        
        # Schatten
        for i, char in enumerate(title):
            offset_y = math.sin(self.title_wave + i * 0.5) * 8
            char_surf = self.font_title.render(char, True, (0, 0, 0))
            char_x = title_x - len(title) * 25 + i * 50
            s.blit(char_surf, (char_x + 4, title_y + offset_y + 4))
        
        # Haupttext mit Gold-Gradient
        for i, char in enumerate(title):
            offset_y = math.sin(self.title_wave + i * 0.5) * 8
            gold_r = 255
            gold_g = int(200 + math.sin(self.timer * 2 + i) * 50)
            gold_b = int(50 + math.sin(self.timer * 3 + i) * 50)
            char_surf = self.font_title.render(char, True, (gold_r, gold_g, gold_b))
            char_x = title_x - len(title) * 25 + i * 50
            s.blit(char_surf, (char_x, title_y + offset_y))
    
    def _draw_gem_counter(self, s, w, y):
        """Zeichnet den Gem-Counter"""
        gems = load_gems()
        # Diamant-Symbol
        gem_icon_x = w // 2 - 80
        gem_points = [
            (gem_icon_x, y + 8), (gem_icon_x + 8, y), (gem_icon_x + 16, y + 8), 
            (gem_icon_x + 8, y + 20)
        ]
        pg.draw.polygon(s, (255, 220, 50), gem_points)
        pg.draw.polygon(s, (255, 255, 200), gem_points, 2)
        
        gem_text = f"{gems}"
        gem_surf = self.font_subtitle.render(gem_text, True, (255, 220, 100))
        s.blit(gem_surf, (gem_icon_x + 24, y - 2))
    
    def _draw_main_menu(self, s, w, h):
        """Zeichnet das Hauptmenü"""
        self._draw_title(s, w, h)
        
        # Untertitel
        subtitle = "Ein Piraten-Abenteuer"
        subtitle_surf = self.font_subtitle.render(subtitle, True, (200, 220, 255))
        s.blit(subtitle_surf, (w // 2 - subtitle_surf.get_width() // 2, 140))
        
        # Gem-Anzeige 
        self._draw_gem_counter(s, w, 180)
        
        # Menü-Items
        menu_y = h // 2 - 50
        item_spacing = 70
        for i, item in enumerate(self.menu_items):
            is_selected = i == self.selected
            
            # Hover-Effekt
            if is_selected:
                # Pulsierende Auswahl
                pulse = abs(math.sin(self.timer * 4)) * 0.3 + 0.7
                color = (int(255 * pulse), int(220 * pulse), int(100 * pulse))
                
                # Auswahlbox
                box_w = 350
                box_h = 55
                box_x = w // 2 - box_w // 2
                box_y = menu_y + i * item_spacing - 10
                
                # Glühender Rahmen
                glow_surf = pg.Surface((box_w + 20, box_h + 20), pg.SRCALPHA)
                pg.draw.rect(glow_surf, (255, 200, 50, 50), (0, 0, box_w + 20, box_h + 20), border_radius=15)
                s.blit(glow_surf, (box_x - 10, box_y - 10))
                
                # Box
                pg.draw.rect(s, (50, 40, 30), (box_x, box_y, box_w, box_h), border_radius=10)
                pg.draw.rect(s, color, (box_x, box_y, box_w, box_h), 3, border_radius=10)
                
                # Pfeil
                arrow_x = box_x - 40
                arrow_offset = math.sin(self.timer * 8) * 5
                pg.draw.polygon(s, color, [
                    (arrow_x + arrow_offset, box_y + box_h // 2),
                    (arrow_x - 15 + arrow_offset, box_y + box_h // 2 - 10),
                    (arrow_x - 15 + arrow_offset, box_y + box_h // 2 + 10)
                ])
            else:
                color = (180, 180, 200)
            
            # Text
            text_surf = self.font_menu.render(item, True, color)
            text_x = w // 2 - text_surf.get_width() // 2
            text_y = menu_y + i * item_spacing
            
            # Schatten
            shadow_surf = self.font_menu.render(item, True, (0, 0, 0))
            s.blit(shadow_surf, (text_x + 2, text_y + 2))
            s.blit(text_surf, (text_x, text_y))
        
        # Steuerungshinweise
        controls_y = h - 80
        controls = [
            "Pfeiltasten / W/S / Maus - Auswahlen",
            "ENTER / LEERTASTE / Linksklick - Bestatigen"
        ]
        for i, ctrl in enumerate(controls):
            ctrl_surf = self.font_small.render(ctrl, True, (150, 170, 200))
            s.blit(ctrl_surf, (w // 2 - ctrl_surf.get_width() // 2, controls_y + i * 25))
        
        # Version
        version = "v1.0 - Premium Edition"
        version_surf = self.font_small.render(version, True, (100, 120, 150))
        s.blit(version_surf, (10, h - 30))
        
        # Free Spins Anzeige (unten links mit klickbarem Glücksrad-Icon)
        free_spins = load_free_spins()
        spin_icon_x = 12
        spin_icon_y = h - 65
        icon_r = 20  # etwas größer für bessere Klickbarkeit
        
        # Hover-Check für Glücksrad-Icon
        mouse_pos = pg.mouse.get_pos()
        icon_area = pg.Rect(spin_icon_x, spin_icon_y, icon_r * 2 + 90, icon_r * 2 + 10)
        is_icon_hovered = icon_area.collidepoint(mouse_pos)
        
        # Hover-Glow Effekt
        if is_icon_hovered:
            glow_surf = pg.Surface((icon_area.w + 16, icon_area.h + 16), pg.SRCALPHA)
            pulse = abs(math.sin(self.timer * 5)) * 0.3 + 0.4
            pg.draw.rect(glow_surf, (255, 200, 50, int(60 * pulse)), (0, 0, icon_area.w + 16, icon_area.h + 16), border_radius=12)
            s.blit(glow_surf, (icon_area.x - 8, icon_area.y - 8))
        
        # Mini-Glücksrad Icon zeichnen
        icon_surf = pg.Surface((icon_r * 2 + 4, icon_r * 2 + 4), pg.SRCALPHA)
        ic = icon_r + 2
        seg_colors = [(255, 200, 50), (50, 200, 100), (200, 80, 80), (80, 150, 255),
                      (255, 150, 50), (100, 220, 200), (220, 100, 200), (180, 180, 50)]
        spin_speed = 60 if is_icon_hovered else 30  # Schneller drehen bei Hover
        for i in range(8):
            start_a = math.radians(i * 45 + self.timer * spin_speed)
            end_a = math.radians((i + 1) * 45 + self.timer * spin_speed)
            pts = [(ic, ic)]
            for step in range(6):
                a = start_a + (end_a - start_a) * step / 5
                pts.append((int(ic + math.cos(a) * icon_r), int(ic - math.sin(a) * icon_r)))
            if len(pts) >= 3:
                pg.draw.polygon(icon_surf, seg_colors[i], pts)
        border_color = (255, 240, 100) if is_icon_hovered else (255, 220, 100)
        pg.draw.circle(icon_surf, border_color, (ic, ic), icon_r, 2)
        pg.draw.circle(icon_surf, (255, 240, 180), (ic, ic), 4)
        s.blit(icon_surf, (spin_icon_x, spin_icon_y))
        
        # Spin-Anzahl Text
        spin_color = (50, 255, 150) if free_spins > 0 else (120, 130, 150)
        if is_icon_hovered:
            spin_color = (100, 255, 180) if free_spins > 0 else (180, 190, 210)
        spin_text = f"{free_spins}"
        spin_surf = self.font_perk.render(spin_text, True, spin_color)
        s.blit(spin_surf, (spin_icon_x + icon_r * 2 + 10, spin_icon_y + 5))
        
        # "Free Spins" Label
        label_color = (200, 210, 240) if is_icon_hovered else (150, 170, 200)
        label_surf = self.font_perk_desc.render("Free Spins", True, label_color)
        s.blit(label_surf, (spin_icon_x + icon_r * 2 + 10, spin_icon_y + 26))
        
        # Speichere Icon-Rect für Klick-Erkennung
        self._wheel_icon_rect = icon_area
        
        # Credits
        credits = "2026 Piraten Studios"
        credits_surf = self.font_small.render(credits, True, (100, 120, 150))
        s.blit(credits_surf, (w - credits_surf.get_width() - 10, h - 30))
    
    def _draw_perk_shop(self, s, w, h):
        """Zeichnet den Perk-Shop"""
        perks_data = load_perks()
        gems = load_gems()
        
        # Titel
        title_surf = self.font_title.render("PERKS", True, (255, 220, 100))
        shadow_surf = self.font_title.render("PERKS", True, (0, 0, 0))
        s.blit(shadow_surf, (w // 2 - title_surf.get_width() // 2 + 3, 33))
        s.blit(title_surf, (w // 2 - title_surf.get_width() // 2, 30))
        
        # Gem-Counter oben
        self._draw_gem_counter(s, w, 105)
        
        # Perk-Liste
        panel_w = min(550, w - 60)
        panel_x = w // 2 - panel_w // 2
        start_y = 140
        item_h = 70
        
        for i, perk in enumerate(PERKS):
            is_selected = i == self.perk_selected
            current_level = perks_data.get(perk["id"], 0)
            is_maxed = current_level >= perk["max_level"]
            cost = perk["cost_per_level"][current_level] if not is_maxed else 0
            can_afford = gems >= cost and not is_maxed
            
            item_y = start_y + i * (item_h + 8)
            
            # Hintergrund-Box
            box_surf = pg.Surface((panel_w, item_h), pg.SRCALPHA)
            
            # Kauf-Flash
            if perk["id"] in self.perk_buy_flash:
                flash_t = self.perk_buy_flash[perk["id"]] / 0.5
                flash_alpha = int(100 * flash_t)
                pg.draw.rect(box_surf, (100, 255, 100, flash_alpha), (0, 0, panel_w, item_h), border_radius=10)
            
            if is_selected:
                pg.draw.rect(box_surf, (30, 40, 70, 220), (0, 0, panel_w, item_h), border_radius=10)
                border_color = (255, 220, 100) if can_afford else (150, 150, 150)
                pg.draw.rect(box_surf, border_color, (0, 0, panel_w, item_h), 3, border_radius=10)
            else:
                pg.draw.rect(box_surf, (15, 25, 50, 200), (0, 0, panel_w, item_h), border_radius=10)
                pg.draw.rect(box_surf, (60, 70, 100, 150), (0, 0, panel_w, item_h), 1, border_radius=10)
            
            s.blit(box_surf, (panel_x, item_y))
            
            # Icon (farbiger Kreis mit Symbol)
            icon_x = panel_x + 35
            icon_y = item_y + item_h // 2
            icon_color = perk["icon_color"]
            
            # Glüh-Effekt für ausgewählt
            if is_selected:
                glow_surf = pg.Surface((50, 50), pg.SRCALPHA)
                pg.draw.circle(glow_surf, (*icon_color, 60), (25, 25), 25)
                s.blit(glow_surf, (icon_x - 25, icon_y - 25))
            
            pg.draw.circle(s, icon_color, (icon_x, icon_y), 18)
            pg.draw.circle(s, (255, 255, 255), (icon_x, icon_y), 18, 2)
            
            # Level-Nummer im Icon
            lvl_surf = self.font_small.render(str(current_level), True, (255, 255, 255))
            s.blit(lvl_surf, (icon_x - lvl_surf.get_width() // 2, icon_y - lvl_surf.get_height() // 2))
            
            # Perk-Name
            name_color = (255, 255, 255) if not is_maxed else (100, 255, 100)
            name_surf = self.font_perk.render(perk["name"], True, name_color)
            s.blit(name_surf, (panel_x + 65, item_y + 10))
            
            # Beschreibung
            desc_surf = self.font_perk_desc.render(perk["description"], True, (180, 190, 220))
            s.blit(desc_surf, (panel_x + 65, item_y + 36))
            
            # Level-Balken (rechts)
            bar_x = panel_x + panel_w - 180
            bar_y = item_y + 12
            for lvl in range(perk["max_level"]):
                pip_x = bar_x + lvl * 22
                pip_w = 18
                pip_h = 14
                if lvl < current_level:
                    pg.draw.rect(s, icon_color, (pip_x, bar_y, pip_w, pip_h), border_radius=3)
                    pg.draw.rect(s, (255, 255, 255, 150), (pip_x, bar_y, pip_w, pip_h), 1, border_radius=3)
                else:
                    pg.draw.rect(s, (40, 50, 70), (pip_x, bar_y, pip_w, pip_h), border_radius=3)
                    pg.draw.rect(s, (80, 90, 110), (pip_x, bar_y, pip_w, pip_h), 1, border_radius=3)
            
            # Kosten / MAX Anzeige (rechts unten)
            if is_maxed:
                max_surf = self.font_perk_desc.render("MAX", True, (100, 255, 100))
                s.blit(max_surf, (panel_x + panel_w - 50, item_y + 42))
            else:
                cost_color = (255, 220, 100) if can_afford else (200, 80, 80)
                cost_text = f"{cost}"
                cost_surf = self.font_perk_desc.render(cost_text, True, cost_color)
                # Kleines Gem-Symbol vor Kosten
                gem_x = panel_x + panel_w - 70
                gem_y = item_y + 44
                mini_gem = [(gem_x, gem_y + 4), (gem_x + 5, gem_y), (gem_x + 10, gem_y + 4), (gem_x + 5, gem_y + 10)]
                pg.draw.polygon(s, (255, 220, 50), mini_gem)
                s.blit(cost_surf, (gem_x + 14, item_y + 40))
        
        # Error-Flash ("Nicht genug Gems!")
        if self.perk_error_flash > 0:
            error_alpha = min(255, int(self.perk_error_flash * 255))
            error_surf = self.font_menu.render("Nicht genug Gems!", True, (255, 80, 80))
            error_bg = pg.Surface((error_surf.get_width() + 30, error_surf.get_height() + 10), pg.SRCALPHA)
            pg.draw.rect(error_bg, (80, 0, 0, min(200, error_alpha)), (0, 0, error_bg.get_width(), error_bg.get_height()), border_radius=8)
            s.blit(error_bg, (w // 2 - error_bg.get_width() // 2, h - 110))
            error_surf.set_alpha(error_alpha)
            s.blit(error_surf, (w // 2 - error_surf.get_width() // 2, h - 105))
        
        # Steuerungshinweise
        controls = "W/S / Maus = Auswahlen   ENTER / Klick = Kaufen   ESC = Zuruck"
        ctrl_surf = self.font_small.render(controls, True, (150, 170, 200))
        s.blit(ctrl_surf, (w // 2 - ctrl_surf.get_width() // 2, h - 40))
    
    # ==================== EINSTELLUNGEN ZEICHNEN ====================
    def _draw_settings(self, s, w, h):
        """Zeichnet das Einstellungsmenü"""
        # Titel
        title_surf = self.font_title.render("Einstellungen", True, (255, 220, 100))
        shadow_surf = self.font_title.render("Einstellungen", True, (0, 0, 0))
        tx = w // 2 - title_surf.get_width() // 2
        s.blit(shadow_surf, (tx + 3, 43))
        s.blit(title_surf, (tx, 40))
        
        # Panel
        panel_w = min(500, w - 80)
        panel_h = 340
        panel_x = w // 2 - panel_w // 2
        panel_y = 130
        
        # Panel Hintergrund
        panel_surf = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        pg.draw.rect(panel_surf, (20, 30, 50, 200), (0, 0, panel_w, panel_h), border_radius=15)
        pg.draw.rect(panel_surf, (100, 150, 200, 100), (0, 0, panel_w, panel_h), 2, border_radius=15)
        s.blit(panel_surf, (panel_x, panel_y))
        
        # Slider zeichnen
        sliders = self._get_settings_slider_rects(w, h)
        keys = ['music_volume', 'sfx_volume']
        icons = ["♪", "🔊"]
        
        for i, slider in enumerate(sliders):
            val = self.settings_data[keys[i]]
            track = slider['track']
            is_selected = i == self.settings_selected
            
            # Label
            label_color = (255, 220, 100) if is_selected else (200, 210, 230)
            label_surf = self.font_perk.render(f"{slider['label']}", True, label_color)
            s.blit(label_surf, (track.x, track.y - 35))
            
            # Prozentwert rechts
            val_text = f"{val}%"
            val_surf = self.font_perk.render(val_text, True, label_color)
            s.blit(val_surf, (track.right - val_surf.get_width(), track.y - 35))
            
            # Track Hintergrund
            pg.draw.rect(s, (40, 50, 70), track, border_radius=6)
            pg.draw.rect(s, (80, 100, 130), track, 1, border_radius=6)
            
            # Gefüllter Teil
            fill_w = int(track.w * val / 100)
            if fill_w > 0:
                fill_rect = pg.Rect(track.x, track.y, fill_w, track.h)
                if is_selected:
                    fill_color = (255, 200, 50)
                else:
                    fill_color = (100, 180, 255)
                pg.draw.rect(s, fill_color, fill_rect, border_radius=6)
            
            # Knopf/Handle
            knob_x = track.x + fill_w
            knob_y = track.y + track.h // 2
            knob_r = 10 if is_selected else 8
            knob_color = (255, 255, 255) if is_selected else (200, 210, 230)
            pg.draw.circle(s, knob_color, (knob_x, knob_y), knob_r)
            if is_selected:
                pg.draw.circle(s, (255, 200, 50), (knob_x, knob_y), knob_r, 2)
            
            # Auswahl-Pfeil
            if is_selected:
                arrow_x = track.x - 30
                arrow_offset = math.sin(self.timer * 8) * 3
                pg.draw.polygon(s, (255, 200, 50), [
                    (arrow_x + arrow_offset, track.y + track.h // 2),
                    (arrow_x - 10 + arrow_offset, track.y + track.h // 2 - 8),
                    (arrow_x - 10 + arrow_offset, track.y + track.h // 2 + 8)
                ])
        
        # Zurück-Button
        back_rect = pg.Rect(w // 2 - 100, h - 100, 200, 50)
        pg.draw.rect(s, (50, 40, 30), back_rect, border_radius=10)
        pg.draw.rect(s, (150, 170, 200), back_rect, 2, border_radius=10)
        back_text = self.font_perk.render("Zurück", True, (200, 210, 230))
        s.blit(back_text, (w // 2 - back_text.get_width() // 2, h - 90))
        
        # Steuerungshinweise
        hints_y = h - 45
        hints = "← → / A/D / Maus - Lautstärke ändern  |  ESC - Zurück"
        hints_surf = self.font_small.render(hints, True, (150, 170, 200))
        s.blit(hints_surf, (w // 2 - hints_surf.get_width() // 2, hints_y))
    
    def _draw_wheel(self, s, w, h):
        """Zeichnet das Glücksrad"""
        # Titel
        title_text = "GLÜCKSRAD"
        title_surf = self.font_title.render(title_text, True, (255, 220, 100))
        shadow_surf = self.font_title.render(title_text, True, (0, 0, 0))
        s.blit(shadow_surf, (w // 2 - title_surf.get_width() // 2 + 3, 23))
        s.blit(title_surf, (w // 2 - title_surf.get_width() // 2, 20))
        
        # Gem-Counter
        self._draw_gem_counter(s, w, 90)
        
        # Rad-Parameter
        cx, cy = w // 2, h // 2 + 20
        radius = min(w, h) // 3
        num_segments = len(WHEEL_SEGMENTS)
        segment_angle = 360 / num_segments
        
        # Gewinn-Flash Hintergrund
        if self.wheel_flash_timer > 0:
            flash_alpha = int(self.wheel_flash_timer * 80)
            flash_surf = pg.Surface((w, h), pg.SRCALPHA)
            flash_surf.fill((255, 255, 100, flash_alpha))
            s.blit(flash_surf, (0, 0))
        
        # Äußerer Glow-Ring
        glow_surf = pg.Surface((radius * 2 + 40, radius * 2 + 40), pg.SRCALPHA)
        glow_colors = [(255, 200, 50, 40), (255, 150, 50, 25), (255, 100, 50, 15)]
        for i, color in enumerate(glow_colors):
            pg.draw.circle(glow_surf, color, (radius + 20, radius + 20), radius + 20 - i * 5)
        s.blit(glow_surf, (cx - radius - 20, cy - radius - 20))
        
        # Rad zeichnen - Segmente
        wheel_surf = pg.Surface((radius * 2 + 4, radius * 2 + 4), pg.SRCALPHA)
        wheel_cx = radius + 2
        wheel_cy = radius + 2
        
        for i, seg in enumerate(WHEEL_SEGMENTS):
            start_angle = math.radians(i * segment_angle + self.wheel_angle)
            end_angle = math.radians((i + 1) * segment_angle + self.wheel_angle)
            
            # Segment als gefülltes Polygon
            points = [(wheel_cx, wheel_cy)]
            steps = 20
            for step in range(steps + 1):
                angle = start_angle + (end_angle - start_angle) * step / steps
                px = wheel_cx + math.cos(angle) * radius
                py = wheel_cy - math.sin(angle) * radius
                points.append((px, py))
            
            if len(points) >= 3:
                # Segment-Farbe
                color = seg["color"]
                pg.draw.polygon(wheel_surf, color, points)
                
                # Hellere Innenkante
                lighter = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
                inner_points = [(wheel_cx, wheel_cy)]
                for step in range(steps + 1):
                    angle = start_angle + (end_angle - start_angle) * step / steps
                    px = wheel_cx + math.cos(angle) * (radius * 0.3)
                    py = wheel_cy - math.sin(angle) * (radius * 0.3)
                    inner_points.append((px, py))
                if len(inner_points) >= 3:
                    pg.draw.polygon(wheel_surf, lighter, inner_points)
                
                # Trennlinien
                lx = wheel_cx + math.cos(start_angle) * radius
                ly = wheel_cy - math.sin(start_angle) * radius
                pg.draw.line(wheel_surf, (255, 255, 255, 180), (wheel_cx, wheel_cy), (lx, ly), 2)
            
            # Text auf Segment
            mid_angle = start_angle + (end_angle - start_angle) / 2
            text_dist = radius * 0.65
            tx = wheel_cx + math.cos(mid_angle) * text_dist
            ty = wheel_cy - math.sin(mid_angle) * text_dist
            
            gem_text = seg["label"]
            # Größere Schrift für höhere Werte
            if seg["gems"] >= 10:
                font = self.font_menu
            else:
                font = self.font_perk
            
            text_surf = font.render(gem_text, True, (255, 255, 255))
            # Text rotieren passend zum Segment
            rot_angle = math.degrees(mid_angle)
            rotated_text = pg.transform.rotate(text_surf, rot_angle)
            text_rect = rotated_text.get_rect(center=(tx, ty))
            wheel_surf.blit(rotated_text, text_rect)
        
        # Äußerer Rand
        pg.draw.circle(wheel_surf, (255, 220, 100), (wheel_cx, wheel_cy), radius, 4)
        pg.draw.circle(wheel_surf, (200, 170, 50), (wheel_cx, wheel_cy), radius + 2, 2)
        
        # Dekorative Punkte am Rand
        for i in range(num_segments * 2):
            angle = math.radians(i * (360 / (num_segments * 2)) + self.wheel_angle * 0.5)
            dx = wheel_cx + math.cos(angle) * (radius + 1)
            dy = wheel_cy - math.sin(angle) * (radius + 1)
            blink = abs(math.sin(self.timer * 8 + i)) > 0.5
            dot_color = (255, 255, 200) if blink else (200, 180, 100)
            pg.draw.circle(wheel_surf, dot_color, (int(dx), int(dy)), 4)
        
        # Mittelkreis
        pg.draw.circle(wheel_surf, (60, 50, 40), (wheel_cx, wheel_cy), 20)
        pg.draw.circle(wheel_surf, (255, 220, 100), (wheel_cx, wheel_cy), 20, 3)
        pg.draw.circle(wheel_surf, (255, 240, 180), (wheel_cx, wheel_cy), 8)
        
        s.blit(wheel_surf, (cx - wheel_cx, cy - wheel_cy))
        
        # Zeiger (oben, fix) - Dreieck das nach unten zeigt
        pointer_x = cx
        pointer_y = cy - radius - 5
        pg.draw.polygon(s, (255, 50, 50), [
            (pointer_x, pointer_y + 30),
            (pointer_x - 15, pointer_y),
            (pointer_x + 15, pointer_y)
        ])
        pg.draw.polygon(s, (255, 200, 200), [
            (pointer_x, pointer_y + 30),
            (pointer_x - 15, pointer_y),
            (pointer_x + 15, pointer_y)
        ], 2)
        # Kleiner Kreis oben am Zeiger
        pg.draw.circle(s, (255, 80, 80), (pointer_x, pointer_y - 2), 6)
        pg.draw.circle(s, (255, 200, 200), (pointer_x, pointer_y - 2), 6, 2)
        
        # Status-Text unten
        if self.wheel_claimed and not self.wheel_can_spin:
            # Keine Spins mehr
            msg = "Komme morgen wieder!"
            msg_surf = self.font_menu.render(msg, True, (150, 200, 255))
            s.blit(msg_surf, (w // 2 - msg_surf.get_width() // 2, h - 120))
        elif self.wheel_result is not None and not self.wheel_spinning:
            # Ergebnis anzeigen
            gems_won = self.wheel_result["gems"]
            pulse = abs(math.sin(self.timer * 6)) * 0.4 + 0.6
            
            # Gewinn-Box
            box_w = 400
            box_h = 60
            box_x = w // 2 - box_w // 2
            box_y = h - 140
            
            box_surf = pg.Surface((box_w, box_h), pg.SRCALPHA)
            pg.draw.rect(box_surf, (20, 30, 50, 220), (0, 0, box_w, box_h), border_radius=12)
            r_col = int(255 * pulse)
            g_col = int(220 * pulse)
            b_col = int(50 * pulse)
            pg.draw.rect(box_surf, (r_col, g_col, b_col), (0, 0, box_w, box_h), 3, border_radius=12)
            s.blit(box_surf, (box_x, box_y))
            
            win_text = f"Du hast {gems_won} Gem{'s' if gems_won > 1 else ''} gewonnen!"
            win_surf = self.font_menu.render(win_text, True, (int(255 * pulse), int(230 * pulse), int(80 * pulse)))
            s.blit(win_surf, (w // 2 - win_surf.get_width() // 2, box_y + 12))
            
            # Einsammeln-Hinweis
            collect_text = "ENTER zum Einsammeln"
            collect_pulse = abs(math.sin(self.timer * 4))
            collect_alpha = int(150 + 105 * collect_pulse)
            collect_surf = self.font_small.render(collect_text, True, (255, 255, 200))
            collect_surf.set_alpha(collect_alpha)
            s.blit(collect_surf, (w // 2 - collect_surf.get_width() // 2, h - 70))
        elif not self.wheel_can_spin:
            msg = "Komme morgen wieder!"
            msg_surf = self.font_menu.render(msg, True, (150, 170, 200))
            s.blit(msg_surf, (w // 2 - msg_surf.get_width() // 2, h - 120))
        elif not self.wheel_spinning:
            # Bereit zum Spinnen
            spin_pulse = abs(math.sin(self.timer * 3))
            spin_text = "Drücke ENTER zum Drehen!"
            spin_color = (int(150 + 105 * spin_pulse), int(200 + 55 * spin_pulse), int(100 + 100 * spin_pulse))
            spin_surf = self.font_menu.render(spin_text, True, spin_color)
            s.blit(spin_surf, (w // 2 - spin_surf.get_width() // 2, h - 120))
            
            # Hinweis je nach Spin-Typ
            last_spin = load_last_spin()
            today = date.today().isoformat()
            if last_spin != today:
                daily_text = "Einmal pro Tag kostenlos!"
            else:
                daily_text = f"Free Spin! ({self.wheel_free_spins} uebrig)"
            daily_surf = self.font_small.render(daily_text, True, (200, 220, 255))
            s.blit(daily_surf, (w // 2 - daily_surf.get_width() // 2, h - 80))
        
        # Free Spins Anzeige
        if self.wheel_free_spins > 0:
            spin_text = f"Free Spins: {self.wheel_free_spins}"
            spin_surf = self.font_perk.render(spin_text, True, (50, 255, 150))
            s.blit(spin_surf, (w // 2 - spin_surf.get_width() // 2, 115))
        
        # Steuerungshinweise
        controls = "ENTER = Drehen   ESC = Zurück"
        ctrl_surf = self.font_small.render(controls, True, (150, 170, 200))
        s.blit(ctrl_surf, (w // 2 - ctrl_surf.get_width() // 2, h - 40))
    
    def _draw_streak_popup(self, s, w, h):
        """Zeichnet das Login-Streak Popup"""
        if self.streak_reward_claimed is None:
            return
        
        reward = self.streak_reward_claimed
        anim_t = min(1.0, self.streak_popup_anim * 3)  # Einblend-Animation
        
        # Dunkler Overlay
        overlay = pg.Surface((w, h), pg.SRCALPHA)
        overlay.fill((0, 0, 0, int(160 * anim_t)))
        s.blit(overlay, (0, 0))
        
        # Popup-Box (springt rein)
        box_w = 420
        box_h = 320
        box_x = w // 2 - box_w // 2
        # Einspring-Animation (bounce)
        if anim_t < 1.0:
            bounce = 1.0 + math.sin(anim_t * math.pi) * 0.15
            box_y = int(h // 2 - box_h // 2 - (1 - anim_t) * 200)
        else:
            bounce = 1.0
            box_y = h // 2 - box_h // 2
        
        # Hauptbox
        popup_surf = pg.Surface((box_w, box_h), pg.SRCALPHA)
        pg.draw.rect(popup_surf, (15, 25, 55, 240), (0, 0, box_w, box_h), border_radius=16)
        pg.draw.rect(popup_surf, (255, 200, 50), (0, 0, box_w, box_h), 3, border_radius=16)
        s.blit(popup_surf, (box_x, box_y))
        
        # Titel
        title_text = "LOGIN-STREAK!"
        title_surf = self.font_menu.render(title_text, True, (255, 220, 100))
        shadow = self.font_menu.render(title_text, True, (0, 0, 0))
        s.blit(shadow, (w // 2 - title_surf.get_width() // 2 + 2, box_y + 18))
        s.blit(title_surf, (w // 2 - title_surf.get_width() // 2, box_y + 16))
        
        # Streak-Tage Anzeige (7 Kreise)
        day_y = box_y + 65
        circle_spacing = 48
        start_x = w // 2 - (circle_spacing * 6) // 2
        current_day_in_cycle = (self.streak_count - 1) % 7
        
        for i in range(7):
            cx = start_x + i * circle_spacing
            cy = day_y + 12
            day_reward = STREAK_REWARDS[i]
            
            if i < current_day_in_cycle:
                # Vergangene Tage - ausgefüllt
                pg.draw.circle(s, day_reward["icon_color"], (cx, cy), 16)
                check = self.font_small.render("✓", True, (255, 255, 255))
                s.blit(check, (cx - check.get_width() // 2, cy - check.get_height() // 2))
            elif i == current_day_in_cycle:
                # Heutiger Tag - leuchtend, pulsierend
                pulse = abs(math.sin(self.streak_popup_anim * 4)) * 0.4 + 0.6
                glow_size = int(22 * pulse)
                glow = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                pg.draw.circle(glow, (*day_reward["icon_color"], 80), (glow_size, glow_size), glow_size)
                s.blit(glow, (cx - glow_size, cy - glow_size))
                pg.draw.circle(s, day_reward["icon_color"], (cx, cy), 16)
                pg.draw.circle(s, (255, 255, 255), (cx, cy), 16, 2)
                star = self.font_small.render("★", True, (255, 255, 255))
                s.blit(star, (cx - star.get_width() // 2, cy - star.get_height() // 2))
            else:
                # Zukünftige Tage - grau
                pg.draw.circle(s, (40, 50, 70), (cx, cy), 16)
                pg.draw.circle(s, (80, 90, 110), (cx, cy), 16, 2)
            
            # Tag-Nummer
            day_num = self.font_perk_desc.render(str(i + 1), True, (180, 190, 220))
            s.blit(day_num, (cx - day_num.get_width() // 2, cy + 20))
        
        # Streak-Counter
        streak_text = f"Tag {self.streak_count}"
        streak_surf = self.font_subtitle.render(streak_text, True, (255, 200, 80))
        s.blit(streak_surf, (w // 2 - streak_surf.get_width() // 2, box_y + 110))
        
        # Reward-Anzeige (groß, in der Mitte)
        reward_y = box_y + 155
        
        # Reward-Icon (großer Kreis)
        icon_cx = w // 2
        icon_cy = reward_y + 25
        icon_pulse = abs(math.sin(self.streak_popup_anim * 3)) * 0.3 + 0.7
        icon_size = int(28 * icon_pulse)
        
        # Glow
        glow = pg.Surface((icon_size * 3, icon_size * 3), pg.SRCALPHA)
        pg.draw.circle(glow, (*reward["icon_color"], 50), (icon_size * 3 // 2, icon_size * 3 // 2), icon_size * 3 // 2)
        s.blit(glow, (icon_cx - icon_size * 3 // 2, icon_cy - icon_size * 3 // 2))
        
        pg.draw.circle(s, reward["icon_color"], (icon_cx, icon_cy), icon_size)
        pg.draw.circle(s, (255, 255, 255), (icon_cx, icon_cy), icon_size, 2)
        
        # Icon-Symbol je nach Typ
        if reward["type"] == "gems":
            sym = self.font_perk.render("💎", True, (255, 255, 255))
        elif reward["type"] == "xp_booster":
            sym = self.font_perk.render("⚡", True, (255, 255, 255))
        else:
            sym = self.font_perk.render("🎰", True, (255, 255, 255))
        s.blit(sym, (icon_cx - sym.get_width() // 2, icon_cy - sym.get_height() // 2))
        
        # Reward-Text
        reward_text = reward["label"]
        if self.streak_already_claimed:
            reward_surf = self.font_menu.render(reward_text, True, (150, 160, 180))
        else:
            reward_surf = self.font_menu.render(reward_text, True, (255, 255, 255))
        s.blit(reward_surf, (w // 2 - reward_surf.get_width() // 2, icon_cy + 38))
        
        # Typ-Beschreibung
        if self.streak_already_claimed:
            desc = "Bereits abgeholt - komm morgen wieder!"
            desc_color = (140, 150, 170)
        elif reward["type"] == "xp_booster":
            desc = "Doppelte XP im nächsten Spiel!"
            desc_color = (180, 200, 230)
        elif reward["type"] == "free_spins":
            desc = "Nutze sie am Glücksrad!"
            desc_color = (180, 200, 230)
        else:
            desc = "Wurde deinem Konto gutgeschrieben!"
            desc_color = (180, 200, 230)
        desc_surf = self.font_perk_desc.render(desc, True, desc_color)
        s.blit(desc_surf, (w // 2 - desc_surf.get_width() // 2, icon_cy + 72))
        
        # Schließen-Hinweis
        close_pulse = abs(math.sin(self.streak_popup_anim * 2))
        close_alpha = int(150 + 105 * close_pulse)
        close_text = "ENTER zum Schließen"
        close_surf = self.font_small.render(close_text, True, (200, 210, 230))
        close_surf.set_alpha(close_alpha)
        s.blit(close_surf, (w // 2 - close_surf.get_width() // 2, box_y + box_h - 35))
