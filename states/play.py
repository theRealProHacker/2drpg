from time import time
import random
import json
import os
import math
from typing import cast

import pygame as pg
from StateManager import State

from spritesheet import spritesheet
from sounds import get_sound_manager
from states.profile import add_profile_xp, get_all_talent_bonuses

# Pfad für persistente Gem-Speicherung
GEM_SAVE_FILE = "gems_save.json"

# ==================== PIRATEN-PRESETS ====================
PIRATE_PRESETS = {
    'balanced': {
        'name': 'Balanced Captain',
        'max_hp_mult': 1.0,
        'damage_mult': 0.95,
        'speed_mult': 1.0,
        'repair_mult': 1.10,
        'reload_mult': 1.0,
        'defense': 0.05,
        'evasion': 0.05,
    },
    'berserker': {
        'name': 'Berserker Raider',
        'max_hp_mult': 0.85,
        'damage_mult': 1.20,
        'speed_mult': 1.0,
        'repair_mult': 1.0,
        'reload_mult': 1.0,
        'defense': 0.0,
        'evasion': 0.0,
    },
    'navigator': {
        'name': 'Storm Navigator',
        'max_hp_mult': 1.0,
        'damage_mult': 1.0,
        'speed_mult': 1.18,
        'repair_mult': 1.0,
        'reload_mult': 1.15,
        'defense': 0.0,
        'evasion': 0.15,
    },
    'engineer': {
        'name': 'Iron Engineer',
        'max_hp_mult': 1.20,
        'damage_mult': 1.0,
        'speed_mult': 0.90,
        'repair_mult': 1.0,
        'reload_mult': 1.0,
        'defense': 0.15,
        'evasion': 0.0,
    },
    'reaper': {
        'name': 'Reaper Corsair',
        'max_hp_mult': 0.80,
        'damage_mult': 1.30,
        'speed_mult': 1.0,
        'repair_mult': 1.0,
        'reload_mult': 1.0,
        'defense': 0.0,
        'evasion': 0.05,
    },
    'old_salt': {
        'name': 'Old Salt Veteran',
        'max_hp_mult': 1.10,
        'damage_mult': 0.90,
        'speed_mult': 1.0,
        'repair_mult': 1.25,
        'reload_mult': 1.0,
        'defense': 0.10,
        'evasion': 0.05,
    },
    'gunslinger': {
        'name': 'Quickdraw Gunner',
        'max_hp_mult': 1.0,
        'damage_mult': 0.90,
        'speed_mult': 1.0,
        'repair_mult': 1.0,
        'reload_mult': 0.75,
        'defense': 0.0,
        'evasion': 0.08,
    },
    'juggernaut': {
        'name': 'Juggernaut',
        'max_hp_mult': 1.40,
        'damage_mult': 0.95,
        'speed_mult': 0.82,
        'repair_mult': 1.0,
        'reload_mult': 1.0,
        'defense': 0.25,
        'evasion': 0.0,
    },
    'duelist': {
        'name': 'Sea Duelist',
        'max_hp_mult': 0.90,
        'damage_mult': 1.12,
        'speed_mult': 1.12,
        'repair_mult': 1.0,
        'reload_mult': 1.0,
        'defense': 0.05,
        'evasion': 0.12,
    },
    'warlord': {
        'name': 'Dread Warlord',
        'max_hp_mult': 1.15,
        'damage_mult': 1.25,
        'speed_mult': 1.05,
        'repair_mult': 0.85,
        'reload_mult': 1.0,
        'defense': 0.12,
        'evasion': 0.08,
    },
}

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
        'unlock_pirate': None,
    },
    {
        'id': 'play_60_min',
        'name': 'Veteran Sailor',
        'description': 'Play for 60 total minutes',
        'type': 'playtime',
        'target': 3600,
        'reward_gems': 20,
        'unlock_pirate': None,
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


# ==================== PARTIKEL-SYSTEM ====================
class Particle:
    """Ein einzelnes Partikel für Effekte"""
    def __init__(self, pos, velocity, color, size, lifetime, gravity=0, fade=True, shrink=True):
        self.pos = pg.Vector2(pos)
        self.velocity = pg.Vector2(velocity)
        self.color = color
        self.size = size
        self.max_size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.fade = fade
        self.shrink = shrink
        self.is_dead = False
    
    def update(self, dt):
        self.pos += self.velocity * dt
        self.velocity.y += self.gravity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
    
    def draw(self, surface, offset):
        if self.is_dead:
            return
        screen_pos = self.pos - offset
        
        # Größe basierend auf Lebenszeit
        size = self.size
        if self.shrink:
            size = int(self.max_size * (self.lifetime / self.max_lifetime))
        
        if size > 0:
            # Einfacher Kreis ohne separate Surface (PERFORMANCE)
            pg.draw.circle(surface, self.color[:3], (int(screen_pos.x), int(screen_pos.y)), size)


class WakeParticle:
    """Kielwasser-Partikel hinter Schiffen"""
    def __init__(self, pos, size=8):
        self.pos = pg.Vector2(pos)
        self.size = size
        self.max_size = size
        self.lifetime = 2.0
        self.max_lifetime = 2.0
        self.is_dead = False
    
    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
    
    def draw(self, surface, offset):
        if self.is_dead:
            return
        screen_pos = self.pos - offset
        
        progress = 1 - (self.lifetime / self.max_lifetime)
        size = int(self.max_size * (1 + progress * 2))
        
        if size > 0:
            # Einfacher Kreis ohne separate Surface (PERFORMANCE)
            alpha_color = (200, 220, 255)
            pg.draw.circle(surface, alpha_color, (int(screen_pos.x), int(screen_pos.y)), size)
            pg.draw.circle(surface, (255, 255, 255), (int(screen_pos.x), int(screen_pos.y)), size, 2)


class ExplosionEffect:
    """Explosions-Effekt bei Treffern"""
    def __init__(self, pos, color=(255, 150, 50), size=30):
        self.pos = pg.Vector2(pos)
        self.particles = []
        self.is_dead = False
        
        # Partikel erstellen
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            velocity = pg.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            particle_color = (
                min(255, color[0] + random.randint(-30, 30)),
                min(255, color[1] + random.randint(-30, 30)),
                min(255, max(0, color[2] + random.randint(-30, 30)))
            )
            self.particles.append(Particle(
                pos, velocity, particle_color,
                size=random.randint(3, 8),
                lifetime=random.uniform(0.3, 0.8),
                gravity=100, fade=True, shrink=True
            ))
        
        # Rauch-Partikel
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 60)
            velocity = pg.Vector2(math.cos(angle) * speed, math.sin(angle) * speed - 30)
            self.particles.append(Particle(
                pos, velocity, (80, 80, 80),
                size=random.randint(8, 15),
                lifetime=random.uniform(0.5, 1.2),
                gravity=-20, fade=True, shrink=False
            ))
    
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead]
        if not self.particles:
            self.is_dead = True
    
    def draw(self, surface, offset):
        for p in self.particles:
            p.draw(surface, offset)


class SplashEffect:
    """Wasser-Spritzer-Effekt"""
    def __init__(self, pos):
        self.pos = pg.Vector2(pos)
        self.particles = []
        self.is_dead = False
        
        for _ in range(10):
            angle = random.uniform(-math.pi, 0)  # Nur nach oben
            speed = random.uniform(80, 180)
            velocity = pg.Vector2(math.cos(angle) * speed * 0.3, math.sin(angle) * speed)
            self.particles.append(Particle(
                pos, velocity, (150, 200, 255),
                size=random.randint(2, 5),
                lifetime=random.uniform(0.3, 0.7),
                gravity=400, fade=True, shrink=True
            ))
    
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead]
        if not self.particles:
            self.is_dead = True
    
    def draw(self, surface, offset):
        for p in self.particles:
            p.draw(surface, offset)


class DamageNumber:
    """Schwebende Schadenszahl"""
    _font = None  # Shared font für alle Instanzen
    
    @classmethod
    def _get_font(cls):
        if cls._font is None:
            cls._font = pg.font.SysFont("Arial", 24, bold=True)
        return cls._font
    
    def __init__(self, pos, damage, color=(255, 50, 50), text=None):
        self.pos = pg.Vector2(pos)
        self.damage = damage
        self.color = color
        self.text = text  # Optionaler Text (z.B. "MISS") statt einer Zahl
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.velocity = pg.Vector2(random.uniform(-20, 20), -80)
        self.is_dead = False
    
    def update(self, dt):
        self.pos += self.velocity * dt
        self.velocity.y += 50 * dt  # Verlangsamen
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
    
    def draw(self, surface, offset):
        if self.is_dead:
            return
        screen_pos = self.pos - offset
        font = DamageNumber._get_font()
        label = self.text if self.text is not None else str(int(self.damage))

        # Schatten
        shadow_text = font.render(label, True, (0, 0, 0))
        surface.blit(shadow_text, (int(screen_pos.x) + 2, int(screen_pos.y) + 2))

        # Text
        text = font.render(label, True, self.color)
        surface.blit(text, (int(screen_pos.x), int(screen_pos.y)))


# ==================== CREW-SYSTEM ====================
class CrewMember:
    """Ein Besatzungsmitglied mit Rolle und Gesundheit"""
    ROLES = {
        'driver': {'name': 'Driver', 'effect': 'Movement', 'health': 100},
        'gunner': {'name': 'Gunner', 'effect': 'Cannons', 'health': 100},
        'loader': {'name': 'Loader', 'effect': 'Reload', 'health': 80},
        'navigator': {'name': 'Navigator', 'effect': 'Handling', 'health': 90},
        'engineer': {'name': 'Engineer', 'effect': 'Repair', 'health': 90},
        'boatswain': {'name': 'Boatswain', 'effect': 'Hull', 'health': 90}
    }
    
    def __init__(self, role):
        self.role = role
        self.health = self.ROLES[role]['health']
        self.max_health = self.ROLES[role]['health']
        self.is_alive = True
        self.damage_percentage = 0  # 0-100
        self.name = self.ROLES[role]['name']
        self.level = 1  # 1=Green, 2=Veteran, 3=Master

    def take_damage(self, amount):
        """Nimmt Schaden"""
        if not self.is_alive:
            return
        self.health -= amount
        self.damage_percentage = max(0, min(100, 100 * (1 - self.health / self.max_health)))
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            self.damage_percentage = 100
    
    def heal(self, amount):
        """Heilt das Crew-Mitglied"""
        if not self.is_alive:
            return False
        self.health = min(self.max_health, self.health + amount)
        self.damage_percentage = max(0, min(100, 100 * (1 - self.health / self.max_health)))
        return True
    
    def get_color(self):
        """Gibt die Farbe basierend auf Schadensgrad zurück"""
        if self.damage_percentage <= 33:
            return (0, 220, 0)  # Grün
        elif self.damage_percentage <= 67:
            return (255, 220, 0)  # Gelb
        else:
            return (255, 50, 50)  # Rot


class ShipCrew:
    """Verwaltet die Besatzung und deren Effekte"""
    def __init__(self):
        self.driver = CrewMember('driver')
        self.gunner = CrewMember('gunner')
        self.loader = CrewMember('loader')
        self.navigator = CrewMember('navigator')
        self.engineer = CrewMember('engineer')
        self.boatswain = CrewMember('boatswain')

        # Rekrutierte Reserve-Crew (auf Inseln angeheuert)
        self.reserves = []  # list[CrewMember]

        # Ersatz-Timer
        self.driver_replacement_timer = 0
        self.driver_replacement_duration = 3.0  # 3 Sekunden zum Ersetzen
        self.driver_needs_replacement = False
        self.gunner_replacement_timer = 0
        self.gunner_replacement_duration = 2.5
        self.gunner_needs_replacement = False
        
        self.crew_death_timer = 0
    
    def alive_count(self):
        """Zählt lebende Crew-Mitglieder"""
        return sum(1 for _role, member in self.get_members() if member.is_alive)

    def get_members(self):
        """Liefert alle Crew-Mitglieder als (role, member)"""
        return [
            ('driver', self.driver),
            ('gunner', self.gunner),
            ('loader', self.loader),
            ('navigator', self.navigator),
            ('engineer', self.engineer),
            ('boatswain', self.boatswain),
        ]
    
    def driver_alive(self):
        """Prüft ob Driver am Leben ist"""
        return self.driver.is_alive
    
    def add_recruit(self, role, level=1, name=None):
        """Fügt eine auf einer Insel angeheuerte Person zur Reserve hinzu."""
        m = CrewMember(role)
        m.level = level
        if name:
            m.name = name
        self.reserves.append(m)
        return m

    def has_replacement_available(self):
        """Prüft ob ein Ersatz verfügbar ist (Reserve-Crew oder lebende Support-Rolle)."""
        if self.reserves:
            return True
        return any(member.is_alive for role, member in self.get_members() if role in ('loader', 'navigator', 'engineer', 'boatswain'))

    def has_driver_replacement_available(self):
        """Prüft ob Driver ersetzt werden kann"""
        return self.has_replacement_available()

    def has_gunner_replacement_available(self):
        """Prüft ob Gunner ersetzt werden kann"""
        return self.has_replacement_available()
    
    def try_replace_driver(self, dt):
        """Versucht den Driver zu ersetzen wenn er tot ist"""
        if self.driver.is_alive or not self.driver_needs_replacement:
            self.driver_replacement_timer = 0
            return False
        
        self.driver_replacement_timer += dt
        if self.driver_replacement_timer >= self.driver_replacement_duration:
            # Eine Reserve-Crew ersetzt Driver
            if self.has_driver_replacement_available():
                self.driver.is_alive = True
                self.driver.health = self.driver.max_health
                self.driver.damage_percentage = 0
                if self.reserves:
                    self.reserves.pop(0)
                self.driver_needs_replacement = False
                self.driver_replacement_timer = 0
                return True
        return False

    def try_replace_gunner(self, dt):
        """Versucht den Gunner zu ersetzen wenn er tot ist"""
        if self.gunner.is_alive or not self.gunner_needs_replacement:
            self.gunner_replacement_timer = 0
            return False

        self.gunner_replacement_timer += dt
        if self.gunner_replacement_timer >= self.gunner_replacement_duration:
            # Eine Reserve-Crew ersetzt Gunner
            if self.has_gunner_replacement_available():
                self.gunner.is_alive = True
                self.gunner.health = self.gunner.max_health
                self.gunner.damage_percentage = 0
                if self.reserves:
                    self.reserves.pop(0)
                self.gunner_needs_replacement = False
                self.gunner_replacement_timer = 0
                return True
        return False
    
    def on_crew_death(self, role):
        """Wird aufgerufen wenn ein Crew-Mitglied stirbt"""
        if role == 'driver' and self.has_driver_replacement_available():
            self.driver_needs_replacement = True
        if role == 'gunner' and self.has_gunner_replacement_available():
            self.gunner_needs_replacement = True
    
    def draw_hud(self, surface, width, height):
        """Zeichnet das Crew-HUD ohne einzelne Lebensleisten"""
        hud_x = width - 250
        hud_y = 10
        box_width = 240
        box_height = 80
        
        # Hintergrund mit Militär-Stil
        pg.draw.rect(surface, (20, 20, 40), (hud_x, hud_y, box_width, box_height))
        pg.draw.rect(surface, (100, 150, 180), (hud_x, hud_y, box_width, box_height), 2)
        
        # Font
        font_small = pg.font.SysFont("Arial", 16, bold=True)
        font_tiny = pg.font.SysFont("Arial", 13)
        
        # Titel
        title = font_small.render("CREW", True, (100, 200, 255))
        surface.blit(title, (hud_x + 10, hud_y + 5))
        
        y_offset = hud_y + 28
        alive = self.alive_count()
        count_surf = font_small.render(f"{alive}/6 Alive", True, (210, 230, 255))
        surface.blit(count_surf, (hud_x + 12, y_offset))

        # Rolle-Status kurz als Punkte: D/G/L/N/E/B
        status_chars = [
            ('D', self.driver),
            ('G', self.gunner),
            ('L', self.loader),
            ('N', self.navigator),
            ('E', self.engineer),
            ('B', self.boatswain),
        ]
        sx = hud_x + 12
        sy = hud_y + 56
        for label, member in status_chars:
            color = member.get_color() if member.is_alive else (15, 15, 15)
            pg.draw.circle(surface, color, (sx, sy), 6)
            pg.draw.circle(surface, (90, 90, 90), (sx, sy), 6, 1)
            text = font_tiny.render(label, True, (220, 220, 220))
            surface.blit(text, (sx - 4, sy + 8))
            sx += 35
        
        # Replacement-Info für kritische Rollen
        if self.driver_needs_replacement and self.has_driver_replacement_available():
            progress = self.driver_replacement_timer / self.driver_replacement_duration
            progress_text = font_tiny.render(f"Driver Replacing... {int(progress*100)}%", True, (255, 200, 0))
            surface.blit(progress_text, (hud_x + 120, hud_y + 8))
        elif self.gunner_needs_replacement and self.has_gunner_replacement_available():
            progress = self.gunner_replacement_timer / self.gunner_replacement_duration
            progress_text = font_tiny.render(f"Gunner Replacing... {int(progress*100)}%", True, (255, 200, 0))
            surface.blit(progress_text, (hud_x + 120, hud_y + 8))
    
    def draw_ship_model(self, surface, width, height):
        """Schadensmodell: zeigt direkt am Schiff, welche Systeme intakt/beschaedigt/zerstoert sind."""
        model_x = width - 130
        model_y = 145

        box_width = 120
        box_height = 205
        box_left = model_x - 60
        box_top = model_y - 22
        pg.draw.rect(surface, (18, 22, 38), (box_left, box_top, box_width, box_height), border_radius=4)
        pg.draw.rect(surface, (80, 120, 160), (box_left, box_top, box_width, box_height), 2, border_radius=4)

        font_title = pg.font.SysFont("Arial", 13, bold=True)
        font_tag = pg.font.SysFont("Arial", 9, bold=True)
        font_status = pg.font.SysFont("Arial", 12, bold=True)

        title = font_title.render("DAMAGE MODEL", True, (120, 200, 255))
        surface.blit(title, (box_left + box_width // 2 - title.get_width() // 2, box_top + 4))

        center_x = model_x
        center_y = model_y + 52
        t = pg.time.get_ticks() * 0.001

        # ----- Hilfsfunktionen -----
        def lerp(c1, c2, f):
            f = max(0.0, min(1.0, f))
            return (int(c1[0] + (c2[0] - c1[0]) * f),
                    int(c1[1] + (c2[1] - c1[1]) * f),
                    int(c1[2] + (c2[2] - c1[2]) * f))

        def state_color(member):
            """Gruen (intakt) -> Gelb -> Rot (kritisch); Grau wenn zerstoert."""
            if not member.is_alive:
                return (60, 60, 66)
            ratio = max(0.0, min(1.0, member.health / max(1, member.max_health)))
            if ratio > 0.5:
                return lerp((255, 210, 0), (0, 220, 0), (ratio - 0.5) * 2)
            return lerp((225, 40, 40), (255, 210, 0), ratio * 2)

        def mark_x(cx, cy, r):
            pg.draw.line(surface, (235, 45, 45), (cx - r, cy - r), (cx + r, cy + r), 2)
            pg.draw.line(surface, (235, 45, 45), (cx - r, cy + r), (cx + r, cy - r), 2)

        def smoke(cx, cy):
            # aufsteigender Rauch fuer zerstoerte Bauteile
            for i in range(3):
                ph = (t * 1.4 + i * 0.33) % 1.0
                sy = int(cy - ph * 22)
                sx = cx + int(math.sin(t * 4 + i * 2) * 4)
                rad = int(2 + ph * 5)
                shade = max(30, int(110 - ph * 70))
                pg.draw.circle(surface, (shade, shade, shade), (sx, sy), rad)

        def tag(text, cx, cy, member):
            col = (235, 80, 80) if not member.is_alive else (170, 190, 210)
            lbl = font_tag.render(text, True, col)
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy))

        # ----- Rumpf (Boatswain) -----
        rumpf_outer = [
            (center_x - 28, center_y - 50), (center_x - 22, center_y - 35),
            (center_x - 20, center_y - 15), (center_x - 18, center_y),
            (center_x - 18, center_y + 35), (center_x - 20, center_y + 45),
            (center_x - 15, center_y + 55), (center_x + 15, center_y + 55),
            (center_x + 20, center_y + 45), (center_x + 18, center_y + 35),
            (center_x + 18, center_y), (center_x + 20, center_y - 15),
            (center_x + 22, center_y - 35), (center_x + 28, center_y - 50),
        ]
        hull = self.boatswain
        hr = hull.health / max(1, hull.max_health)
        if hull.is_alive:
            hull_fill = lerp((120, 50, 50), (45, 80, 140), hr)
            hull_edge = lerp((210, 80, 80), (110, 160, 230), hr)
        else:
            hull_fill = (40, 32, 32)
            hull_edge = (170, 55, 55)
        pg.draw.polygon(surface, hull_fill, rumpf_outer)
        pg.draw.polygon(surface, hull_edge, rumpf_outer, 2)

        deck_inner = [
            (center_x - 22, center_y - 45), (center_x - 16, center_y - 30),
            (center_x - 14, center_y + 25), (center_x - 12, center_y + 50),
            (center_x + 12, center_y + 50), (center_x + 14, center_y + 25),
            (center_x + 16, center_y - 30), (center_x + 22, center_y - 45),
        ]
        deck_col = lerp((70, 60, 55), (70, 110, 165), hr if hull.is_alive else 0.0)
        pg.draw.polygon(surface, deck_col, deck_inner)

        if not hull.is_alive:
            # Wasserlinie-Loecher + Rauch wenn der Rumpf zerstoert ist
            for hx, hy in [(-12, -10), (10, 15), (-8, 38), (6, -28)]:
                pg.draw.circle(surface, (15, 12, 12), (center_x + hx, center_y + hy), 4)
            smoke(center_x - 16, center_y + 30)

        # ----- Kanonen (Gunner) -----
        gc = state_color(self.gunner)
        for tx in (center_x - 12, center_x + 12):
            pg.draw.circle(surface, gc, (tx, center_y - 25), 6)
            pg.draw.circle(surface, (15, 15, 15), (tx, center_y - 25), 6, 1)
            bx = tx + (7 if tx > center_x else -7)
            barrel_col = (40, 40, 40) if self.gunner.is_alive else (75, 75, 75)
            pg.draw.line(surface, barrel_col, (tx, center_y - 25), (bx, center_y - 35), 3)
        if not self.gunner.is_alive:
            mark_x(center_x - 12, center_y - 25, 6)
            mark_x(center_x + 12, center_y - 25, 6)
            smoke(center_x, center_y - 28)
        tag("GUNS", center_x, center_y - 49, self.gunner)

        # ----- Bruecke / Radar (Navigator) -----
        nc = state_color(self.navigator)
        bridge = pg.Rect(center_x - 9, center_y - 14, 18, 20)
        pg.draw.rect(surface, nc, bridge, border_radius=2)
        pg.draw.rect(surface, (15, 15, 15), bridge, 1, border_radius=2)
        mast_col = (190, 190, 190) if self.navigator.is_alive else (80, 80, 80)
        pg.draw.line(surface, mast_col, (center_x, center_y - 14), (center_x, center_y - 24), 2)
        pg.draw.circle(surface, (210, 210, 0) if self.navigator.is_alive else (70, 70, 70), (center_x, center_y - 24), 2)
        if not self.navigator.is_alive:
            mark_x(center_x, center_y - 4, 8)
            smoke(center_x, center_y - 8)
        tag("BRG", center_x + 22, center_y - 12, self.navigator)

        # ----- Munition (Loader) -----
        lc = state_color(self.loader)
        mag = pg.Rect(center_x - 7, center_y + 8, 14, 11)
        pg.draw.rect(surface, lc, mag, border_radius=2)
        pg.draw.rect(surface, (15, 15, 15), mag, 1, border_radius=2)
        if not self.loader.is_alive:
            mark_x(center_x, center_y + 13, 6)
            smoke(center_x, center_y + 10)
        tag("AMMO", center_x + 20, center_y + 8, self.loader)

        # ----- Maschine (Engineer) -----
        ec = state_color(self.engineer)
        eng = pg.Rect(center_x - 9, center_y + 24, 18, 14)
        pg.draw.rect(surface, ec, eng, border_radius=2)
        pg.draw.rect(surface, (15, 15, 15), eng, 1, border_radius=2)
        pg.draw.line(surface, (25, 25, 25), (center_x - 4, center_y + 26), (center_x - 4, center_y + 36), 1)
        pg.draw.line(surface, (25, 25, 25), (center_x + 4, center_y + 26), (center_x + 4, center_y + 36), 1)
        if not self.engineer.is_alive:
            mark_x(center_x, center_y + 31, 8)
            smoke(center_x, center_y + 26)
        tag("ENG", center_x + 22, center_y + 26, self.engineer)

        # ----- Ruder / Steuer (Driver) -----
        dc = state_color(self.driver)
        wheel = (center_x, center_y + 47)
        pg.draw.circle(surface, dc, wheel, 6)
        pg.draw.circle(surface, (15, 15, 15), wheel, 6, 1)
        for ang in range(0, 360, 45):
            ex = wheel[0] + int(math.cos(math.radians(ang)) * 6)
            ey = wheel[1] + int(math.sin(math.radians(ang)) * 6)
            pg.draw.line(surface, (20, 20, 20), wheel, (ex, ey), 1)
        if not self.driver.is_alive:
            mark_x(wheel[0], wheel[1], 6)
            smoke(center_x, center_y + 44)
        tag("HELM", center_x - 24, center_y + 44, self.driver)

        # Rumpf-Tag
        tag("HULL", center_x - 24, center_y - 40, self.boatswain)

        # ----- Status-Zeile -----
        members = [
            ("GUNS", self.gunner), ("BRIDGE", self.navigator), ("AMMO", self.loader),
            ("ENGINE", self.engineer), ("HELM", self.driver), ("HULL", self.boatswain),
        ]
        down = [name for name, m in members if not m.is_alive]
        footer_y = box_top + box_height - 18
        if down:
            msg = f"{len(down)} SYSTEM{'S' if len(down) > 1 else ''} DOWN"
            blink = 0.5 + 0.5 * math.sin(t * 6)
            col = (int(180 + 75 * blink), 50, 50)
            status = font_status.render(msg, True, col)
        else:
            status = font_status.render("ALL SYSTEMS OK", True, (60, 220, 90))
        surface.blit(status, (box_left + box_width // 2 - status.get_width() // 2, footer_y))
        

# ==================== SCHIFF-SCHADENSMODELL ====================
class ShipDamageModel:
    """Verwaltet Schadenseffekte am Schiff (Löcher, Feuer)"""
    def __init__(self, max_health=100):
        self.max_health = max_health
        self.damage_level = 0  # 0.0 - 1.0 (0 = kein Schaden, 1 = zerstört)
        self.holes = []  # Liste von Loch-Positionen
        self.fire_particles = []  # Feuer-Partikel
        self.smoke_particles = []  # Rauch-Partikel
        self.hole_spawn_timer = 0
        self.fire_spawn_timer = 0
        self.has_fire = False  # Ob das Schiff brennt
        self.fire_damage_timer = 0  # Timer für zusätzlichen Brand-Schaden
        self.fire_damage_cooldown = 2.0  # Alle 2 Sekunden Feuer-Schaden
    
    def update_damage(self, health, max_health):
        """Aktualisiert den Schadensgrad basierend auf Leben"""
        old_damage = self.damage_level
        self.damage_level = 1.0 - (max(0, health) / max_health)
        
        # Löcher erzeugen bei bestimmten Schadensschwellen
        if self.damage_level > 0.3 and old_damage <= 0.3:
            self._spawn_holes(2)
        elif self.damage_level > 0.5 and old_damage <= 0.5:
            self._spawn_holes(3)
        elif self.damage_level > 0.75 and old_damage <= 0.75:
            self._spawn_holes(4)
        
        # Feuer ab 50% Schaden
        if self.damage_level > 0.5:
            self.has_fire = True
        else:
            self.has_fire = False
            self.fire_particles = []
            self.smoke_particles = []
    
    def _spawn_holes(self, count):
        """Erzeugt neue Löcher auf dem Schiff"""
        for _ in range(count):
            # Zufällige Position auf dem Schiff
            x = random.randint(-40, 40)
            y = random.randint(-30, 30)
            hole_size = random.randint(4, 8)
            self.holes.append({
                'x': x,
                'y': y,
                'size': hole_size,
                'age': 0
            })
    
    def update(self, dt, ship_pos):
        """Aktualisiert Feuer- und Raucheffekte"""
        self.hole_spawn_timer += dt
        self.fire_spawn_timer += dt
        self.fire_damage_timer += dt
        
        # Feuer-Partikel erzeugen (wenn Schiff brennt)
        if self.has_fire and self.fire_spawn_timer > 0.05:
            # Flammen
            fire_x = ship_pos.x + random.randint(-30, 30)
            fire_y = ship_pos.y + random.randint(-35, -10)
            
            angle = random.uniform(-math.pi / 4, math.pi / 4)
            speed = random.uniform(40, 120)
            velocity = pg.Vector2(math.cos(angle) * speed, math.sin(angle) * speed - 60)
            
            fire_color = random.choice([
                (255, 100, 0),
                (255, 150, 0),
                (255, 200, 0),
                (200, 50, 0)
            ])
            
            self.fire_particles.append(Particle(
                (fire_x, fire_y), velocity, fire_color,
                size=random.randint(5, 12),
                lifetime=random.uniform(0.3, 0.8),
                gravity=0, fade=True, shrink=True
            ))
            
            # Rauch
            smoke_x = ship_pos.x + random.randint(-25, 25)
            smoke_y = ship_pos.y + random.randint(-40, -5)
            smoke_velocity = pg.Vector2(random.uniform(-20, 20), random.uniform(-80, -40))
            
            self.smoke_particles.append(Particle(
                (smoke_x, smoke_y), smoke_velocity, (100, 100, 100),
                size=random.randint(6, 14),
                lifetime=random.uniform(0.8, 1.5),
                gravity=-20, fade=True, shrink=False
            ))
            
            self.fire_spawn_timer = 0
        
        # Partikel updaten und entfernen
        for p in self.fire_particles:
            p.update(dt)
        self.fire_particles = [p for p in self.fire_particles if not p.is_dead]
        
        for p in self.smoke_particles:
            p.update(dt)
        self.smoke_particles = [p for p in self.smoke_particles if not p.is_dead]
    
    def draw_on_ship(self, surface, ship_pos):
        """Zeichnet Löcher auf dem Schiff"""
        for hole in self.holes:
            hole_x = int(ship_pos.x + hole['x'])
            hole_y = int(ship_pos.y + hole['y'])
            pg.draw.circle(surface, (40, 30, 20), (hole_x, hole_y), hole['size'])
            pg.draw.circle(surface, (20, 10, 0), (hole_x, hole_y), hole['size'], 1)
    
    def draw_effects(self, surface, offset):
        """Zeichnet Feuer und Rauch"""
        for p in self.fire_particles:
            p.draw(surface, offset)
        for p in self.smoke_particles:
            p.draw(surface, offset)


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


def _load_full_save():
    """Lädt die komplette Save-Datei"""
    if os.path.exists(GEM_SAVE_FILE):
        try:
            with open(GEM_SAVE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'gems': 0, 'perks': {}}
    return {'gems': 0, 'perks': {}}


def save_gems(count):
    """Speichert die Gem-Anzahl in der Datei (Perks bleiben erhalten)"""
    data = _load_full_save()
    data['gems'] = count
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


# ==================== FLOTTE & CREW-ROSTER (persistent) ====================
DEFAULT_SHIP = {
    "class_name": "Sloop",
    "hp_mult": 1.0,
    "speed_mult": 1.0,
    "dmg_mult": 1.0,
    "sprite_key": "default",
}


def load_crew_roster():
    """Lädt das permanente Crew-Roster (auf Inseln angeheuerte Reserve-Crew)."""
    data = _load_full_save()
    roster = data.get('crew_roster', [])
    return roster if isinstance(roster, list) else []


def save_crew_roster(roster):
    """Speichert das permanente Crew-Roster."""
    data = _load_full_save()
    data['crew_roster'] = roster
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_fleet():
    """Lädt die Flotte (Liste von Schiff-Dicts); enthält immer mindestens das Standardschiff."""
    data = _load_full_save()
    fleet = data.get('fleet', [])
    if not isinstance(fleet, list) or not fleet:
        return [dict(DEFAULT_SHIP)]
    return fleet


def save_fleet(fleet):
    """Speichert die Flotte."""
    data = _load_full_save()
    data['fleet'] = fleet
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_active_ship_idx():
    """Lädt den Index des aktiven Flaggschiffs."""
    data = _load_full_save()
    try:
        return int(data.get('active_ship_idx', 0))
    except (TypeError, ValueError):
        return 0


def save_active_ship_idx(idx):
    """Speichert den Index des aktiven Flaggschiffs."""
    data = _load_full_save()
    data['active_ship_idx'] = int(idx)
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_selected_pirate_id():
    """Lädt die aktuell ausgewählte Piratenklasse"""
    data = _load_full_save()
    pid = data.get('selected_pirate_id', 'balanced')
    if pid not in PIRATE_PRESETS:
        return 'balanced'
    return pid


def load_achievement_state():
    """Lädt Achievement-Fortschritt"""
    data = _load_full_save()
    ach = data.get('achievements', {})
    return {
        'total_kills': int(ach.get('total_kills', 0)),
        'total_playtime_seconds': float(ach.get('total_playtime_seconds', 0.0)),
        'unlocked': list(ach.get('unlocked', [])),
    }


def save_achievement_state(state):
    """Speichert Achievement-Fortschritt"""
    data = _load_full_save()
    data['achievements'] = {
        'total_kills': int(state.get('total_kills', 0)),
        'total_playtime_seconds': float(state.get('total_playtime_seconds', 0.0)),
        'unlocked': list(state.get('unlocked', [])),
    }
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_unlocked_pirate_ids():
    """Lädt freigeschaltete Piratenklassen"""
    data = _load_full_save()
    base = {'balanced'}
    unlocked = data.get('unlocked_pirates', list(base))
    if not isinstance(unlocked, list):
        return set(base)
    return set(unlocked) | base


def save_unlocked_pirate_ids(unlocked_ids):
    """Speichert freigeschaltete Piratenklassen"""
    data = _load_full_save()
    base = {'balanced'}
    data['unlocked_pirates'] = sorted(set(unlocked_ids) | base)
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_xp_booster():
    """Lädt verbleibende XP-Booster Minuten"""
    data = _load_full_save()
    return data.get('xp_booster_minutes', 0)


def save_xp_booster(minutes):
    """Speichert XP-Booster Minuten"""
    data = _load_full_save()
    data['xp_booster_minutes'] = minutes
    with open(GEM_SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load_highscore():
    """Lädt den Highscore aus der Save-Datei"""
    data = _load_full_save()
    return data.get('highscore', {
        'survival_time': 0,
        'kills': 0,
        'level': 1,
        'gems': 0
    })


def save_highscore(survival_time, kills, level, gems):
    """Speichert den Highscore (basierend auf Überlebenszeit)"""
    data = _load_full_save()
    old = data.get('highscore', {'survival_time': 0, 'kills': 0, 'level': 1, 'gems': 0})
    # Neuer Highscore wenn länger überlebt
    if survival_time > old.get('survival_time', 0):
        data['highscore'] = {
            'survival_time': survival_time,
            'kills': kills,
            'level': level,
            'gems': gems
        }
        with open(GEM_SAVE_FILE, 'w') as f:
            json.dump(data, f)
        return True  # Neuer Highscore!
    return False  # Kein neuer Highscore


class Gem:
    """Ein seltenes Juwel das eingesammelt werden kann - PREMIUM VERSION"""
    def __init__(self, pos):
        self.pos = pg.Vector2(pos)
        self.radius = 18
        self.collected = False
        self.sparkle_timer = 0
        self.float_offset = 0
        self.color = random.choice([
            (255, 50, 150),   # Pink
            (50, 200, 255),   # Cyan
            (255, 200, 50),   # Gold
            (150, 50, 255),   # Lila
            (50, 255, 150),   # Smaragd
        ])
        self.sparkles = []  # Mini-Partikel um das Gem
    
    def update(self, dt_seconds):
        self.sparkle_timer += dt_seconds
        self.float_offset = math.sin(self.sparkle_timer * 3) * 5  # Schweben
        
        # Gelegentlich Sparkle spawnen
        if random.random() < 0.1:
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(10, 25)
            sparkle_pos = pg.Vector2(math.cos(angle) * dist, math.sin(angle) * dist)
            self.sparkles.append({
                'pos': sparkle_pos,
                'life': 0.5,
                'size': random.randint(2, 4)
            })
        
        # Sparkles aktualisieren
        for sparkle in self.sparkles:
            sparkle['life'] -= dt_seconds
            sparkle['pos'].y -= 20 * dt_seconds
        self.sparkles = [s for s in self.sparkles if s['life'] > 0]
    
    def draw(self, surface, offset):
        if self.collected:
            return
        screen_pos = self.pos - offset + pg.Vector2(0, self.float_offset)
        
        # Glitzer-Effekt für Hauptfarbe
        sparkle = abs(math.sin(self.sparkle_timer * 5)) * 0.3 + 0.7
        color = tuple(int(c * sparkle) for c in self.color)
        
        # Diamant-Form zeichnen
        x, y = int(screen_pos.x), int(screen_pos.y)
        
        # Hauptform
        points = [
            (x, y - self.radius),
            (x + self.radius, y),
            (x, y + self.radius // 2),
            (x - self.radius, y),
        ]
        pg.draw.polygon(surface, color, points)
        
        # Highlight (oben)
        highlight_color = tuple(min(255, c + 80) for c in self.color)
        top_points = [
            (x, y - self.radius),
            (x + self.radius // 2, y - self.radius // 3),
            (x, y),
            (x - self.radius // 2, y - self.radius // 3),
        ]
        pg.draw.polygon(surface, highlight_color, top_points)
        
        # Rahmen
        pg.draw.polygon(surface, (255, 255, 255), points, 2)
        
        # Glanzpunkt
        pg.draw.circle(surface, (255, 255, 255), (x - 4, y - 6), 4)
        pg.draw.circle(surface, (255, 255, 255), (x + 2, y - 3), 2)


class StatCrate:
    """Kiste mit zufaelligem Item-Boost fuer diesen Run."""
    def __init__(self, pos):
        self.pos = pg.Vector2(pos)
        self.collected = False
        self.size = 26
        self.timer = random.uniform(0.0, 10.0)
        self.color = random.choice([
            (175, 120, 70),
            (160, 105, 60),
            (190, 130, 75),
        ])

    def update(self, dt_seconds):
        self.timer += dt_seconds

    def draw(self, surface, offset):
        if self.collected:
            return
        bob = math.sin(self.timer * 2.4) * 3
        pulse = abs(math.sin(self.timer * 4.8)) * 0.35 + 0.65
        sx = int(self.pos.x - offset.x)
        sy = int(self.pos.y - offset.y + bob)

        # Schatten
        pg.draw.ellipse(surface, (0, 0, 0, 90), (sx - 18, sy + 13, 36, 10))

        # Glow
        glow_surf = pg.Surface((56, 56), pg.SRCALPHA)
        pg.draw.circle(glow_surf, (255, 190, 90, int(60 * pulse)), (28, 28), 20)
        surface.blit(glow_surf, (sx - 28, sy - 28))

        # Kiste
        outer = pg.Rect(sx - self.size // 2, sy - self.size // 2, self.size, self.size)
        pg.draw.rect(surface, self.color, outer, border_radius=4)
        pg.draw.rect(surface, (95, 62, 35), outer, 2, border_radius=4)
        pg.draw.line(surface, (230, 185, 90), (outer.left, sy), (outer.right, sy), 3)
        pg.draw.line(surface, (230, 185, 90), (sx, outer.top), (sx, outer.bottom), 3)
        pg.draw.rect(surface, (245, 220, 150), (sx - 3, sy - 3, 6, 6), border_radius=2)


# ==================== ARTEFAKTE (Kisten-Beute) ====================
# Jede Kiste enthaelt ein zufaelliges Artefakt. Manche geben simple Stat-Boni,
# andere schalten einzigartige Kampf-Effekte frei (Krit, Lebensraub, Mehrfach-
# schuss, Durchschlag, Explosivmunition, Schild, Wiederbelebung ...).
# apply(p) veraendert die crate_bonus_* Werte des PlayState p.
RARITY_WEIGHT = {'common': 100, 'uncommon': 50, 'rare': 22, 'epic': 9, 'legendary': 3}
RARITY_COLOR = {
    'common': (205, 205, 215),
    'uncommon': (90, 220, 130),
    'rare': (90, 165, 255),
    'epic': (200, 120, 255),
    'legendary': (255, 190, 70),
}

ARTIFACTS = [
    # ---------- Common: einfache Stat-Boni ----------
    {'id': 'wind_sail',   'name': 'Wind-Segel',        'desc': '+8% Fahrtempo',        'rarity': 'common', 'color': (90, 220, 150), 'apply': lambda p: p._art_apply(speed_pct=0.08)},
    {'id': 'canvas',      'name': 'Segeltuch',         'desc': '+6% Fahrtempo',        'rarity': 'common', 'color': (120, 210, 180), 'apply': lambda p: p._art_apply(speed_pct=0.06)},
    {'id': 'fast_fuse',   'name': 'Schnellzuender',    'desc': '+8% Feuerrate',        'rarity': 'common', 'color': (255, 170, 70), 'apply': lambda p: p._art_apply(fire_rate_pct=0.08)},
    {'id': 'powder',      'name': 'Pulverkammer',      'desc': '+6% Feuerrate',        'rarity': 'common', 'color': (255, 190, 90), 'apply': lambda p: p._art_apply(fire_rate_pct=0.06)},
    {'id': 'rations',     'name': 'Heilproviant',      'desc': '+0.8 Reparatur/s',     'rarity': 'common', 'color': (90, 210, 120), 'apply': lambda p: p._art_apply(regen=0.8)},
    {'id': 'planks',      'name': 'Verstaerkte Planken','desc': '+18 Max HP',          'rarity': 'common', 'color': (220, 95, 95),  'apply': lambda p: p._art_apply(max_health=18)},
    {'id': 'oak_hull',    'name': 'Eichenrumpf',       'desc': '+14 Max HP',           'rarity': 'common', 'color': (200, 130, 90),  'apply': lambda p: p._art_apply(max_health=14)},
    {'id': 'sharp_ammo',  'name': 'Scharfe Munition',  'desc': '+6 Schaden',           'rarity': 'common', 'color': (190, 120, 255), 'apply': lambda p: p._art_apply(damage=6)},
    {'id': 'whetstone',   'name': 'Schleifstein',      'desc': '+5 Schaden',           'rarity': 'common', 'color': (170, 140, 230), 'apply': lambda p: p._art_apply(damage=5)},
    {'id': 'lead_ball',   'name': 'Bleikugeln',        'desc': '+8% Schaden',          'rarity': 'common', 'color': (160, 150, 200), 'apply': lambda p: p._art_apply(damage_pct=0.08)},
    {'id': 'lookout',     'name': 'Ausguck',           'desc': '+40 Aufsammel-Radius', 'rarity': 'common', 'color': (120, 200, 255), 'apply': lambda p: p._art_apply(pickup_radius=40)},
    {'id': 'lucky_coin',  'name': 'Gluckstaler',       'desc': '+1 Muenze pro Kill',   'rarity': 'common', 'color': (230, 190, 70),  'apply': lambda p: p._art_apply(coin_bonus=1)},
    {'id': 'ballast',     'name': 'Ballast-Abwurf',    'desc': '+7% Fahrtempo',        'rarity': 'common', 'color': (110, 200, 170), 'apply': lambda p: p._art_apply(speed_pct=0.07)},
    {'id': 'emergency',   'name': 'Notproviant',       'desc': '+12 Max HP, +0.5 Rep', 'rarity': 'common', 'color': (150, 210, 120), 'apply': lambda p: p._art_apply(max_health=12, regen=0.5)},

    # ---------- Uncommon ----------
    {'id': 'gust',        'name': 'Sturmboee',         'desc': '+14% Fahrtempo',       'rarity': 'uncommon', 'color': (80, 230, 160), 'apply': lambda p: p._art_apply(speed_pct=0.14)},
    {'id': 'double_load', 'name': 'Doppellader',       'desc': '+1 Schuss pro Seite',  'rarity': 'uncommon', 'color': (255, 200, 90), 'apply': lambda p: p._art_apply(extra_shots=1)},
    {'id': 'fire_arrow',  'name': 'Brandpfeile',       'desc': '+6% Schaden, kl. Explosion','rarity': 'uncommon', 'color': (255, 140, 60), 'apply': lambda p: p._art_apply(damage_pct=0.06, explosive=45)},
    {'id': 'grapple',     'name': 'Enterhaken',        'desc': '+8 Ramm-Schaden',      'rarity': 'uncommon', 'color': (210, 160, 90), 'apply': lambda p: p._art_apply(ram_damage=8)},
    {'id': 'armor_plate', 'name': 'Panzerplatten',     'desc': '+10% Verteidigung',    'rarity': 'uncommon', 'color': (150, 180, 220), 'apply': lambda p: p._art_apply(defense=0.10)},
    {'id': 'fog_veil',    'name': 'Nebelschleier',     'desc': '+8% Ausweichen',       'rarity': 'uncommon', 'color': (180, 210, 235), 'apply': lambda p: p._art_apply(evasion=0.08)},
    {'id': 'scope',       'name': 'Zielfernrohr',      'desc': '+8% Krit-Chance',      'rarity': 'uncommon', 'color': (255, 120, 120), 'apply': lambda p: p._art_apply(crit_chance=0.08)},
    {'id': 'vampir',      'name': 'Vampirklinge',      'desc': '+6% Lebensraub',       'rarity': 'uncommon', 'color': (210, 70, 90),  'apply': lambda p: p._art_apply(lifesteal=0.06)},
    {'id': 'cannon_oil',  'name': 'Kanonenoel',        'desc': '+12% Feuerrate',       'rarity': 'uncommon', 'color': (255, 180, 80), 'apply': lambda p: p._art_apply(fire_rate_pct=0.12)},
    {'id': 'treasure_map','name': 'Schatzkarte',       'desc': '+12% XP',              'rarity': 'uncommon', 'color': (230, 200, 110),'apply': lambda p: p._art_apply(xp_pct=0.12)},
    {'id': 'gem_luck',    'name': 'Gluecksmuenze',     'desc': '+12% Gem-Fund',        'rarity': 'uncommon', 'color': (255, 220, 90), 'apply': lambda p: p._art_apply(gem_find=0.12)},
    {'id': 'heavy_shot',  'name': 'Wuchtgeschoss',     'desc': 'Groessere Kugeln',     'rarity': 'uncommon', 'color': (170, 160, 210),'apply': lambda p: p._art_apply(proj_size=6)},
    {'id': 'turbo_fuse',  'name': 'Turbolunte',        'desc': '+18% Kugel-Tempo',     'rarity': 'uncommon', 'color': (255, 210, 120),'apply': lambda p: p._art_apply(proj_speed_pct=0.18)},
    {'id': 'rum_barrel',  'name': 'Rumfass',           'desc': '+1.4 Reparatur/s',     'rarity': 'uncommon', 'color': (200, 150, 90), 'apply': lambda p: p._art_apply(regen=1.4)},
    {'id': 'chain_ball',  'name': 'Kettenkugel',       'desc': '+1 Durchschlag',       'rarity': 'uncommon', 'color': (160, 170, 190),'apply': lambda p: p._art_apply(pierce=1)},
    {'id': 'spike_hull',  'name': 'Igel-Panzer',       'desc': 'Reflektiert 60% Schaden','rarity': 'uncommon', 'color': (200, 200, 220),'apply': lambda p: p._art_apply(thorns=0.6)},

    # ---------- Rare ----------
    {'id': 'gunner_master','name': 'Kanonier-Meister', 'desc': '+18% Schaden, +10% Feuerrate','rarity': 'rare', 'color': (200, 110, 255),'apply': lambda p: p._art_apply(damage_pct=0.18, fire_rate_pct=0.10)},
    {'id': 'ghost_ship',  'name': 'Geisterschiff',     'desc': '+14% Ausweichen',      'rarity': 'rare', 'color': (170, 220, 240),'apply': lambda p: p._art_apply(evasion=0.14)},
    {'id': 'bulwark',     'name': 'Bollwerk',          'desc': '+18% Verteidigung, +25 HP','rarity': 'rare', 'color': (140, 190, 230),'apply': lambda p: p._art_apply(defense=0.18, max_health=25)},
    {'id': 'berserk_keg', 'name': 'Berserker-Fass',    'desc': '+25% Schaden, -8% Verteid.','rarity': 'rare', 'color': (255, 90, 70), 'apply': lambda p: p._art_apply(damage_pct=0.25, defense=-0.08)},
    {'id': 'clipper',     'name': 'Schnellsegler',     'desc': '+20% Tempo, +12% Feuerrate','rarity': 'rare', 'color': (90, 230, 190),'apply': lambda p: p._art_apply(speed_pct=0.20, fire_rate_pct=0.12)},
    {'id': 'demolitionist','name': 'Sprengmeister',    'desc': 'Explosivmunition (70)','rarity': 'rare', 'color': (255, 130, 50), 'apply': lambda p: p._art_apply(explosive=70)},
    {'id': 'bloodthirst', 'name': 'Blutdurst',         'desc': '+12% Lebensraub, +5 HP/Kill','rarity': 'rare', 'color': (220, 60, 80), 'apply': lambda p: p._art_apply(lifesteal=0.12, heal_on_kill=5)},
    {'id': 'war_chest',   'name': 'Kriegskasse',       'desc': '+2 Muenzen/Kill, +15% Gem','rarity': 'rare', 'color': (240, 200, 80),'apply': lambda p: p._art_apply(coin_bonus=2, gem_find=0.15)},
    {'id': 'triple_shot', 'name': 'Dreifachschuss',    'desc': '+2 Schuss pro Seite',  'rarity': 'rare', 'color': (255, 210, 100),'apply': lambda p: p._art_apply(extra_shots=2)},
    {'id': 'piercer',     'name': 'Durchschlag',       'desc': '+2 Durchschlag, +10% Tempo','rarity': 'rare', 'color': (150, 180, 210),'apply': lambda p: p._art_apply(pierce=2, proj_speed_pct=0.10)},
    {'id': 'kraken_armor','name': 'Kraken-Panzer',     'desc': '+40 Schild',           'rarity': 'rare', 'color': (90, 200, 210), 'apply': lambda p: p._art_apply(max_shield=40)},
    {'id': 'reaper',      'name': 'Schnitter',         'desc': '+12% Krit, +40% Krit-Schaden','rarity': 'rare', 'color': (230, 90, 130),'apply': lambda p: p._art_apply(crit_chance=0.12, crit_mult=0.40)},

    # ---------- Epic ----------
    {'id': 'hell_broadside','name': 'Hoellenbroadside','desc': '+2 Schuss, +12% Schaden','rarity': 'epic', 'color': (255, 100, 80), 'apply': lambda p: p._art_apply(extra_shots=2, damage_pct=0.12)},
    {'id': 'phoenix',     'name': 'Phoenixfeder',      'desc': 'Wiederbelebung (1x)',  'rarity': 'epic', 'color': (255, 160, 60), 'apply': lambda p: p._art_apply(revive=1)},
    {'id': 'storm_lord',  'name': 'Sturmherr',         'desc': '+25% Tempo, +15% Ausw., +12% FR','rarity': 'epic', 'color': (100, 230, 210),'apply': lambda p: p._art_apply(speed_pct=0.25, evasion=0.15, fire_rate_pct=0.12)},
    {'id': 'titan_hull',  'name': 'Titanenrumpf',      'desc': '+60 HP, +20% Verteid., +2 Rep','rarity': 'epic', 'color': (150, 200, 240),'apply': lambda p: p._art_apply(max_health=60, defense=0.20, regen=2.0)},
    {'id': 'marksman',    'name': 'Meisterschuetze',   'desc': '+20% Krit, +80% Krit-Schaden','rarity': 'epic', 'color': (255, 110, 140),'apply': lambda p: p._art_apply(crit_chance=0.20, crit_mult=0.80)},
    {'id': 'soul_reaver', 'name': 'Seelenraeuber',     'desc': '+18% Lebensraub, +8 HP/Kill','rarity': 'epic', 'color': (200, 60, 110),'apply': lambda p: p._art_apply(lifesteal=0.18, heal_on_kill=8)},
    {'id': 'thunder_ball','name': 'Donnerkugeln',      'desc': 'Explosion (90), +2 Durchschlag','rarity': 'epic', 'color': (255, 150, 60),'apply': lambda p: p._art_apply(explosive=90, pierce=2)},
    {'id': 'gold_rush',   'name': 'Goldrausch',        'desc': '+30% XP, +25% Gem, +3 Muenzen','rarity': 'epic', 'color': (255, 215, 90),'apply': lambda p: p._art_apply(xp_pct=0.30, gem_find=0.25, coin_bonus=3)},

    # ---------- Legendary ----------
    {'id': 'leviathan',   'name': 'Leviathan-Herz',    'desc': '+80 HP, +30 Schild, +12% Verteid.','rarity': 'legendary', 'color': (255, 200, 80),'apply': lambda p: p._art_apply(max_health=80, max_shield=30, regen=2.5, defense=0.12)},
    {'id': 'armageddon',  'name': 'Weltenbrand',       'desc': '+30% Schaden, Explosion (100), +2 Schuss','rarity': 'legendary', 'color': (255, 150, 50),'apply': lambda p: p._art_apply(damage_pct=0.30, explosive=100, extra_shots=2)},
    {'id': 'poseidon',    'name': 'Poseidons Zorn',    'desc': '+2 Schuss, +2 Durchschlag, +15% Krit','rarity': 'legendary', 'color': (90, 210, 255),'apply': lambda p: p._art_apply(extra_shots=2, pierce=2, proj_speed_pct=0.20, crit_chance=0.15)},
    {'id': 'captains_curse','name': 'Fluch des Kapitaens','desc': '+40% Schaden, +25% Lebensraub','rarity': 'legendary', 'color': (200, 70, 90),'apply': lambda p: p._art_apply(damage_pct=0.40, crit_chance=0.15, lifesteal=0.25, defense=-0.10)},
    {'id': 'eternal_storm','name': 'Ewiger Sturm',     'desc': '+30% Tempo, +20% FR, Wiederbeleb.','rarity': 'legendary', 'color': (120, 240, 220),'apply': lambda p: p._art_apply(speed_pct=0.30, fire_rate_pct=0.20, evasion=0.15, revive=1)},
]


pg.font.init()

font: pg.font.FontType = pg.font.SysFont("Arial", 100)


def white2transparent(surf: pg.Surface):
    w, h = surf.get_size()

    for x in range(w):
        for y in range(h):
            if surf.get_at((x, y)) == pg.Color("white"):
                surf.set_at((x, y), pg.Color(0, 0, 0, 0))


def tint_segel(surf: pg.Surface, color: pg.Color):
    """Färbt helle Bereiche (Segel) in der angegebenen Farbe"""
    result = surf.copy()
    w, h = result.get_size()
    
    for x in range(w):
        for y in range(h):
            pixel = result.get_at((x, y))
            # Helle Pixel (Segel) einfärben - wenn R,G,B alle hoch sind
            if pixel.a > 0 and pixel.r > 200 and pixel.g > 200 and pixel.b > 200:
                # Mische die Farbe mit dem Original
                new_color = pg.Color(
                    min(255, (pixel.r + color.r) // 2),
                    min(255, (pixel.g + color.g) // 2),
                    min(255, (pixel.b + color.b) // 2),
                    pixel.a
                )
                result.set_at((x, y), new_color)
    return result


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


# ==================== INSEL / REKRUTIERUNG (Stage 1) ====================
PIRATE_NAMES = [
    "Blackbeard", "Anne", "Calico Jack", "Mary", "Bartholomew", "Henry",
    "Grace", "Ching", "Roberts", "Morgan", "Hook", "Silver", "Flint",
    "Sparrow", "Barbossa", "Vane", "Rackham", "Bonny", "Teach", "Kidd",
]

# Schiffs-Katalog: class_name, Multiplikatoren, Preis (Gems)
SHIP_CATALOG = [
    {"class_name": "Sloop",      "hp_mult": 1.0, "speed_mult": 1.15, "dmg_mult": 0.90, "price": 0,   "sprite_key": "default"},
    {"class_name": "Brigantine", "hp_mult": 1.3, "speed_mult": 1.00, "dmg_mult": 1.10, "price": 50,  "sprite_key": "default"},
    {"class_name": "Fregatte",   "hp_mult": 1.7, "speed_mult": 0.90, "dmg_mult": 1.30, "price": 110, "sprite_key": "default"},
    {"class_name": "Galeone",    "hp_mult": 2.2, "speed_mult": 0.78, "dmg_mult": 1.55, "price": 210, "sprite_key": "default"},
]


class CrewRecruit:
    """Ein anheuerbarer Crew-Kandidat auf einer Insel."""
    LEVEL_NAMES = {1: "Green", 2: "Veteran", 3: "Master"}
    LEVEL_PRICE = {1: 15, 2: 40, 3: 80}

    def __init__(self, role, name, level, price):
        self.role = role
        self.name = name
        self.level = level
        self.price = price

    @classmethod
    def random(cls):
        role = random.choice(list(CrewMember.ROLES.keys()))
        name = random.choice(PIRATE_NAMES)
        level = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        return cls(role, name, level, cls.LEVEL_PRICE[level])


class ShipOffer:
    """Ein kaufbares Schiff in der Werft."""
    def __init__(self, spec):
        self.class_name = spec["class_name"]
        self.hp_mult = spec["hp_mult"]
        self.speed_mult = spec["speed_mult"]
        self.dmg_mult = spec["dmg_mult"]
        self.price = spec["price"]
        self.sprite_key = spec.get("sprite_key", "default")

    def to_fleet_entry(self):
        return {
            "class_name": self.class_name,
            "hp_mult": self.hp_mult,
            "speed_mult": self.speed_mult,
            "dmg_mult": self.dmg_mult,
            "sprite_key": self.sprite_key,
        }


class IslandMap:
    """Beschreibt eine begehbare Insel: Welt-Anker + Surface + Maske + Props."""
    def __init__(self, island_id, anchor_topleft, surface, mask):
        self.id = island_id                  # -1 = Hauptinsel, sonst Index in extra_islands
        self.anchor = pg.Vector2(anchor_topleft)
        self.surface = surface
        self.mask = mask
        self.interactables = []              # list[Interactable]

    def is_land(self, world_pos):
        lx = int(world_pos.x - self.anchor.x)
        ly = int(world_pos.y - self.anchor.y)
        if 0 <= lx < self.surface.get_width() and 0 <= ly < self.surface.get_height():
            return bool(self.mask.get_at((lx, ly)))
        return False


class Interactable:
    """Ein NPC/Gebäude an Land, mit dem der Spieler per E interagiert."""
    def __init__(self, kind, pos, payload):
        self.kind = kind          # "recruit" | "shipyard"
        self.pos = pg.Vector2(pos)
        self.payload = payload    # list[CrewRecruit] oder list[ShipOffer]
        self.radius = 72
        self.bob_timer = random.uniform(0.0, 3.0)

    def update(self, dt_seconds):
        self.bob_timer += dt_seconds

    def draw(self, surface, offset):
        sx = int(self.pos.x - offset.x)
        sy = int(self.pos.y - offset.y)
        bob = int(math.sin(self.bob_timer * 2.5) * 3)
        # Boden-Schatten
        shadow = pg.Surface((40, 14), pg.SRCALPHA)
        pg.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (sx - 20, sy + 14))
        if self.kind == "recruit":
            self._draw_recruit(surface, sx, sy + bob)
        else:
            self._draw_shipyard(surface, sx, sy + bob)

    def _draw_recruit(self, surface, sx, sy):
        # Einfacher Pirat-NPC
        pg.draw.rect(surface, (50, 80, 130), (sx - 9, sy - 4, 18, 22), border_radius=4)   # Körper
        pg.draw.rect(surface, (35, 60, 100), (sx - 9, sy - 4, 18, 22), 1, border_radius=4)
        pg.draw.circle(surface, (235, 200, 165), (sx, sy - 12), 8)                          # Kopf
        pg.draw.circle(surface, (60, 45, 35), (sx, sy - 12), 8, 1)
        pg.draw.rect(surface, (185, 55, 55), (sx - 8, sy - 18, 16, 5), border_radius=2)     # Bandana
        pg.draw.circle(surface, (25, 25, 25), (sx - 3, sy - 12), 1)
        pg.draw.circle(surface, (25, 25, 25), (sx + 3, sy - 12), 1)
        # "!" Sprechblase
        pulse = abs(math.sin(self.bob_timer * 4))
        pg.draw.circle(surface, (255, 230, 120), (sx, sy - 30), 8)
        ex = self._exclaim_font().render("!", True, (60, 40, 0))
        surface.blit(ex, ex.get_rect(center=(sx, sy - 30)))

    def _draw_shipyard(self, surface, sx, sy):
        # Werft-Hütte
        pg.draw.polygon(surface, (95, 62, 38), [(sx - 24, sy - 12), (sx + 24, sy - 12), (sx, sy - 32)])  # Dach
        pg.draw.rect(surface, (130, 92, 58), (sx - 20, sy - 12, 40, 30), border_radius=3)                 # Wand
        pg.draw.rect(surface, (70, 48, 28), (sx - 20, sy - 12, 40, 30), 2, border_radius=3)
        pg.draw.rect(surface, (55, 38, 22), (sx - 6, sy + 2, 12, 16), border_radius=2)                    # Tür
        # Anker-Symbol
        pg.draw.circle(surface, (220, 220, 230), (sx, sy - 6), 3, 1)
        pg.draw.line(surface, (220, 220, 230), (sx, sy - 4), (sx, sy + 8), 2)
        pg.draw.line(surface, (220, 220, 230), (sx - 6, sy + 6), (sx + 6, sy + 6), 2)

    _ex_font = None

    @classmethod
    def _exclaim_font(cls):
        if cls._ex_font is None:
            cls._ex_font = pg.font.SysFont("Arial", 12, bold=True)
        return cls._ex_font


class Cannonball:
    """Eine Kanonenkugel die vom Spieler oder NPC abgefeuert wird"""
    def __init__(self, pos, direction, is_enemy=False):
        self.pos = pg.Vector2(pos)
        self.direction = pg.Vector2(direction)
        self.speed = 500  # Pixel pro Sekunde
        self.radius = 10
        self.lifetime = 3.0  # Sekunden bis Kugel verschwindet
        self.age = 0
        self.is_dead = False
        self.is_enemy = is_enemy  # True = von NPC, False = vom Spieler
        self.boss_damage = 10  # Standard-Schaden (wird bei Boss überschrieben)
        # Trail für visuellen Effekt
        self.trail = []
        self.trail_timer = 0
    
    def update(self, dt_seconds):
        # Trail-Position speichern
        self.trail_timer += dt_seconds
        if self.trail_timer >= 0.02:  # Alle 20ms
            self.trail_timer = 0
            self.trail.append((pg.Vector2(self.pos), self.age))
            # Trail auf max 15 Positionen begrenzen
            if len(self.trail) > 15:
                self.trail.pop(0)
        
        self.pos += self.direction * self.speed * dt_seconds
        self.age += dt_seconds
        if self.age >= self.lifetime:
            self.is_dead = True
    
    def draw(self, surface, offset):
        screen_pos = self.pos - offset
        sx, sy = int(screen_pos.x), int(screen_pos.y)
        
        # Trail zeichnen (vereinfacht - keine SRCALPHA Surfaces)
        for i, (trail_pos, trail_age) in enumerate(self.trail):
            trail_screen = trail_pos - offset
            size = int(self.radius * 0.3 * (i / len(self.trail)))
            if size > 0:
                if self.is_enemy:
                    pg.draw.circle(surface, (200, 100, 50), (int(trail_screen.x), int(trail_screen.y)), size)
                else:
                    pg.draw.circle(surface, (150, 150, 100), (int(trail_screen.x), int(trail_screen.y)), size)
        
        if self.is_enemy:
            # Feuer-Effekt (vereinfacht - kein Glow-Surface)
            pg.draw.circle(surface, pg.Color(200, 80, 30), (sx, sy), self.radius)
            pg.draw.circle(surface, pg.Color(255, 150, 50), (sx, sy), self.radius - 3)
        else:
            # Goldene Kugel für Spieler (vereinfacht)
            pg.draw.circle(surface, pg.Color(80, 80, 80), (sx, sy), self.radius)
            pg.draw.circle(surface, pg.Color(150, 130, 80), (sx, sy), self.radius - 2)
            pg.draw.circle(surface, pg.Color(255, 255, 200), (sx - 2, sy - 2), 3)


class NPCShip:
    """Ein NPC-Schiff das zu Zielpunkten fährt"""
    def __init__(self, pos, schiff_ohne_segel, schiff_mit_segel, segel_farbe, world_size):
        self.pos = pg.Vector2(pos)
        self.richtung = 0
        self.moving = True  # Immer am Fahren
        self.segel_farbe = segel_farbe
        self.world_size = world_size
        
        # Schiff-Bilder mit gefärbtem Segel
        self.schiff_ohne = schiff_ohne_segel
        self.schiff_mit = tint_segel(schiff_mit_segel, segel_farbe)
        
        # Boss-Varianten (größere Bilder)
        self.schiff_mit_boss = self._build_boss_sprite(self.schiff_mit)
        
        # Alle 8 Rotationen vorberechnen (PERFORMANCE!)
        self._cached_images = []
        self._cached_masks = []
        self._cached_boss_images = []
        self._cached_boss_masks = []
        for r in range(8):
            img = pg.transform.rotate(self.schiff_mit, r * -45)
            self._cached_images.append(img)
            self._cached_masks.append(pg.mask.from_surface(img))
            boss_img = pg.transform.rotate(self.schiff_mit_boss, r * -45)
            self._cached_boss_images.append(boss_img)
            self._cached_boss_masks.append(pg.mask.from_surface(boss_img))
        
        # Ziel-System
        self.target = None
        
        # Geschwindigkeit (Pixel pro Sekunde)
        self.speed = 100
        
        # Leben
        self.health = 100
        self.max_health = 100
        self.is_dead = False
        self.respawn_timer = 0
        self.respawn_duration = 10.0  # 10 Sekunden bis Respawn
        
        # Schießen
        self.shoot_cooldown = random.uniform(0, 2.0)  # Zufälliger Start-Cooldown
        self.shoot_cooldown_duration = 1.5  # 1.5 Sekunden zwischen Schüssen
        self.shoot_range = 400  # Maximale Schussreichweite
        
        # Boss-System
        self.is_boss = False
        self.boss_aggro_range = 400  # Reichweite um Spieler zu verfolgen
        self.boss_aggroed = False  # Wird True wenn Spieler in Range war
        self.boss_damage = 10  # Normaler Schaden
        self.hit_radius = 46  # Feste, einfache Hitbox (weltkoordinaten)
        self.can_respawn = True
        self.is_boss_minion = False
        
        # Insel-Zuordnung (wird später gesetzt)
        self.home_island = 0
        
        # Erstes Ziel setzen
        self.pick_new_target()

    def _build_boss_sprite(self, base_ship):
        """Erstellt eine markantere Boss-Variante mit Emblem und Kontur."""
        boss_ship = pg.transform.smoothscale(
            base_ship,
            (int(base_ship.get_width() * 1.85), int(base_ship.get_height() * 1.85))
        ).convert_alpha()

        # Dunklere, aggressivere Grundstimmung
        darken = pg.Surface(boss_ship.get_size(), pg.SRCALPHA)
        darken.fill((150, 120, 120, 255))
        boss_ship.blit(darken, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

        # Rote Kontur auf Basis der sichtbaren Sprite-Form
        mask = pg.mask.from_surface(boss_ship)
        outline = mask.outline()
        if len(outline) > 2:
            outline_fx = pg.Surface(boss_ship.get_size(), pg.SRCALPHA)
            pg.draw.lines(outline_fx, (255, 70, 50, 185), True, outline, 2)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                shifted = [(x + dx, y + dy) for x, y in outline]
                pg.draw.lines(outline_fx, (255, 40, 30, 80), True, shifted, 1)
            boss_ship.blit(outline_fx, (0, 0))

        # Kleines Kronen-Emblem als Boss-Kennung
        cx = boss_ship.get_width() // 2
        cy = max(10, boss_ship.get_height() // 4)
        crown = [
            (cx - 9, cy + 6), (cx - 7, cy - 3), (cx - 2, cy + 2),
            (cx + 1, cy - 5), (cx + 4, cy + 2), (cx + 9, cy - 3), (cx + 11, cy + 6)
        ]
        pg.draw.polygon(boss_ship, (255, 210, 90), crown)
        pg.draw.polygon(boss_ship, (110, 70, 20), crown, 1)
        pg.draw.rect(boss_ship, (220, 170, 70), (cx - 9, cy + 6, 20, 3))

        return boss_ship
    
    def pick_new_target(self):
        """Wählt ein neues zufälliges Ziel im 1000 Pixel Radius"""
        # Zufälliger Winkel und Distanz
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(100, 1000)  # Zwischen 100 und 1000 Pixel
        
        # Neues Ziel relativ zur aktuellen Position
        offset_x = distance * pg.math.Vector2(1, 0).rotate_rad(angle).x
        offset_y = distance * pg.math.Vector2(1, 0).rotate_rad(angle).y
        self.target = self.pos + pg.Vector2(offset_x, offset_y)
        self.moving = True
        
        # Richtung zum Ziel berechnen
        self.update_direction_to_target()
    
    def update_direction_to_target(self):
        """Berechnet die beste Richtung zum Ziel (8 Richtungen)"""
        if self.target is None:
            return
        
        direction = self.target - self.pos
        if direction.length() < 1:
            return
        
        # Winkel berechnen (0 = unten, im Uhrzeigersinn)
        angle = direction.angle_to(pg.Vector2(0, 1))
        
        # Auf 8 Richtungen runden (0-7)
        # Jede Richtung ist 45 Grad
        self.richtung = round(angle / 45) % 8
    
    def update(self, dt, world_size, player_pos=None, insel_mask=None, insel_surf=None, rocks=None, extra_islands=None):
        # dt in Sekunden
        dt_seconds = dt / 1000.0
        
        # Alte Position speichern
        old_pos = self.pos.copy()
        old_richtung = self.richtung
        
        # Immer fahren!
        self.moving = True
        
        # Ausweich-Timer initialisieren falls nicht vorhanden
        if not hasattr(self, 'avoid_timer'):
            self.avoid_timer = 0
            self.avoid_direction = 0
        
        # Boss-Aggro: aggroed wenn Spieler nah, de-aggroed wenn Spieler weit weg
        if self.is_boss and player_pos is not None:
            dist_to_player = self.pos.distance_to(player_pos)
            if dist_to_player < self.boss_aggro_range:
                self.boss_aggroed = True
            elif dist_to_player > self.boss_aggro_range * 2.5:
                self.boss_aggroed = False  # De-aggro wenn Spieler weit weg
        
        # Spieler verfolgen
        if player_pos is not None:
            if self.is_boss and self.boss_aggroed:
                # Boss verfolgt solange aggroed
                self.target = player_pos
            elif self.avoid_timer <= 0:
                self.target = player_pos
        
        # Ausweich-Timer runterzählen
        if self.avoid_timer > 0:
            self.avoid_timer -= dt_seconds
            # Während Ausweichen: in Ausweich-Richtung fahren
            self.richtung = self.avoid_direction
        elif self.target is not None:
            # Normal zum Ziel fahren
            self.update_direction_to_target()
        
        # Bewegung in aktuelle Richtung
        self.pos += richtungen[self.richtung] * dt_seconds * self.speed
        
        # Kollision prüfen und umfahren
        collision = False
        collision_point = None
        
        # Gecachte Image und Mask verwenden (keine Neuberechnung!)
        npc_img = self.get_image()
        npc_mask = self.get_mask()
        npc_rect = npc_img.get_rect(center=self.pos)
        
        # Kollision mit Haupt-Insel prüfen
        if insel_mask is not None and insel_surf is not None:
            offset = (npc_rect.left, npc_rect.top)
            if insel_mask.overlap(npc_mask, offset):
                collision = True
                insel_w, insel_h = insel_surf.get_size()
                collision_point = pg.Vector2(insel_w // 2, insel_h // 2)
        
        # Kollision mit Extra-Inseln prüfen (gecachte Masken)
        if not collision and extra_islands is not None:
            for island_pos, island_scale, island_img, island_mask in extra_islands:
                island_rect = island_img.get_rect(center=island_pos)
                offset = (npc_rect.left - island_rect.left, npc_rect.top - island_rect.top)
                if island_mask.overlap(npc_mask, offset):
                    collision = True
                    collision_point = pg.Vector2(island_pos)
                    break
        
        # Kollision mit Steinen prüfen (gecachte Masken + Distance Culling)
        if not collision and rocks is not None:
            for rock_pos, rock_img, rock_mask in rocks:
                if self.pos.distance_squared_to(rock_pos) > 90000:  # 300px
                    continue
                rock_rect = rock_img.get_rect(center=rock_pos)
                offset = (npc_rect.left - rock_rect.left, npc_rect.top - rock_rect.top)
                if rock_mask.overlap(npc_mask, offset):
                    collision = True
                    collision_point = pg.Vector2(rock_pos)
                    break
        
        # Bei Kollision: zurücksetzen und umfahren
        if collision:
            self.pos = old_pos
            
            # Zusätzlich: Vom Hindernis weg drücken (verhindert Steckenbleiben)
            if collision_point is not None:
                push_dir = self.pos - collision_point
                if push_dir.length() > 0:
                    push_dir = push_dir.normalize()
                    self.pos += push_dir * dt_seconds * 50  # Langsam wegdrücken
            
            # Neue Ausweich-Richtung nur setzen wenn Timer abgelaufen
            if self.avoid_timer <= 0:
                # Berechne welche Seite zum Umfahren besser ist
                if collision_point is not None and self.target is not None:
                    # Vektor vom Hindernis zum Schiff
                    to_ship = self.pos - collision_point
                    # Vektor vom Schiff zum Ziel
                    to_target = self.target - self.pos
                    
                    # Kreuzprodukt um zu bestimmen ob links oder rechts umfahren
                    cross = to_ship.x * to_target.y - to_ship.y * to_target.x
                    
                    if cross > 0:
                        # Links umfahren (mehr drehen für besseres Ausweichen)
                        self.avoid_direction = (old_richtung + 3) % 8
                    else:
                        # Rechts umfahren
                        self.avoid_direction = (old_richtung - 3) % 8
                else:
                    # Zufällige Richtung wenn kein Ziel
                    self.avoid_direction = (old_richtung + 4) % 8
                
                # Ausweichen für 1-2 Sekunden
                self.avoid_timer = 1.5
        
        # Schießen
        self.shoot_cooldown -= dt_seconds
        return None  # Wird später für Projektil-Rückgabe verwendet
    
    def try_shoot(self, player_pos):
        """Versucht auf den Spieler zu schießen, gibt Cannonball zurück oder None"""
        if self.is_dead:
            return None
        
        if self.shoot_cooldown > 0:
            return None
        
        # Prüfe Distanz zum Spieler
        dist = self.pos.distance_to(player_pos)
        if dist > self.shoot_range:
            return None
        
        # Schießen!
        self.shoot_cooldown = self.shoot_cooldown_duration
        
        # Richtung zum Spieler
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            return None
        
        ball = Cannonball(self.pos, direction, is_enemy=True)
        ball.boss_damage = self.boss_damage  # Schaden mitgeben
        return ball
    
    def get_image(self):
        # Gecachte vorberechnete Rotation verwenden
        if self.is_boss:
            return self._cached_boss_images[self.richtung]
        return self._cached_images[self.richtung]
    
    def get_mask(self):
        """Gibt die gecachte Maske zurück"""
        if self.is_boss:
            return self._cached_boss_masks[self.richtung]
        return self._cached_masks[self.richtung]
    
    def get_rect(self):
        img = self.get_image()
        return img.get_rect(center=self.pos)
    
    def respawn(self, world_size, player_pos, insel_size):
        """Respawnt das NPC-Schiff an einer neuen Position"""
        insel_w, insel_h = insel_size
        
        while True:
            x = random.randint(-int(world_size.x // 2), int(world_size.x // 2))
            y = random.randint(-int(world_size.y // 2), int(world_size.y // 2))
            pos = pg.Vector2(x, y)
            
            # Nicht zu nah am Spieler
            if pos.distance_to(player_pos) < 500:
                continue
            
            # Nicht auf der Insel
            if 0 < x < insel_w and 0 < y < insel_h:
                continue
            
            break
        
        self.pos = pos
        self.health = 100
        self.is_dead = False
        self.respawn_timer = 0
        self.pick_new_target()
    
    def respawn_near_island(self, insel_size, player_pos, difficulty=1.0):
        """Respawnt das NPC-Schiff in der Nähe des Spielers mit Schwierigkeits-Skalierung"""
        insel_w, insel_h = insel_size
        
        # Spawn in einem Ring um den Spieler herum (600-1200 Pixel entfernt)
        while True:
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(600, 1200)
            x = player_pos.x + distance * pg.math.Vector2(1, 0).rotate_rad(angle).x
            y = player_pos.y + distance * pg.math.Vector2(1, 0).rotate_rad(angle).y
            pos = pg.Vector2(x, y)
            
            # Nicht auf der Haupt-Insel
            if 0 < x < insel_w and 0 < y < insel_h:
                continue
            
            # Nicht zu nah am Spieler
            if pos.distance_to(player_pos) < 400:
                continue
            
            break
        
        self.pos = pos
        
        # Boss-Chance reduziert: 1% bis max 2.5%
        boss_chance = 0.01 + min(0.015, difficulty * 0.003)
        self.is_boss = random.random() < boss_chance
        self.boss_aggroed = False
        
        if self.is_boss:
            # Boss: deutlich mehr HP, aber seltenere Spawns
            self.health = int(900 * difficulty)
            self.max_health = int(900 * difficulty)
            self.shoot_cooldown_duration = max(0.3, 1.0 / difficulty)
            self.speed = int(110 * min(2.4, 0.8 + difficulty * 0.25))
            self.shoot_range = int(450 + difficulty * 15)
            self.boss_damage = int(25 * (1 + (difficulty - 1) * 0.3))  # Schaden skaliert
            self.boss_aggro_range = int(450 + difficulty * 20)
            self.respawn_duration = max(10.0, 20.0 - difficulty)  # Schnellerer Respawn
            self.hit_radius = 66
            self.is_boss_minion = False
            self.can_respawn = True
        else:
            # Normales Schiff
            self.health = int(100 * difficulty)
            self.max_health = int(100 * difficulty)
            self.shoot_cooldown_duration = max(0.5, 1.5 / difficulty)
            self.speed = int(100 * min(3.2, 0.8 + difficulty * 0.45))
            self.shoot_range = int(400 + difficulty * 10)
            self.boss_damage = int(10 * (1 + (difficulty - 1) * 0.25))  # Schaden skaliert
            self.respawn_duration = max(5.0, 10.0 - difficulty * 0.5)  # Schnellerer Respawn
            self.hit_radius = 46
            self.is_boss_minion = False
            self.can_respawn = True
        
        self.is_dead = False
        self.respawn_timer = 0
        self.shoot_cooldown = random.uniform(0, 1.0)
        self.pick_new_target()
    
    def scale_to_difficulty(self, difficulty):
        """Skaliert die Stats eines lebenden NPCs zur aktuellen Schwierigkeit"""
        if self.is_boss:
            new_max = int(900 * difficulty)
            self.shoot_cooldown_duration = max(0.3, 1.0 / difficulty)
            self.speed = int(110 * min(2.4, 0.8 + difficulty * 0.25))
            self.shoot_range = int(450 + difficulty * 15)
            self.boss_damage = int(25 * (1 + (difficulty - 1) * 0.3))
            self.boss_aggro_range = int(450 + difficulty * 20)
            self.hit_radius = 66
        else:
            new_max = int(100 * difficulty)
            self.shoot_cooldown_duration = max(0.5, 1.5 / difficulty)
            self.speed = int(100 * min(3.2, 0.8 + difficulty * 0.45))
            self.shoot_range = int(400 + difficulty * 10)
            self.boss_damage = int(10 * (1 + (difficulty - 1) * 0.25))
            self.hit_radius = 46
        
        # HP proportional skalieren (behalte aktuelles HP-Verhältnis)
        if self.max_health > 0 and new_max > self.max_health:
            hp_ratio = self.health / self.max_health
            self.max_health = new_max
            self.health = int(new_max * hp_ratio)


class PlayState(State):
    def __init__(self):
        # text
        self.text: pg.Surface = font.render("Play", True, "black")
        self.col_text: pg.Surface = font.render("Collision", True, "black")
        self.ncol_text: pg.Surface = font.render("No Collision", True, "black")
        
        # Weltgröße
        self.world_size = pg.Vector2(4000, 4000)
        
        # load insel
        self.insel = pg.image.load("assets/Insel.png").convert_alpha()
        self.insel = pg.transform.scale2x(self.insel)
        self.insel = pg.transform.scale2x(self.insel)
        self.insel = pg.transform.scale2x(self.insel)
        self.insel = pg.transform.scale2x(self.insel)  # 16x größer
        self.insel = pg.transform.scale_by(self.insel, 1.5)  # noch größer
        self.mask_insel=pg.mask.from_surface(surface=self.insel)

        # load schiff
        self.schiff1 = pg.image.load("assets/Schiff 1.png").convert_alpha()
        white2transparent(self.schiff1)
        self.schiff1 = pg.transform.scale2x(self.schiff1)
        self.schiff1 = pg.transform.scale_by(self.schiff1, 1.5)  # größer

        # mit Segel
        self.schiff2 = pg.image.load("assets/Schiff 2.png").convert_alpha()
        white2transparent(self.schiff2)
        self.schiff2 = pg.transform.scale2x(self.schiff2)
        self.schiff2 = pg.transform.scale_by(self.schiff2, 1.5)  # größer
        self.mask_schiff2=pg.mask.from_surface(surface=self.schiff2)

        # Startposition außerhalb der Insel (Insel ist jetzt viel größer)
        insel_w, insel_h = self.insel.get_size()
        self.cords_schiff1 = pg.Vector2(insel_w + 200, insel_h // 2)
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

        # Steine (zwei Varianten) - Basis-Bilder laden
        self.rock_base_imgs = []
        for i in [1, 2]:
            img = pg.image.load(f"assets/Stein {i}.png").convert_alpha()
            self.rock_base_imgs.append(img)
        
        # Zusätzliche kleine Inseln ZUERST generieren (bevor Steine)
        self.extra_islands = self.generate_extra_islands()
        
        # Steine zufällig generieren (Position, Typ, pre-skaliertes Bild)
        self.rocks = self.generate_rocks()
        
        # Alle Inseln sammeln - ABER nur Hauptinsel spawnt Schiffe
        insel_w, insel_h = self.insel.get_size()
        all_islands = [(pg.Vector2(insel_w // 2, insel_h // 2), True)]  # Nur Hauptinsel
        self.island_ship_status = all_islands  # Tracking welche Inseln noch Schiffe haben
        
        # NPC-Schiffe generieren (pro Insel)
        self.npc_ships = self.generate_npc_ships()
    
        # camera
        self.camera_pos = pg.Vector2(self.cords_schiff1)
        self.zoom = 1.0
        self.base_zoom = 1.0
        self.move_zoom = 1.1
        self.zoom_speed = 5.0
        self.cam_lerp = 8.0
        
        # Leben-System
        self.health = 100  # 100%
        self.is_dead = False
        self.death_timer = 0
        self.death_duration = 5.0  # 5 Sekunden (damit Highscore lesbar)
        
        # Kollisions-Cooldown (damit nicht sofort alles Leben weg ist)
        self.damage_cooldown = 0
        self.damage_cooldown_duration = 0.5  # 0.5 Sekunden zwischen Schaden
        
        # Schiff-Schadensmodell (Löcher und Feuer)
        self.ship_damage_model = ShipDamageModel(max_health=100)
        
        # Crew-System
        self.crew = ShipCrew()
        
        # Kanonenkugeln
        self.cannonballs = []
        self.shoot_cooldown = 0
        self.shoot_cooldown_duration = 0.45  # 0.45 Sekunden zwischen Schüssen
        
        # EXP-System
        self.exp = 0
        self.exp_to_level = 100  # EXP für nächstes Level
        self.level = 1
        
        # Skill-Punkte und Upgrades
        self.skill_points = 0
        self.speed_level = 0  # Boot-Geschwindigkeit
        self.fire_rate_level = 0  # Schussgeschwindigkeit
        self.regen_level = 0  # Reparatur-Level
        self.max_health_level = 0  # Maximale Leben
        self.damage_level = 0  # Kugel-Schaden
        
        # Kill-Counter
        self.kills = 0

        # Muenzen: Pro-Run-Waehrung fuer Rekrutierung & Werft (wird jeden Run zurueckgesetzt)
        self.coins = 0

        # Survival-Zeit (für Schwierigkeits-Skalierung)
        self.survival_time = 0
        
        # Highscore
        self.highscore = load_highscore()
        self.is_new_highscore = False
        
        # Große Minimap (Pause-Modus)
        self.show_big_minimap = False
        self.map_drag_offset = pg.Vector2(0, 0)  # Offset für Karten-Drag
        self.map_dragging = False  # Ob gerade gedraggt wird
        self.map_drag_start = pg.Vector2(0, 0)  # Startposition des Drags
        self.map_zoom = 1.0       # Zoom-Level der Weltkarte (0.3 – 3.0)
        self.map_zoom_target = 1.0
        self.map_hover_info = None  # Tooltip-Info beim Hovern
        
        # Fog of War - Erkundete Bereiche
        # Grid-basiert: jede Zelle ist 100x100 Pixel
        self.fog_cell_size = 100
        self.explored_cells = set()  # Set von (grid_x, grid_y) Tupeln
        
        # Basis-Werte
        self.base_speed = 300  # Vorwärts
        self.base_speed_back = 150  # Rückwärts
        self.base_shoot_cooldown = 0.45
        self.base_regen = 0  # Legacy-Feld (keine passive Regeneration mehr)
        self.base_repair_rate = 2.5  # HP/s beim aktiven Reparieren
        self.repair_hold_time = 0.0
        self.repair_channel_time = 0.35  # Reparatur startet nach kurzem Channel
        self.repairing = False
        self.base_max_health = 100
        self.base_damage = 25
        
        # Gem-System (persistent über Runs)
        self.total_gems = load_gems()  # Gesamtanzahl aus Datei laden
        self.gems = self.generate_gems()  # Gems für diesen Run
        self.gem_spawn_timer = 0
        self.gem_spawn_interval = 30.0  # Alle 30 Sekunden Chance auf neuen Gem

        # Kisten/Artefakte (nur fuer den aktuellen Run)
        self.crates = self.generate_crates()
        self.crate_spawn_timer = 0
        self.crate_spawn_interval = 30.0  # Alle 30 Sekunden eine neue Kiste
        self._clear_crate_effects()

        # Fonts cachen (Performance)
        self.font_main = pg.font.SysFont("Arial", 24)
        self.font_small = pg.font.SysFont("Arial", 18)
        self.font_title = pg.font.SysFont("Arial", 36)
        self.font_big = pg.font.SysFont("Arial", 48)
        
        # Piraten-Charakter Animationen laden
        pirate_sheet = pg.image.load("assets/pirate.png").convert_alpha()
        # Frame-Größe aus dem Bild (ca. 32x32 pro Frame, 5 Frames pro Animation)
        frame_w, frame_h = 32, 32
        
        # Walk Animation (9. Reihe, unterste Reihe)
        self.walk_frames = []
        for i in range(5):
            frame = pirate_sheet.subsurface(pg.Rect(i * frame_w, 8 * frame_h, frame_w, frame_h))
            frame = pg.transform.scale2x(frame)  # 2x größer
            self.walk_frames.append(frame)
        
        # Idle Animation (7. Reihe)
        self.idle_frames = []
        for i in range(4):
            frame = pirate_sheet.subsurface(pg.Rect(i * frame_w, 6 * frame_h, frame_w, frame_h))
            frame = pg.transform.scale2x(frame)  # 2x größer
            self.idle_frames.append(frame)

        # Piraten-Sprite wie im Quit-Dialog (fuer den Avatar an Land)
        self.pirate_frames = self._load_pirate_frames(scale=1)

        # Charakter-Status
        self.on_foot = False  # Ob Spieler zu Fuß ist
        self.player_foot_pos = pg.Vector2(0, 0)  # Position wenn zu Fuß
        self.foot_direction = 0  # 0=rechts, 1=oben, 2=links, 3=unten
        self.animation_timer = 0
        self.animation_speed = 0.15  # Sekunden pro Frame
        # On-Foot / Insel-Modus (Stage 1)
        self.foot_speed = 220              # Laufgeschwindigkeit px/s
        self.foot_facing = pg.Vector2(1, 0)
        self.foot_ui = None                # None | "recruit" | "shipyard"
        self.nearby_interactable = None
        self.current_island = None         # IslandMap, wenn an Land
        self._active_interactable = None
        self._panel_index = 0
        self._foot_moving = False
        self._foot_message = None          # (text, restzeit_sekunden)
        # Flotte / Crew-Roster (werden in restart_game aus dem Save geladen)
        self.fleet = [dict(DEFAULT_SHIP)]
        self.active_ship_idx = 0
        
        # ==================== PREMIUM EFFEKTE ====================
        # Partikel-Systeme
        self.wake_particles = []  # Kielwasser
        self.explosions = []  # Explosionen
        self.splashes = []  # Wasser-Spritzer
        self.damage_numbers = []  # Schadenszahlen
        self.wake_spawn_timer = 0
        self.wake_spawn_interval = 0.05  # Alle 50ms ein Wake-Partikel
        
        # Screen Shake
        self.screen_shake = 0
        self.screen_shake_intensity = 0
        
        # Sonnenstrahl-Effekt
        self.sun_rays_timer = 0
        self.sun_rays = []
        for i in range(5):
            self.sun_rays.append({
                'angle': random.uniform(0, math.pi / 4),
                'width': random.randint(100, 200),
                'alpha': random.randint(20, 40),
                'speed': random.uniform(0.1, 0.3)
            })
        
        # Tag/Nacht-Zyklus (optional - sehr langsam)
        self.day_time = 0.5  # 0 = Mitternacht, 0.5 = Mittag, 1 = Mitternacht
        self.day_cycle_speed = 0.01  # Sehr langsam
        
        # Wellen-Overlay
        self.wave_offset = 0

        # Boss encounter state
        self.boss_arena = None  # type: dict | None

    def generate_gems(self):
        """Generiert zufällige Gems (sehr selten)"""
        gems = []
        # Nur 1-3 Gems pro Spiel
        num_gems = random.randint(1, 3)
        
        insel_w, insel_h = self.insel.get_size()
        
        for _ in range(num_gems):
            # Zufällige Position in der Welt (nicht auf Insel)
            while True:
                x = random.randint(-int(self.world_size.x // 2), int(self.world_size.x // 2))
                y = random.randint(-int(self.world_size.y // 2), int(self.world_size.y // 2))
                
                # Nicht auf der Insel
                if 0 < x < insel_w and 0 < y < insel_h:
                    continue
                
                break
            
            gems.append(Gem(pg.Vector2(x, y)))
        
        return gems

    def generate_crates(self):
        """Kisten spawnen ausschliesslich ueber den 30-Sekunden-Timer,
        daher startet der Run ohne Kisten."""
        return []

    def _clear_crate_effects(self):
        """Entfernt alle aktiven Artefakt-Effekte (z. B. beim Tod)."""
        self.active_crate_effects = []
        # --- Basis-Boni ---
        self.crate_bonus_speed_pct = 0.0
        self.crate_bonus_fire_rate_pct = 0.0
        self.crate_bonus_regen = 0.0
        self.crate_bonus_max_health = 0
        self.crate_bonus_damage = 0
        # --- Erweiterte Boni / einzigartige Effekte ---
        self.crate_bonus_damage_pct = 0.0
        self.crate_bonus_defense = 0.0
        self.crate_bonus_evasion = 0.0
        self.crate_bonus_crit_chance = 0.0
        self.crate_bonus_crit_mult = 0.0      # additiv auf Basis-Krit x2.0
        self.crate_bonus_lifesteal = 0.0
        self.crate_bonus_heal_on_kill = 0
        self.crate_bonus_xp_pct = 0.0
        self.crate_bonus_gem_find = 0.0
        self.crate_bonus_coin_bonus = 0
        self.crate_bonus_extra_shots = 0
        self.crate_bonus_proj_speed_pct = 0.0
        self.crate_bonus_proj_size = 0
        self.crate_bonus_pierce = 0
        self.crate_bonus_explosive = 0
        self.crate_bonus_thorns = 0.0
        self.crate_bonus_ram_damage = 0
        self.crate_bonus_pickup_radius = 0
        self.crate_bonus_revive = 0
        self.crate_bonus_max_shield = 0
        # Aktueller Schildwert + Aufladezustand
        self.shield = 0
        self.shield_regen_timer = 0.0
        self.artifact_popup = None  # {'name','rarity','color','desc','timer'}

    def _art_apply(self, **kwargs):
        """Addiert Artefakt-Boni auf die crate_bonus_* Werte."""
        for key, delta in kwargs.items():
            attr = 'crate_bonus_' + key
            setattr(self, attr, getattr(self, attr, 0) + delta)
        # Verteidigung / Ausweichen nicht negativ werden lassen
        # (Glass-Cannon-Artefakte koennen abziehen)
        if 'max_shield' in kwargs:
            # Schild sofort auf neues Maximum auffuellen
            self.shield = self.crate_bonus_max_shield

    def _current_max_health(self):
        return self.base_max_health + self.max_health_level * 20 + self.crate_bonus_max_health

    def _heal(self, amount):
        """Heilt das Schiff, begrenzt auf aktuelles Maximum."""
        if amount <= 0 or self.is_dead:
            return
        self.health = min(self._current_max_health(), self.health + amount)

    def _make_player_ball(self, pos, direction):
        """Erzeugt eine Spieler-Kanonenkugel inkl. Artefakt-Projektil-Boni."""
        ball = Cannonball(pos, direction)
        ball.speed *= (1 + self.crate_bonus_proj_speed_pct)
        ball.radius += self.crate_bonus_proj_size
        ball.pierce = self.crate_bonus_pierce      # Anzahl zusaetzlicher Durchschlaege
        ball.explosive = self.crate_bonus_explosive  # AoE-Radius (0 = keiner)
        ball.hit_ids = set()                        # bereits getroffene Gegner (Durchschlag)
        return ball

    def _boss_bar_visible(self):
        """True wenn gerade eine Boss-Leiste oben angezeigt wird."""
        for npc in self.npc_ships:
            if npc.is_boss and not npc.is_dead:
                if npc.boss_aggroed or self.cords_schiff1.distance_to(npc.pos) < 600:
                    return True
        return False

    def _draw_crate_marker_icon(self, surface, cx, cy, size):
        """Zeichnet ein kleines Kisten-Symbol mittig um (cx, cy)."""
        r = pg.Rect(cx - size // 2, cy - size // 2, size, size)
        pg.draw.rect(surface, (185, 130, 75), r, border_radius=3)
        pg.draw.rect(surface, (95, 62, 35), r, 2, border_radius=3)
        pg.draw.line(surface, (235, 190, 95), (r.left, cy), (r.right, cy), 2)
        pg.draw.line(surface, (235, 190, 95), (cx, r.top), (cx, r.bottom), 2)

    def _draw_crate_hud(self, s, w, h):
        """Artefakt-UI: Kompass mit Kisten-Richtungen, aktive Artefakte,
        Schild-Anzeige und das Sammel-Popup."""
        boss_bar = self._boss_bar_visible()

        # ---- Kompass: Richtung & Distanz zu allen offenen Kisten ----
        pulse = abs(math.sin(self.survival_time * 4)) * 0.4 + 0.6
        R = 48
        cx = w // 2
        cy = 150 if boss_bar else 72
        comp = pg.Surface((R * 2 + 8, R * 2 + 8), pg.SRCALPHA)
        ccx = ccy = R + 4
        # Kompass-Scheibe
        pg.draw.circle(comp, (12, 18, 30, 205), (ccx, ccy), R)
        pg.draw.circle(comp, (95, 125, 165, 220), (ccx, ccy), R, 2)
        pg.draw.circle(comp, (60, 80, 110, 150), (ccx, ccy), R * 2 // 3, 1)
        # Himmelsrichtungen (N rot hervorgehoben)
        for label, dx, dy in (("N", 0, -1), ("O", 1, 0), ("S", 0, 1), ("W", -1, 0)):
            lx = ccx + int(dx * (R - 10))
            ly = ccy + int(dy * (R - 10))
            col = (235, 120, 120) if label == "N" else (150, 170, 200)
            ltxt = self.font_small.render(label, True, col)
            comp.blit(ltxt, (lx - ltxt.get_width() // 2, ly - ltxt.get_height() // 2))
        # Schiff in der Mitte
        pg.draw.circle(comp, (255, 230, 140), (ccx, ccy), 3)
        # Offene Kisten als Blips (Winkel = Richtung, Radius = Distanz)
        open_crates = [c for c in self.crates if not c.collected]
        max_range = 2600.0
        for crate in open_crates:
            d = crate.pos - self.cords_schiff1
            dist = d.length()
            if dist < 1:
                continue
            dirn = d / dist
            rr = 11 + min(1.0, dist / max_range) * (R - 17)
            bx = ccx + int(dirn.x * rr)
            by = ccy + int(dirn.y * rr)
            pg.draw.rect(comp, (200, 145, 80), (bx - 4, by - 4, 8, 8), border_radius=2)
            pg.draw.rect(comp, (245, 205, 115, int(255 * pulse)), (bx - 4, by - 4, 8, 8), 1, border_radius=2)
        s.blit(comp, (cx - (R + 4), cy - (R + 4)))
        # Anzahl offener Kisten
        if open_crates:
            cnt = self.font_small.render(f"{len(open_crates)} Kisten", True, (255, 225, 160))
            s.blit(cnt, (cx - cnt.get_width() // 2, cy + R + 4))

        # ---- Aktive Artefakte (oben rechts) ----
        effects = self.active_crate_effects
        if effects:
            panel_w = 186
            row_h = 20
            start_y = 74 if boss_bar else 14
            title = self.font_small.render("Artefakte", True, (255, 220, 140))
            max_rows = min(len(effects), 12)
            panel_h = 26 + max_rows * row_h
            px = w - panel_w - 12
            panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
            pg.draw.rect(panel, (0, 0, 0, 150), (0, 0, panel_w, panel_h), border_radius=8)
            pg.draw.rect(panel, (120, 100, 60, 200), (0, 0, panel_w, panel_h), 2, border_radius=8)
            panel.blit(title, (10, 5))
            for i, eff in enumerate(effects[:max_rows]):
                ry = 26 + i * row_h
                dot = RARITY_COLOR.get(eff.get('rarity', 'common'), (200, 200, 200))
                pg.draw.circle(panel, dot, (14, ry + 8), 5)
                pg.draw.circle(panel, (255, 255, 255), (14, ry + 8), 5, 1)
                label = eff['name']
                if eff.get('stacks', 1) > 1:
                    label += f" x{eff['stacks']}"
                name_surf = self.font_small.render(label, True, (225, 225, 235))
                panel.blit(name_surf, (26, ry))
            s.blit(panel, (px, start_y))

        # ---- Schild-Anzeige (ueber der Lebensleiste) ----
        if self.crate_bonus_max_shield > 0:
            sh_w = 200
            sh_x, sh_y = 30, h - 102
            pg.draw.rect(s, (10, 20, 35), (sh_x, sh_y, sh_w, 6), border_radius=3)
            fill = int(sh_w * (self.shield / max(1, self.crate_bonus_max_shield)))
            if fill > 0:
                pg.draw.rect(s, (90, 200, 240), (sh_x, sh_y, fill, 6), border_radius=3)

        # ---- Sammel-Popup ----
        if self.artifact_popup is not None:
            pop = self.artifact_popup
            t = pop['timer']
            alpha = int(255 * min(1.0, t / 0.6))  # am Ende ausblenden
            rise = int((3.5 - t) * 6)
            pw, ph = 300, 56
            popup = pg.Surface((pw, ph), pg.SRCALPHA)
            pg.draw.rect(popup, (18, 16, 26, 235), (0, 0, pw, ph), border_radius=10)
            pg.draw.rect(popup, (*pop['color'], 255), (0, 0, pw, ph), 3, border_radius=10)
            self._draw_crate_marker_icon(popup, 24, ph // 2, 22)
            head = self.font_small.render("Artefakt gefunden!", True, (210, 210, 220))
            popup.blit(head, (46, 8))
            name_surf = self.font_main.render(pop['name'], True, pop['color'])
            popup.blit(name_surf, (46, 24))
            desc_surf = self.font_small.render(pop['desc'], True, (185, 190, 205))
            popup.blit(desc_surf, (pw - desc_surf.get_width() - 12, ph - 20))
            popup.set_alpha(alpha)
            s.blit(popup, (w // 2 - pw // 2, 96 - rise))

    def _apply_random_crate_item(self):
        """Vergibt ein zufaelliges Artefakt (nach Seltenheit gewichtet)."""
        weights = [RARITY_WEIGHT.get(a['rarity'], 1) for a in ARTIFACTS]
        artifact = random.choices(ARTIFACTS, weights=weights, k=1)[0]
        artifact['apply'](self)

        # HP ggf. auf neues Maximum anheben ist nicht noetig; nur Overheal kappen
        self.health = min(self.health, self._current_max_health())

        # Als aktives Artefakt merken (Stacks zaehlen)
        existing = None
        for e in self.active_crate_effects:
            if e['id'] == artifact['id']:
                existing = e
                break
        if existing is not None:
            existing['stacks'] += 1
        else:
            self.active_crate_effects.append({
                'id': artifact['id'],
                'name': artifact['name'],
                'desc': artifact['desc'],
                'rarity': artifact['rarity'],
                'color': artifact['color'],
                'stacks': 1,
            })

        # Sammel-Popup anzeigen
        self.artifact_popup = {
            'name': artifact['name'],
            'desc': artifact['desc'],
            'rarity': artifact['rarity'],
            'color': RARITY_COLOR.get(artifact['rarity'], (255, 255, 255)),
            'timer': 3.5,
        }

    def _kill_enemy(self, npc_ship):
        """Zentrale Kill-Logik (aus jeder Schadensquelle aufrufbar)."""
        if npc_ship.is_dead:
            return
        npc_ship.is_dead = True
        self.kills += 1
        self.coins += 1 + self.crate_bonus_coin_bonus
        # Artefakt-Boni beim Kill
        if self.crate_bonus_heal_on_kill:
            self._heal(self.crate_bonus_heal_on_kill)
        if self.crate_bonus_gem_find > 0 and random.random() < self.crate_bonus_gem_find:
            self.total_gems += 1
            save_gems(self.total_gems)
            self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -70), 1, (255, 220, 50)))

        if hasattr(self, 'achievement_state'):
            self.achievement_state['total_kills'] = int(self.achievement_state.get('total_kills', 0)) + 1
            self._check_achievements()
        # Grosse Explosion beim Tod
        self.explosions.append(ExplosionEffect(npc_ship.pos, color=(255, 100, 30), size=40))
        self.screen_shake = 0.3
        self.screen_shake_intensity = 12
        if hasattr(self, 'sfx'):
            self.sfx.play('explosion')

        # Pruefe ob alle Schiffe dieser Insel tot sind
        if hasattr(npc_ship, 'home_island'):
            island_idx = npc_ship.home_island
            all_dead = True
            for other_ship in self.npc_ships:
                if hasattr(other_ship, 'home_island') and other_ship.home_island == island_idx and not other_ship.is_dead:
                    all_dead = False
                    break
            if all_dead and island_idx < len(self.island_ship_status):
                island_pos, _ = self.island_ship_status[island_idx]
                self.island_ship_status[island_idx] = (island_pos, False)

        # EXP / Level
        difficulty = self.get_difficulty()
        if npc_ship.is_boss:
            self.level += 1
            self.skill_points += 2
            self.exp = 0
            self.exp_to_level = int(self.exp_to_level * 1.35)
            self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -50), 1, (255, 230, 120)))
            self.achievement_popups.append({'text': 'Boss defeated: Instant Level Up!', 'timer': 4.0})
            if self.boss_arena is not None and self.boss_arena.get('boss') is npc_ship:
                self._end_boss_arena()
            self.total_gems += 20
            save_gems(self.total_gems)
            self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -80), 20, (255, 220, 50)))
            self.screen_shake = 0.5
            self.screen_shake_intensity = 20
        else:
            base_exp = 25
            xp_multiplier = 1.0 + getattr(self, 'xp_boost_perk', 0) * 0.15 + self.crate_bonus_xp_pct
            if getattr(self, 'xp_booster_active', False) and getattr(self, 'xp_booster_remaining', 0) > 0:
                xp_multiplier *= 2.0
            scaled_exp = int(base_exp * difficulty * xp_multiplier)
            self.exp += scaled_exp
            self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -50), scaled_exp, (50, 200, 255)))

        while self.exp >= self.exp_to_level:
            self.exp -= self.exp_to_level
            self.level += 1
            self.exp_to_level = int(self.exp_to_level * 1.5)
            self.skill_points += 1
            if hasattr(self, 'sfx'):
                self.sfx.play('levelup')

    def generate_rocks(self):
        """Generiert zufällige Steinpositionen überall in der Welt"""
        rocks = []
        
        # Mindestabstand zwischen Steinen
        min_distance = 150
        
        # Viel mehr Steine über die ganze Welt verteilt!
        num_rocks = random.randint(120, 180)
        
        # Insel-Rect für Kollisionsprüfung
        insel_w, insel_h = self.insel.get_width(), self.insel.get_height()
        insel_rect = self.insel.get_rect(topleft=(0, 0))
        
        attempts = 0
        max_attempts = 4000
        
        # Spawn-Bereich: gesamte Welt
        half_wx = int(self.world_size.x // 2)
        half_wy = int(self.world_size.y // 2)
        
        while len(rocks) < num_rocks and attempts < max_attempts:
            attempts += 1
            
            # Zufällige Position in der gesamten Welt
            x = random.randint(-half_wx, half_wy)
            y = random.randint(-half_wy, half_wy)
            new_pos = pg.Vector2(x, y)
            
            # Zufälliger Typ und Skalierung
            rock_type = random.randint(0, 1)
            base_img = self.rock_base_imgs[rock_type]
            
            # Zufällige Skalierung: 1.0 bis 3.0
            scale = random.uniform(1.0, 3.0)
            
            # Pre-render skaliertes Bild für Performance
            scaled_img = pg.transform.scale_by(base_img, scale)
            scaled_mask = pg.mask.from_surface(scaled_img)
            rock_rect = scaled_img.get_rect(center=new_pos)
            
            # Prüfe ob Stein auf Haupt-Insel liegt (Masken-Kollision)
            offset = (rock_rect.left - insel_rect.left, rock_rect.top - insel_rect.top)
            if self.mask_insel.overlap(scaled_mask, offset):
                continue
            
            # Prüfe ob Stein auf einer Extra-Insel liegt
            collision_with_extra_island = False
            for island_pos, island_scale, island_img, island_mask in self.extra_islands:
                island_rect = island_img.get_rect(center=island_pos)
                island_offset = (rock_rect.left - island_rect.left, rock_rect.top - island_rect.top)
                if island_mask.overlap(scaled_mask, island_offset):
                    collision_with_extra_island = True
                    break
            
            if collision_with_extra_island:
                continue
            
            # Prüfe Mindestabstand zu anderen Steinen
            valid = True
            for rock_pos, _, _ in rocks:
                distance = new_pos.distance_to(rock_pos)
                if distance < min_distance:
                    valid = False
                    break
            
            if valid:
                # Speichere Position, pre-rendered Bild UND Maske (Performance!)
                rocks.append((new_pos, scaled_img, scaled_mask))
        
        return rocks

    def generate_extra_islands(self):
        """Generiert zusätzliche kleine Inseln in der Welt"""
        islands = []
        num_islands = random.randint(2, 3)  # Nur 2-3 zusätzliche Inseln (weniger Lag)
        
        # Verschiedene Skalierungen für Variation
        scales = [0.3, 0.4, 0.5]
        
        insel_w, insel_h = self.insel.get_size()
        min_distance = 2500  # Großer Mindestabstand zwischen Inseln
        
        attempts = 0
        max_attempts = 100
        
        while len(islands) < num_islands and attempts < max_attempts:
            attempts += 1
            
            # Zufällige Position weiter weg von der Haupt-Insel
            x = random.randint(-3000, insel_w + 3000)
            y = random.randint(-3000, insel_h + 3000)
            new_pos = pg.Vector2(x, y)
            
            # Nicht auf der Haupt-Insel
            if 0 < x < insel_w and 0 < y < insel_h:
                continue
            
            # Nicht zu nah an der Haupt-Insel Mitte
            haupt_insel_center = pg.Vector2(insel_w // 2, insel_h // 2)
            if new_pos.distance_to(haupt_insel_center) < min_distance:
                continue
            
            # Nicht zu nah an anderen Extra-Inseln
            valid = True
            for island_data in islands:
                if new_pos.distance_to(island_data[0]) < min_distance:
                    valid = False
                    break
            
            if valid:
                # Zufällige Skalierung
                scale = random.choice(scales)
                # Zufällige Variation: 0=normal, 1=horizontal gespiegelt, 2=vertikal gespiegelt, 3=beide gespiegelt
                flip_type = random.randint(0, 3)
                # Zufällige Rotation (nur 0 oder 180 für weniger Verzerrung)
                rotation = random.choice([0, 180])
                
                # Pre-render das transformierte Bild einmal
                island_img = self.insel.copy()
                if flip_type == 1:
                    island_img = pg.transform.flip(island_img, True, False)
                elif flip_type == 2:
                    island_img = pg.transform.flip(island_img, False, True)
                elif flip_type == 3:
                    island_img = pg.transform.flip(island_img, True, True)
                if rotation != 0:
                    island_img = pg.transform.rotate(island_img, rotation)
                # Skalieren
                new_w = int(island_img.get_width() * scale)
                new_h = int(island_img.get_height() * scale)
                island_img = pg.transform.scale(island_img, (new_w, new_h))
                island_mask = pg.mask.from_surface(island_img)
                
                islands.append((new_pos, scale, island_img, island_mask))
        
        return islands

    def generate_npc_ships(self):
        """Generiert NPC-Schiffe mit farbigen Segeln - 3-5 pro Insel"""
        ships = []
        
        # Segel-Farben: Blau, Rot, Schwarz
        segel_farben = [
            pg.Color(50, 100, 255),   # Blau
            pg.Color(255, 50, 50),     # Rot
            pg.Color(30, 30, 30),      # Schwarz
        ]
        
        # Insel-Bereich (topleft bei 0,0)
        insel_w, insel_h = self.insel.get_size()
        
        # Berechne den Insel-Radius für Spawn-Distanz
        insel_radius = max(insel_w, insel_h) // 2
        print(f"Insel-Größe: {insel_w}x{insel_h}, Radius: {insel_radius}")  # Debug
        
        # Für jede Insel 2-3 Schiffe spawnen
        for island_idx, (island_pos, _) in enumerate(self.island_ship_status):
            num_ships_for_island = random.randint(2, 3)
            print(f"Spawne {num_ships_for_island} Schiffe für Insel {island_idx} bei {island_pos}")  # Debug
            
            for ship_num in range(num_ships_for_island):
                # Zufällige Position um die Insel herum
                attempts = 0
                valid_pos = None
                
                while attempts < 100:
                    attempts += 1
                    # Position AUSSERHALB der Insel (Insel-Radius + 100-500 Pixel)
                    angle = random.uniform(0, 2 * 3.14159)
                    distance = insel_radius + random.uniform(100, 500)
                    x = island_pos.x + distance * pg.math.Vector2(1, 0).rotate_rad(angle).x
                    y = island_pos.y + distance * pg.math.Vector2(1, 0).rotate_rad(angle).y
                    pos = pg.Vector2(x, y)
                    
                    # Nicht zu nah am Spieler-Startpunkt
                    if pos.distance_to(self.cords_schiff1) < 150:
                        continue
                    
                    # Position ist gültig! (vereinfacht - keine Kollisionsprüfung mehr)
                    valid_pos = pos
                    break
                
                if valid_pos is not None:
                    # Zufällige Segel-Farbe
                    farbe = random.choice(segel_farben)
                    
                    ship = NPCShip(valid_pos, self.schiff1, self.schiff2, farbe, self.world_size)
                    ship.home_island = island_idx  # Merke welcher Insel das Schiff zugehört
                    ships.append(ship)
                    print(f"  Schiff {ship_num+1} bei {valid_pos}")  # Debug
                else:
                    print(f"  Schiff {ship_num+1} konnte nicht platziert werden!")  # Debug
        
        # === Open-Water Schiffe (überall in der Welt, nicht nur bei Inseln) ===
        num_open_water = random.randint(5, 8)
        half_wx = int(self.world_size.x // 2)
        half_wy = int(self.world_size.y // 2)
        
        for _ in range(num_open_water):
            attempts = 0
            while attempts < 50:
                attempts += 1
                x = random.randint(-half_wx, half_wx)
                y = random.randint(-half_wy, half_wy)
                pos = pg.Vector2(x, y)
                
                # Nicht auf der Haupt-Insel
                if 0 < x < insel_w and 0 < y < insel_h:
                    continue
                # Nicht zu nah am Spieler
                if pos.distance_to(self.cords_schiff1) < 300:
                    continue
                
                farbe = random.choice(segel_farben)
                ship = NPCShip(pos, self.schiff1, self.schiff2, farbe, self.world_size)
                ship.home_island = -1  # Kein Insel-Zugehörigkeit
                ships.append(ship)
                break
        
        print(f"NPC-Schiffe generiert: {len(ships)}")  # Debug
        return ships

    def take_damage(self, amount):
        """Nimmt Schaden wenn Cooldown abgelaufen ist"""
        if self.damage_cooldown <= 0:
            # Evasion (Basis + Artefakte): Chance den Treffer komplett auszuweichen
            evasion = min(0.9, getattr(self, 'evasion', 0.0) + getattr(self, 'crate_bonus_evasion', 0.0))
            if evasion > 0 and random.random() < evasion:
                self.damage_cooldown = self.damage_cooldown_duration
                self.damage_numbers.append(
                    DamageNumber(self.cords_schiff1 + pg.Vector2(0, -45), 0, (120, 220, 255), text="MISS")
                )
                if hasattr(self, 'sfx'):
                    self.sfx.play('damage')
                return

            # Defense (Basis + Artefakte): reduziert den erlittenen Schaden
            defense = min(0.9, max(0.0, getattr(self, 'defense', 0.0) + getattr(self, 'crate_bonus_defense', 0.0)))
            if defense > 0:
                amount = max(1, int(round(amount * (1 - defense))))

            # Thorns-Artefakt: reflektiert Schaden auf Gegner in der Naehe (kann nicht toeten)
            thorns = getattr(self, 'crate_bonus_thorns', 0.0)
            if thorns > 0:
                reflected = amount * thorns
                for npc in self.npc_ships:
                    if npc.is_dead:
                        continue
                    if self.cords_schiff1.distance_squared_to(npc.pos) <= 220 * 220:
                        npc.health = max(1, npc.health - reflected)

            # Schild-Artefakt: absorbiert Schaden zuerst
            if getattr(self, 'shield', 0) > 0:
                absorbed = min(self.shield, amount)
                self.shield -= absorbed
                amount -= absorbed
                self.shield_regen_timer = 0.0
                if amount <= 0:
                    self.damage_cooldown = self.damage_cooldown_duration
                    self.damage_numbers.append(
                        DamageNumber(self.cords_schiff1 + pg.Vector2(0, -45), 0, (120, 200, 255), text="BLOCK")
                    )
                    if hasattr(self, 'sfx'):
                        self.sfx.play('damage')
                    return

            self.health -= amount
            self.damage_cooldown = self.damage_cooldown_duration
            
            # Crew-Mitglieder können auch getroffen werden (30% Chance für jeden)
            for role, member in self.crew.get_members():
                if member.is_alive and random.random() < 0.30:  # 30% Chance pro Mitglied
                    crew_damage = random.randint(int(amount * 0.5), amount)
                    member.take_damage(crew_damage)
                    if not member.is_alive:
                        self.crew.on_crew_death(role)
            
            if hasattr(self, 'sfx'):
                self.sfx.play('damage')
            
            # Prüfe ob noch mindestens 1 Crew-Mitglied lebt
            if self.crew.alive_count() <= 0:
                self.health = 0
                self.is_dead = True

            # Wiederbelebung (Phoenixfeder-Artefakt): rettet einmal vor dem Tod
            if self.health <= 0 and not self.is_dead and getattr(self, 'crate_bonus_revive', 0) > 0:
                self.crate_bonus_revive -= 1
                self.health = int(self._current_max_health() * 0.5)
                self.damage_cooldown = 2.0  # kurze Unverwundbarkeit
                self.explosions.append(ExplosionEffect(self.cords_schiff1, color=(255, 180, 60), size=60))
                self.damage_numbers.append(
                    DamageNumber(self.cords_schiff1 + pg.Vector2(0, -50), 0, (255, 200, 80), text="REVIVE")
                )
                self.screen_shake = 0.4
                self.screen_shake_intensity = 14
                if hasattr(self, 'sfx'):
                    self.sfx.play('levelup')
                return

            if self.health <= 0:
                self.health = 0
                self.is_dead = True
                self.death_timer = 0
                self.repairing = False
                self.repair_hold_time = 0.0
                self._clear_crate_effects()
                self.crates = []
                # Highscore speichern
                self.is_new_highscore = save_highscore(
                    self.survival_time, self.kills, self.level, self.total_gems
                )
                if self.is_new_highscore:
                    self.highscore = load_highscore()
                # Profil-XP vergeben (Kills * 10 + Überlebenszeit * 2 + Level * 15)
                profile_xp = self.kills * 10 + int(self.survival_time * 2) + self.level * 15
                # Talent-Bonus auf Profil-XP
                bonuses = get_all_talent_bonuses()
                profile_xp = int(profile_xp * (1 + bonuses.get('xp_bonus', 0)))
                add_profile_xp(profile_xp, kills=self.kills, playtime=self.survival_time)
                # Talent: Extra-Gems pro Run
                extra_gems = bonuses.get('extra_gems_per_run', 0)
                if bonuses.get('double_gems', False):
                    extra_gems *= 2
                if extra_gems > 0:
                    self.total_gems += extra_gems
                    save_gems(self.total_gems)
                if hasattr(self, 'sfx'):
                    self.sfx.play('death')
    
    def toggle_on_foot(self):
        """Wechselt zwischen Schiff und zu Fuss."""
        if self.on_foot:
            # Wieder einsteigen - nur nahe am Boot.
            # WICHTIG: Schiff bleibt an seiner Wasser-Position (nicht auf player_foot_pos
            # setzen, sonst steckt das Schiff im Insel-Maskenbereich fest).
            if self.player_foot_pos.distance_to(self.cords_schiff1) < 100:
                self.on_foot = False
                self.current_island = None
                self.nearby_interactable = None
                self._active_interactable = None
                self.foot_ui = None
            return
        # Aussteigen: passende Insel + Land-Punkt suchen
        island_map, land_pos = self._find_disembark_spot()
        if island_map is None:
            return
        self.on_foot = True
        self.player_foot_pos = land_pos
        self.foot_facing = pg.Vector2(1, 0)
        self.foot_ui = None
        self.nearby_interactable = None
        self.current_island = island_map
        self._build_island_interactables(island_map)
        self.camera_pos = pg.Vector2(self.player_foot_pos)

    def _teleport_to_boat(self):
        """Teleportiert den Spieler von ueberall auf der Insel zurueck aufs Boot."""
        if not self.on_foot:
            return
        self.on_foot = False
        self.current_island = None
        self.nearby_interactable = None
        self._active_interactable = None
        self.foot_ui = None
        # Spieler-Position auf die Schiffsposition setzen (fuers naechste Aussteigen)
        self.player_foot_pos = pg.Vector2(self.cords_schiff1)
        self._play_sfx('menu_confirm')

    def _near_landing(self):
        """Schnelle Prüfung, ob das Schiff nahe genug an einer Insel zum Aussteigen ist."""
        ship = self.cords_schiff1
        if self.insel.get_rect(topleft=(0, 0)).inflate(300, 300).collidepoint(ship.x, ship.y):
            return True
        for island_pos, _scale, island_img, _m in self.extra_islands:
            if island_img.get_rect(center=island_pos).inflate(300, 300).collidepoint(ship.x, ship.y):
                return True
        return False

    def _find_disembark_spot(self):
        """Sucht nahe der Schiffsposition einen Land-Pixel; liefert (IslandMap, Vector2) oder (None, None)."""
        ship = self.cords_schiff1
        candidates = []
        main_rect = self.insel.get_rect(topleft=(0, 0))
        if main_rect.inflate(400, 400).collidepoint(ship.x, ship.y):
            candidates.append(IslandMap(-1, pg.Vector2(0, 0), self.insel, self.mask_insel))
        for i, (island_pos, _scale, island_img, island_mask) in enumerate(self.extra_islands):
            rect = island_img.get_rect(center=island_pos)
            if rect.inflate(400, 400).collidepoint(ship.x, ship.y):
                candidates.append(IslandMap(i, pg.Vector2(rect.topleft), island_img, island_mask))
        if not candidates:
            return None, None
        # Radiale Suche nach einem begehbaren Land-Pixel
        for dist in range(40, 280, 14):
            for angle_deg in range(0, 360, 12):
                ang = math.radians(angle_deg)
                test = pg.Vector2(ship.x + math.cos(ang) * dist, ship.y + math.sin(ang) * dist)
                for im in candidates:
                    if im.is_land(test):
                        return im, test
        # Fallback: Mittelpunkt der ersten Kandidaten-Insel
        im = candidates[0]
        center_world = im.anchor + pg.Vector2(im.surface.get_width() // 2, im.surface.get_height() // 2)
        return im, center_world

    def _build_island_interactables(self, island_map):
        """Platziert 1 Rekrut-NPC + 1 Werft an Land-Pixeln nahe dem Spieler."""
        island_map.interactables = []
        recruits = [CrewRecruit.random() for _ in range(3)]
        offers = [ShipOffer(spec) for spec in SHIP_CATALOG if spec["price"] > 0]
        placed = []
        for kind, payload in (("recruit", recruits), ("shipyard", offers)):
            pos = self._find_land_spot_near(island_map, self.player_foot_pos, placed)
            island_map.interactables.append(Interactable(kind, pos, payload))
            placed.append(pos)

    def _find_land_spot_near(self, island_map, origin, avoid, min_dist=90, max_dist=260):
        """Findet einen Land-Pixel in einem Ring um origin, mit Abstand zu bereits platzierten Props."""
        for _ in range(160):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(min_dist, max_dist)
            cand = pg.Vector2(origin.x + math.cos(ang) * dist, origin.y + math.sin(ang) * dist)
            if not island_map.is_land(cand):
                continue
            if any(cand.distance_to(p) < 90 for p in avoid):
                continue
            return cand
        return pg.Vector2(origin.x + 70, origin.y)

    def _play_sfx(self, name):
        if hasattr(self, 'sfx'):
            try:
                self.sfx.play(name)
            except Exception:
                pass

    # ---------- On-Foot Update ----------
    def _update_on_foot(self, events, dt):
        dt_seconds = dt / 1000.0
        if hasattr(self, 'sfx'):
            self.sfx.ensure_music_playing()
        # transiente Nachricht abklingen lassen
        if self._foot_message:
            self._foot_message = (self._foot_message[0], self._foot_message[1] - dt_seconds)
            if self._foot_message[1] <= 0:
                self._foot_message = None
        # Events
        for event in events:
            if event.type != pg.KEYDOWN:
                continue
            if event.key == pg.K_ESCAPE:
                if self.foot_ui is not None:
                    self.foot_ui = None
                    self._active_interactable = None
                else:
                    self.exit("pause")
                return
            elif event.key == pg.K_e:
                if self.foot_ui is not None:
                    self._confirm_foot_ui()
                elif self.nearby_interactable is not None:
                    self._open_interactable(self.nearby_interactable)
                else:
                    self.toggle_on_foot()
                    return
            elif event.key == pg.K_t and self.foot_ui is None:
                # Von ueberall auf der Insel zurueck aufs Boot teleportieren
                self._teleport_to_boat()
                return
            elif self.foot_ui is not None:
                self._handle_panel_key(event.key)
        # Panel offen -> Bewegung einfrieren
        if self.foot_ui is not None:
            if self.current_island:
                for it in self.current_island.interactables:
                    it.update(dt_seconds)
            return
        # Laufen (poll, 8-Richtungen, normalisiert)
        keys = pg.key.get_pressed()
        mv = pg.Vector2(keys[pg.K_d] - keys[pg.K_a], keys[pg.K_s] - keys[pg.K_w])
        moving = mv.length_squared() > 0
        if moving:
            mv = mv.normalize()
            self.foot_facing = mv
            step = mv * self.foot_speed * dt_seconds
            nx = self.player_foot_pos + pg.Vector2(step.x, 0)
            if self.current_island is None or self.current_island.is_land(nx):
                self.player_foot_pos = nx
            ny = self.player_foot_pos + pg.Vector2(0, step.y)
            if self.current_island is None or self.current_island.is_land(ny):
                self.player_foot_pos = ny
        self._foot_moving = moving
        self.animation_timer += dt_seconds
        # Proximity-Scan auf Interactables
        self.nearby_interactable = None
        best = float("inf")
        if self.current_island:
            for it in self.current_island.interactables:
                it.update(dt_seconds)
                d2 = self.player_foot_pos.distance_squared_to(it.pos)
                if d2 < it.radius * it.radius and d2 < best:
                    best = d2
                    self.nearby_interactable = it
        # Kamera folgt dem Spieler (RAW dt wie beim Segeln!)
        self.camera_pos += (self.player_foot_pos - self.camera_pos) * min(1, dt * self.cam_lerp)

    def _open_interactable(self, it):
        self.foot_ui = it.kind
        self._active_interactable = it
        self._panel_index = 0

    def _handle_panel_key(self, key):
        it = self._active_interactable
        if it is None:
            return
        options = it.payload if isinstance(it.payload, list) else []
        n = len(options)
        if n == 0:
            return
        if key in (pg.K_UP, pg.K_w):
            self._panel_index = (self._panel_index - 1) % n
        elif key in (pg.K_DOWN, pg.K_s):
            self._panel_index = (self._panel_index + 1) % n
        elif key in (pg.K_RETURN, pg.K_SPACE):
            self._confirm_foot_ui()

    def _confirm_foot_ui(self):
        it = self._active_interactable
        if it is None:
            self.foot_ui = None
            return
        options = it.payload if isinstance(it.payload, list) else []
        if not options:
            self.foot_ui = None
            return
        idx = max(0, min(self._panel_index, len(options) - 1))
        choice = options[idx]
        if it.kind == "recruit":
            if self.coins >= choice.price:
                self.coins -= choice.price
                self.crew.add_recruit(choice.role, choice.level, choice.name)
                roster = load_crew_roster()
                roster.append({"role": choice.role, "name": choice.name, "level": choice.level})
                save_crew_roster(roster)
                options.pop(idx)
                self._foot_message = (f"{choice.name} angeheuert!", 2.0)
                self._play_sfx('pickup')
            else:
                self._foot_message = ("Nicht genug Muenzen!", 1.5)
        else:  # shipyard
            if self.coins >= choice.price:
                self.coins -= choice.price
                entry = choice.to_fleet_entry()
                self.fleet.append(entry)
                self.active_ship_idx = len(self.fleet) - 1
                save_fleet(self.fleet)
                save_active_ship_idx(self.active_ship_idx)
                options.pop(idx)
                self._foot_message = (f"{choice.class_name} gekauft - ab naechstem Run aktiv!", 2.6)
                self._play_sfx('pickup')
            else:
                self._foot_message = ("Nicht genug Muenzen!", 1.5)
        if not options:
            self.foot_ui = None
            self._active_interactable = None
        else:
            self._panel_index = min(self._panel_index, len(options) - 1)

    def _fill_ocean(self, camera_surface, w, h, sx, sy):
        """Fuellt die Kamera-Surface komplett mit gekacheltem Ozean.
        Kachelanzahl richtet sich nach der Bildschirmgroesse, damit bei
        grossen Fenstern/Zoom keine Raender frei bleiben; eine Grundfarbe
        verhindert Luecken bei Zoom oder Screen-Shake."""
        if not hasattr(self, '_ocean_bg_color'):
            self._ocean_bg_color = self.tiles[0].get_at((32, 32))
        camera_surface.fill(self._ocean_bg_color)
        tile = int(time() * 2)
        ox, oy = int(sx) % 64, int(sy) % 64
        cols = w // 64 + 3
        rows = h // 64 + 3
        for i in range(cols):
            for j in range(rows):
                pos = (64 * i - 64 - ox, 64 * j - 64 - oy)
                camera_surface.blit(self.tiles[(tile + i) % 4], pos)

    # ---------- On-Foot Rendering ----------
    def _draw_on_foot(self, s, w, h):
        camera_surface = pg.Surface((w, h), pg.SRCALPHA)
        center = pg.Vector2(w // 2, h // 2)
        # Ozean (scrollt mit Kamera, deckt den ganzen Bildschirm ab)
        sx, sy = int(self.camera_pos.x), int(self.camera_pos.y)
        self._fill_ocean(camera_surface, w, h, sx, sy)
        # Hauptinsel
        insel_pos = pg.Vector2(0, 0) - self.camera_pos + center
        camera_surface.blit(self.insel, insel_pos)
        # Extra-Inseln
        for island_pos, _scale, island_img, _m in self.extra_islands:
            sp = island_pos - self.camera_pos + center
            camera_surface.blit(island_img, island_img.get_rect(center=sp))
        # Steine (mit Culling)
        for rock_pos, rock_img, _m in self.rocks:
            if abs(rock_pos.x - self.camera_pos.x) > w // 2 + 100 or abs(rock_pos.y - self.camera_pos.y) > h // 2 + 100:
                continue
            sp = rock_pos - self.camera_pos + center
            camera_surface.blit(rock_img, rock_img.get_rect(center=sp))
        # Das gemoorte Schiff (zum Wiedereinsteigen sichtbar)
        ship_sp = self.cords_schiff1 - self.camera_pos + center
        camera_surface.blit(self.schiff2, self.schiff2.get_rect(center=ship_sp))
        # Interactables (NPCs/Gebaeude)
        offset = self.camera_pos - center
        if self.current_island:
            for it in self.current_island.interactables:
                it.draw(camera_surface, offset)
        # Avatar
        self._draw_foot_avatar(camera_surface, w, h)
        s.blit(camera_surface, (0, 0))
        # Interaktions-Prompts
        if self.foot_ui is None:
            if self.nearby_interactable is not None:
                label = "anheuern" if self.nearby_interactable.kind == "recruit" else "Werft"
                sp = self.nearby_interactable.pos - self.camera_pos + center
                self._draw_prompt(s, sp, f"[E] {label}")
            elif self.player_foot_pos.distance_to(self.cords_schiff1) < 100:
                sp = self.cords_schiff1 - self.camera_pos + center
                self._draw_prompt(s, sp, "[E] An Bord")
        # Panels
        if self.foot_ui == "recruit":
            self._draw_recruit_panel(s, w, h)
        elif self.foot_ui == "shipyard":
            self._draw_shipyard_panel(s, w, h)
        # HUD
        self._draw_foot_hud(s, w, h)

    def _load_pirate_frames(self, scale=1):
        """Laedt die Piraten-Frames aus dem Sprite-Sheet (identisch zum Quit-Dialog)."""
        try:
            sheet = pg.image.load("assets/pirate.png").convert()
        except Exception:
            return []
        bg = sheet.get_at((sheet.get_width() // 2, 2))  # Hintergrund-Farbe
        lefts, top, cw, ch = (165, 251, 336, 422), 548, 86, 88
        frames = []
        for lx in lefts:
            cell = pg.Surface((cw, ch), pg.SRCALPHA)
            cell.blit(sheet, (0, 0), pg.Rect(lx, top, cw, ch))
            # Grauen Hintergrund + weichen Schlagschatten ausschneiden (Toleranz)
            cell.lock()
            for y in range(ch):
                for x in range(cw):
                    r, g, b, _ = cell.get_at((x, y))
                    if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < 78:
                        cell.set_at((x, y), (0, 0, 0, 0))
            cell.unlock()
            bb = cell.get_bounding_rect()
            if bb.width == 0:
                continue
            frame = pg.Surface(bb.size, pg.SRCALPHA)
            frame.blit(cell, (0, 0), bb)
            if scale != 1:
                frame = pg.transform.scale(frame, (bb.width * scale, bb.height * scale))
            frames.append(frame)
        return frames

    def _draw_foot_avatar(self, surface, w, h):
        center = pg.Vector2(w // 2, h // 2)
        sp = self.player_foot_pos - self.camera_pos + center
        ix, iy = int(sp.x), int(sp.y)
        # Piraten-Sprite wie im Quit-Dialog verwenden
        frames = getattr(self, "pirate_frames", None)
        if frames:
            # Beim Laufen leicht wippen lassen, im Stehen ruhig animieren
            idx = int(self.animation_timer * 6) % len(frames)
            bob = int(math.sin(self.animation_timer * 12) * 3) if self._foot_moving else 0
            frame = frames[idx]
            if self.foot_facing.x < 0:
                frame = pg.transform.flip(frame, True, False)
            fw, fh = frame.get_width(), frame.get_height()
            # Boden-Schatten
            shadow = pg.Surface((int(fw * 0.6), int(fh * 0.16)), pg.SRCALPHA)
            pg.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
            surface.blit(shadow, (ix - int(fw * 0.3), iy + int(fh * 0.42)))
            surface.blit(frame, (int(ix - fw / 2), int(iy - fh / 2 + bob)))
            return
        # Boden-Schatten (Fallback)
        shadow = pg.Surface((28, 10), pg.SRCALPHA)
        pg.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
        surface.blit(shadow, (ix - 14, iy + 12))
        frames = self.walk_frames if self._foot_moving else self.idle_frames
        if frames:
            idx = int(self.animation_timer / self.animation_speed) % len(frames)
            frame = frames[idx]
            if self.foot_facing.x < 0:
                frame = pg.transform.flip(frame, True, False)
            surface.blit(frame, frame.get_rect(center=(ix, iy)))
        else:
            pg.draw.circle(surface, (240, 220, 60), (ix, iy), 10)

    def _draw_prompt(self, surface, screen_pos, text):
        txt = self.font_small.render(text, True, (255, 255, 255))
        pad = 8
        bob = int(math.sin(time() * 4) * 2)
        bw = txt.get_width() + pad * 2
        bh = txt.get_height() + pad
        bx = int(screen_pos.x - bw // 2)
        by = int(screen_pos.y - 56 + bob)
        panel = pg.Surface((bw, bh), pg.SRCALPHA)
        pg.draw.rect(panel, (18, 24, 40, 225), panel.get_rect(), border_radius=8)
        pg.draw.rect(panel, (120, 200, 255), panel.get_rect(), 2, border_radius=8)
        panel.blit(txt, (pad, pad // 2))
        surface.blit(panel, (bx, by))
        tipx = int(screen_pos.x)
        pg.draw.polygon(surface, (120, 200, 255), [(tipx - 5, by + bh), (tipx + 5, by + bh), (tipx, by + bh + 6)])

    def _panel_chrome(self, surface, w, h, title_text):
        pw, ph = 480, 330
        px, py = (w - pw) // 2, (h - ph) // 2
        panel = pg.Surface((pw, ph), pg.SRCALPHA)
        pg.draw.rect(panel, (16, 20, 36, 240), panel.get_rect(), border_radius=12)
        pg.draw.rect(panel, (120, 200, 255), panel.get_rect(), 2, border_radius=12)
        surface.blit(panel, (px, py))
        title = self.font_title.render(title_text, True, (120, 200, 255))
        surface.blit(title, (px + 20, py + 14))
        gem_txt = self.font_main.render(f"Muenzen: {self.coins}", True, (255, 210, 80))
        surface.blit(gem_txt, (px + pw - gem_txt.get_width() - 20, py + 20))
        hint = self.font_small.render("Pfeile waehlen   [E]/Enter bestaetigen   [Esc] schliessen", True, (180, 190, 210))
        surface.blit(hint, (px + 20, py + ph - 28))
        return px, py, pw, ph

    def _draw_recruit_panel(self, surface, w, h):
        px, py, pw, ph = self._panel_chrome(surface, w, h, "Taverne - Crew anheuern")
        it = self._active_interactable
        options = it.payload if it and isinstance(it.payload, list) else []
        if not options:
            none_txt = self.font_main.render("Niemand mehr verfuegbar.", True, (200, 200, 200))
            surface.blit(none_txt, (px + 24, py + 90))
        else:
            for i, rec in enumerate(options):
                row_y = py + 74 + i * 52
                sel = (i == self._panel_index)
                if sel:
                    pg.draw.rect(surface, (40, 60, 92), (px + 12, row_y - 6, pw - 24, 46), border_radius=6)
                role_name = CrewMember.ROLES.get(rec.role, {}).get('name', rec.role)
                lvl_name = CrewRecruit.LEVEL_NAMES.get(rec.level, str(rec.level))
                afford = self.coins >= rec.price
                col = (235, 235, 235) if afford else (150, 110, 110)
                surface.blit(self.font_main.render(f"{rec.name} - {lvl_name} {role_name}", True, col), (px + 26, row_y))
                price = self.font_main.render(f"{rec.price} M", True, (255, 210, 80) if afford else (150, 110, 110))
                surface.blit(price, (px + pw - price.get_width() - 26, row_y))
        self._draw_foot_message(surface, w, h)

    def _draw_shipyard_panel(self, surface, w, h):
        px, py, pw, ph = self._panel_chrome(surface, w, h, "Werft - Schiff kaufen")
        it = self._active_interactable
        options = it.payload if it and isinstance(it.payload, list) else []
        if not options:
            none_txt = self.font_main.render("Ausverkauft.", True, (200, 200, 200))
            surface.blit(none_txt, (px + 24, py + 90))
        else:
            for i, off in enumerate(options):
                row_y = py + 70 + i * 56
                sel = (i == self._panel_index)
                if sel:
                    pg.draw.rect(surface, (40, 60, 92), (px + 12, row_y - 6, pw - 24, 50), border_radius=6)
                afford = self.coins >= off.price
                col = (235, 235, 235) if afford else (150, 110, 110)
                surface.blit(self.font_main.render(off.class_name, True, col), (px + 26, row_y))
                stats = f"HP x{off.hp_mult:.1f}  Spd x{off.speed_mult:.2f}  Dmg x{off.dmg_mult:.1f}"
                surface.blit(self.font_small.render(stats, True, (170, 190, 210)), (px + 26, row_y + 24))
                price = self.font_main.render(f"{off.price} M", True, (255, 210, 80) if afford else (150, 110, 110))
                surface.blit(price, (px + pw - price.get_width() - 26, row_y + 8))
        self._draw_foot_message(surface, w, h)

    def _draw_foot_hud(self, surface, w, h):
        coin_txt = self.font_main.render(f"Muenzen: {self.coins}", True, (255, 210, 80))
        surface.blit(coin_txt, (16, 14))
        gem_txt = self.font_small.render(f"Gems: {self.total_gems}", True, (200, 200, 210))
        surface.blit(gem_txt, (16 + coin_txt.get_width() + 20, 22))
        res = len(self.crew.reserves) if hasattr(self, 'crew') else 0
        mode_txt = self.font_small.render(f"An Land  -  WASD laufen, [E] interagieren, [T] zum Boot  |  Reserve-Crew: {res}", True, (220, 230, 245))
        surface.blit(mode_txt, (16, 46))
        self._draw_foot_message(surface, w, h)

    def _draw_foot_message(self, surface, w, h):
        msg = self._foot_message
        if not msg:
            return
        m = self.font_main.render(msg[0], True, (255, 220, 120))
        bx = (w - m.get_width()) // 2
        by = h - 84
        bg = pg.Surface((m.get_width() + 24, m.get_height() + 12), pg.SRCALPHA)
        pg.draw.rect(bg, (20, 16, 8, 210), bg.get_rect(), border_radius=8)
        surface.blit(bg, (bx - 12, by - 6))
        surface.blit(m, (bx, by))

    def get_difficulty(self):
        """Berechnet die aktuelle Schwierigkeit basierend auf Survival-Zeit"""
        # Startet bei 1.0, erhöht sich alle 60 Sekunden um 0.5
        # Nach 5 Minuten: 3.5x Stärke
        minutes_survived = self.survival_time / 60.0
        return 1.0 + (minutes_survived * 0.5)

    def get_enemy_damage_mult(self):
        """Schaden der NPC-Boote steigt nach einer bestimmten Zeit mit der Überlebensdauer.
        Erste 60s normal, danach alle 60s +25% (maximal x3)."""
        if self.survival_time < 60:
            return 1.0
        extra = (self.survival_time - 60) / 60.0 * 0.25
        return min(3.0, 1.0 + extra)


    def _scale_living_npcs(self):
        """Skaliert lebende NPCs zur aktuellen Schwierigkeit (alle 10 Sekunden)"""
        difficulty = self.get_difficulty()
        for npc_ship in self.npc_ships:
            if not npc_ship.is_dead:
                npc_ship.scale_to_difficulty(difficulty)
    
    def _maybe_spawn_extra_npcs(self):
        """Spawnt zusätzliche NPCs bei höherer Schwierigkeit - in der Nähe des Spielers"""
        difficulty = self.get_difficulty()
        # Alle 2 Minuten + ab Schwierigkeit 2.0: Chance auf Extra-Schiff
        desired_count = len(self.island_ship_status) * 3 + int((difficulty - 1.0) * 1.5)
        alive_count = sum(1 for s in self.npc_ships if not s.is_dead)
        
        if alive_count < desired_count and len(self.npc_ships) < 20:  # Max 20 NPCs
            segel_farben = [
                pg.Color(50, 100, 255),
                pg.Color(255, 50, 50),
                pg.Color(30, 30, 30),
            ]
            insel_w, insel_h = self.insel.get_size()
            
            # Spawn in Ring um den Spieler (600-1200 Pixel entfernt)
            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(600, 1200)
            x = self.cords_schiff1.x + dist * pg.math.Vector2(1, 0).rotate_rad(angle).x
            y = self.cords_schiff1.y + dist * pg.math.Vector2(1, 0).rotate_rad(angle).y
            pos = pg.Vector2(x, y)
            
            # Nicht auf der Haupt-Insel
            on_island = 0 < x < insel_w and 0 < y < insel_h
            if not on_island and pos.distance_to(self.cords_schiff1) > 400:
                farbe = random.choice(segel_farben)
                ship = NPCShip(pos, self.schiff1, self.schiff2, farbe, self.world_size)
                ship.home_island = 0
                ship.scale_to_difficulty(difficulty)
                self.npc_ships.append(ship)

    def _start_boss_arena(self, boss_ship):
        """Startet eine Kampf-Arena um einen aggro Boss."""
        if boss_ship is None or boss_ship.is_dead:
            return
        self.boss_arena = {
            'boss': boss_ship,
            'center': pg.Vector2(boss_ship.pos),
            'radius': 780,
            'phase': 1,
            'fire_cooldown': 1.8,
            'minion_cooldown': 7.0,
            'hazard_tick': 0.0,
        }

    def _end_boss_arena(self):
        self.boss_arena = None  # type: dict | None

    def _get_active_arena_boss(self):
        if self.boss_arena is None:
            return None
        boss = self.boss_arena.get('boss')
        if boss is None or boss.is_dead:
            self._end_boss_arena()
            return None
        if boss not in self.npc_ships:
            self._end_boss_arena()
            return None
        return boss

    def _spawn_boss_minion(self, boss, difficulty):
        """Spawnt ein kleines Helfer-Schiff in Arena-Nähe."""
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(180, 320)
        pos = boss.pos + pg.Vector2(math.cos(angle), math.sin(angle)) * dist
        farbe = pg.Color(220, 70, 70)
        minion = NPCShip(pos, self.schiff1, self.schiff2, farbe, self.world_size)
        minion.is_boss = False
        minion.is_boss_minion = True
        minion.can_respawn = False
        minion.home_island = -2
        minion.health = int(80 * max(1.0, difficulty * 0.9))
        minion.max_health = minion.health
        minion.speed = int(120 * min(2.0, 0.9 + difficulty * 0.25))
        minion.shoot_cooldown_duration = max(0.6, 1.4 / max(1.0, difficulty))
        minion.shoot_range = 430
        minion.boss_damage = int(9 + difficulty * 2)
        minion.hit_radius = 42
        minion.respawn_duration = 9999.0
        self.npc_ships.append(minion)

    def _fire_boss_volley(self, boss, phase):
        """Feuer-Salven des Bosses je nach Phase."""
        to_player = self.cords_schiff1 - boss.pos
        if to_player.length_squared() == 0:
            to_player = pg.Vector2(1, 0)
        else:
            to_player = to_player.normalize()

        shot_count = 3 + phase
        spread_deg = 10 + phase * 4
        center = (shot_count - 1) / 2.0
        for i in range(shot_count):
            angle = (i - center) * spread_deg
            shot_dir = to_player.rotate(angle)
            fire_ball = Cannonball(boss.pos, shot_dir, is_enemy=True)
            fire_ball.speed = 560 + phase * 35
            fire_ball.radius = 11
            fire_ball.lifetime = 3.4
            fire_ball.boss_damage = int(14 + phase * 5)
            self.cannonballs.append(fire_ball)

        if phase >= 3:
            # Zusätzliche Ring-Salve in der letzten Phase
            for i in range(8):
                ring_dir = pg.Vector2(1, 0).rotate(i * 45)
                ring_ball = Cannonball(boss.pos, ring_dir, is_enemy=True)
                ring_ball.speed = 500
                ring_ball.radius = 9
                ring_ball.lifetime = 2.8
                ring_ball.boss_damage = 11
                self.cannonballs.append(ring_ball)

    def _update_boss_encounter(self, dt_seconds):
        boss = self._get_active_arena_boss()
        if boss is None:
            return

        arena = self.boss_arena
        if arena is None:
            return
        arena = cast(dict, arena)
        boss_ratio = boss.health / max(1, boss.max_health)
        if boss_ratio <= 0.33:
            phase = 3
        elif boss_ratio <= 0.66:
            phase = 2
        else:
            phase = 1
        arena['phase'] = phase

        # Boss selbst in der Arena halten (harte Begrenzung)
        center = arena['center']
        to_boss = boss.pos - center
        boss_dist = to_boss.length()
        if boss_dist > arena['radius']:
            if boss_dist > 0:
                boss.pos = center + to_boss.normalize() * arena['radius']
            # Wenn er den Rand erreicht, kurz zurück zur Mitte lenken
            boss.target = pg.Vector2(center)
            boss.avoid_timer = 0
        elif boss_dist > arena['radius'] * 0.9:
            # Schon vor dem Rand: leichte Rücklenkung
            boss.target = pg.Vector2(center)

        # Arena-Grenze erzwingen
        to_player = self.cords_schiff1 - center
        dist = to_player.length()
        if dist > arena['radius']:
            if dist > 0:
                self.cords_schiff1 = center + to_player.normalize() * arena['radius']
            arena['hazard_tick'] -= dt_seconds
            if arena['hazard_tick'] <= 0:
                arena['hazard_tick'] = 0.7
                self.take_damage(8)
                self.damage_numbers.append(DamageNumber(self.cords_schiff1 + pg.Vector2(0, -25), 8, (255, 80, 80)))
        else:
            arena['hazard_tick'] = 0.0

        # Boss-Feuerangriffe
        arena['fire_cooldown'] -= dt_seconds
        if arena['fire_cooldown'] <= 0:
            self._fire_boss_volley(boss, phase)
            arena['fire_cooldown'] = max(0.85, 2.2 - phase * 0.35)
            if hasattr(self, 'sfx'):
                self.sfx.play('cannon')

        # Minions in späteren Phasen
        if phase >= 2:
            arena['minion_cooldown'] -= dt_seconds
            if arena['minion_cooldown'] <= 0:
                alive_minions = sum(1 for n in self.npc_ships if getattr(n, 'is_boss_minion', False) and not n.is_dead)
                if alive_minions < (2 if phase == 2 else 4):
                    self._spawn_boss_minion(boss, self.get_difficulty())
                arena['minion_cooldown'] = 8.5 if phase == 2 else 6.0

    def _check_achievements(self):
        """Prüft Achievement-Fortschritt, vergibt Rewards und schaltet Klassen frei."""
        unlocked_ids = set(self.achievement_state.get('unlocked', []))
        newly_unlocked = []
        newly_unlocked_pirates = set()

        total_kills = int(self.achievement_state.get('total_kills', 0))
        total_playtime = float(self.achievement_state.get('total_playtime_seconds', 0.0))

        for ach in ACHIEVEMENTS:
            if ach['id'] in unlocked_ids:
                continue

            if ach['type'] == 'kills':
                reached = total_kills >= ach['target']
            else:
                reached = total_playtime >= ach['target']

            if not reached:
                continue

            unlocked_ids.add(ach['id'])
            newly_unlocked.append(ach)

            if ach.get('reward_gems', 0) > 0:
                self.total_gems += ach['reward_gems']
                save_gems(self.total_gems)

            pirate_id = ach.get('unlock_pirate')
            if pirate_id:
                newly_unlocked_pirates.add(pirate_id)

        if not newly_unlocked:
            return

        self.achievement_state['unlocked'] = sorted(list(unlocked_ids))
        save_achievement_state(self.achievement_state)

        if newly_unlocked_pirates:
            unlocked_pirates = load_unlocked_pirate_ids()
            unlocked_pirates |= newly_unlocked_pirates
            save_unlocked_pirate_ids(unlocked_pirates)

        for ach in newly_unlocked:
            msg = f"Achievement: {ach['name']} (+{ach['reward_gems']} Gems)"
            pirate_id = ach.get('unlock_pirate')
            if pirate_id:
                pirate_name = PIRATE_PRESETS.get(pirate_id, {}).get('name', pirate_id)
                msg += f" | New class: {pirate_name}"
            self.achievement_popups.append({'text': msg, 'timer': 5.0})

        if hasattr(self, 'sfx'):
            self.sfx.play('levelup')
    
    def restart_game(self):
        """Startet das Spiel neu"""
        # Ausgewählte Piratenklasse laden
        selected_pirate_id = load_selected_pirate_id()
        self.unlocked_pirates = load_unlocked_pirate_ids()
        if selected_pirate_id not in self.unlocked_pirates:
            selected_pirate_id = 'balanced'
        pirate = PIRATE_PRESETS.get(selected_pirate_id, PIRATE_PRESETS['balanced'])
        self.selected_pirate_id = selected_pirate_id
        self.selected_pirate_name = pirate['name']
        self.achievement_state = load_achievement_state()
        self.achievement_popups = []
        self.achievement_save_timer = 0.0

        # Flotte + aktives Flaggschiff aus dem Save laden
        self.fleet = load_fleet()
        self.active_ship_idx = load_active_ship_idx()
        if not (0 <= self.active_ship_idx < len(self.fleet)):
            self.active_ship_idx = 0

        self.xp_boost_perk = 0  # Perk-System entfernt

        # Talent-Boni laden
        self.talent_bonuses = get_all_talent_bonuses()

        # Basis-Werte mit Talent-Boni
        talent_hp = self.talent_bonuses.get('max_hp_bonus', 0)
        talent_dmg = self.talent_bonuses.get('damage_bonus', 0)
        talent_spd = self.talent_bonuses.get('speed_bonus', 0)
        talent_regen = self.talent_bonuses.get('regen_bonus', 0)
        talent_fire = self.talent_bonuses.get('fire_rate_bonus', 0)
        talent_all = self.talent_bonuses.get('all_stats_bonus', 0)

        self.base_max_health = int((100 + talent_hp) * (1 + talent_all))
        self.base_damage = int(25 * (1 + talent_dmg + talent_all))
        self.base_speed = int(300 * (1 + talent_spd + talent_all))
        self.base_speed_back = int(150 * (1 + talent_spd + talent_all))
        self.base_regen = 0
        self.base_repair_rate = (2.5 + talent_regen) * (1 + talent_all)
        self.base_shoot_cooldown = 0.45 * (1 - talent_fire)

        # Piraten-Boni und Debuffs anwenden
        self.base_max_health = int(self.base_max_health * pirate['max_hp_mult'])
        self.base_damage = int(self.base_damage * pirate['damage_mult'])
        self.base_speed = int(self.base_speed * pirate['speed_mult'])
        self.base_speed_back = int(self.base_speed_back * pirate['speed_mult'])
        self.base_repair_rate = self.base_repair_rate * pirate['repair_mult']
        self.base_shoot_cooldown = self.base_shoot_cooldown * pirate['reload_mult']

        # Verteidigung (reduziert erlittenen Schaden) & Ausweichen (Chance zu dodgen)
        self.defense = min(0.9, pirate.get('defense', 0.0))
        self.evasion = min(0.9, pirate.get('evasion', 0.0))

        # Aktives Flaggschiff: Stat-Multiplikatoren der Flotte anwenden
        active_ship = self.fleet[self.active_ship_idx] if (self.fleet and 0 <= self.active_ship_idx < len(self.fleet)) else None
        if active_ship:
            self.base_max_health = int(self.base_max_health * active_ship.get('hp_mult', 1.0))
            self.base_damage = int(self.base_damage * active_ship.get('dmg_mult', 1.0))
            self.base_speed = int(self.base_speed * active_ship.get('speed_mult', 1.0))
            self.base_speed_back = int(self.base_speed_back * active_ship.get('speed_mult', 1.0))

        self.health = self.base_max_health
        self.is_dead = False
        self.death_timer = 0
        self.survival_time = 0  # Survival-Zeit zurücksetzen
        # Startposition außerhalb der Insel
        insel_w, insel_h = self.insel.get_size()
        self.cords_schiff1 = pg.Vector2(insel_w + 200, insel_h // 2)
        self.schiff_richtung = 0
        self.camera_pos = pg.Vector2(self.cords_schiff1)

        # On-Foot-Modus für neuen Run zurücksetzen
        self.on_foot = False
        self.foot_ui = None
        self.current_island = None
        self.nearby_interactable = None
        self._active_interactable = None
        self.player_foot_pos = pg.Vector2(0, 0)
        self._foot_message = None

        # Island status zurücksetzen und neue Schiffe generieren
        self.island_ship_status = [(pg.Vector2(insel_w // 2, insel_h // 2), True)]
        self.npc_ships = self.generate_npc_ships()
        
        self.damage_cooldown = 0
        self.cannonballs = []
        self.shoot_cooldown = 0
        self.exp = 0
        self.level = 1
        self.skill_points = 0
        self.speed_level = 0
        self.fire_rate_level = 0
        self.regen_level = 0
        self.max_health_level = 0
        self.damage_level = 0
        self.kills = 0
        self.coins = 0  # Muenzen jeden Run zuruecksetzen
        self.is_new_highscore = False
        self.highscore = load_highscore()  # Highscore neu laden
        self.explored_cells = set()  # Fog of War zurücksetzen
        self.show_big_minimap = False
        self.map_zoom = 1.0
        self.map_zoom_target = 1.0
        self.map_drag_offset = pg.Vector2(0, 0)
        self.map_hover_info = None
        self.gems = self.generate_gems()  # Neue Gems für neuen Run
        self.gem_spawn_timer = 0
        self.total_gems = load_gems()  # Gems neu laden (nach Perk-Käufen aktuell)

        self.crates = self.generate_crates()
        self.crate_spawn_timer = 0
        self._clear_crate_effects()
        self.repair_hold_time = 0.0
        self.repairing = False

        # Boss encounter state
        self.boss_arena = None
        
        # Crew zurücksetzen für neuen Run
        self.crew = ShipCrew()
        # Permanentes Crew-Roster (auf Inseln angeheuert) als Reserve übernehmen
        for r in load_crew_roster():
            self.crew.add_recruit(r.get('role', 'boatswain'), r.get('level', 1), r.get('name'))

        # XP Booster laden (aus Login-Streak)
        booster_minutes = load_xp_booster()
        self.xp_booster_remaining = booster_minutes * 60.0  # In Sekunden umwandeln
        self.xp_booster_active = booster_minutes > 0

    # def collide(self, other):
    #     ...
        
    def on_enter(self, frm):
        print("Playing")
        # Sound Manager
        self.sfx = get_sound_manager()
        self.sfx.start_ocean_ambience()
        self.sfx.start_battle_music()
        # Wenn vom Menü kommend, Spiel neu starten
        if frm == "menu":
            self.restart_game()

    def update(self, events, dt):
        # dt in Sekunden umrechnen
        dt_seconds = dt / 1000.0

        # An Land (zu Fuß): eigener Update-Zweig, friert Segeln/Kampf ein
        if self.on_foot:
            return self._update_on_foot(events, dt)

        # Musik am Laufen halten (falls Kanal unerwartet stoppt)
        if hasattr(self, 'sfx'):
            self.sfx.ensure_music_playing()
        
        # Survival-Zeit erhöhen (für Schwierigkeits-Skalierung)
        if not self.is_dead:
            self.survival_time += dt_seconds
            if hasattr(self, 'achievement_state'):
                self.achievement_state['total_playtime_seconds'] = self.achievement_state.get('total_playtime_seconds', 0.0) + dt_seconds
                self.achievement_save_timer += dt_seconds
                if self.achievement_save_timer >= 1.0:
                    self.achievement_save_timer = 0.0
                    save_achievement_state(self.achievement_state)
                    self._check_achievements()
            
            # Alle 10 Sekunden: Lebende NPCs skalieren + Extra-Spawns prüfen
            old_ten = int((self.survival_time - dt_seconds) / 10)
            new_ten = int(self.survival_time / 10)
            if new_ten > old_ten:
                self._scale_living_npcs()
                self._maybe_spawn_extra_npcs()
            
            # XP Booster Timer runterzählen
            if self.xp_booster_active and self.xp_booster_remaining > 0:
                self.xp_booster_remaining -= dt_seconds
                if self.xp_booster_remaining <= 0:
                    self.xp_booster_remaining = 0
                    self.xp_booster_active = False
                    save_xp_booster(0)
        
        # Wenn tot, Timer laufen lassen und dann zum Menü
        if self.is_dead:
            self.death_timer += dt_seconds
            if self.death_timer >= self.death_duration:
                if hasattr(self, 'sfx'):
                    self.sfx.stop_ocean_ambience()
                    self.sfx.stop_battle_music()
                self.exit("menu")  # Zurück zum Menü statt restart
            return
        
        # Damage Cooldown
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt_seconds

        # Schild-Artefakt: laedt nach kurzer Ruhe wieder auf
        if self.crate_bonus_max_shield > 0:
            self.shield_regen_timer += dt_seconds
            if self.shield_regen_timer >= 2.0 and self.shield < self.crate_bonus_max_shield:
                self.shield = min(self.crate_bonus_max_shield, self.shield + 8 * dt_seconds)

        # Artefakt-Sammel-Popup ausblenden
        if self.artifact_popup is not None:
            self.artifact_popup['timer'] -= dt_seconds
            if self.artifact_popup['timer'] <= 0:
                self.artifact_popup = None

        # This is an example for handling events
        # and changing states
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.exit("pause")
                elif event.key == pg.K_m:
                    self.show_big_minimap = not self.show_big_minimap
                    if not self.show_big_minimap:
                        # Reset drag offset when closing map
                        self.map_drag_offset = pg.Vector2(0, 0)
                        self.map_zoom = 1.0
                        self.map_zoom_target = 1.0
                        self.map_hover_info = None
                elif event.key == pg.K_c and self.show_big_minimap:
                    # Zentriere die Karte auf dem Spieler
                    self.map_drag_offset = pg.Vector2(0, 0)
                elif event.key == pg.K_a:
                    self.schiff_richtung -= 1
                    self.schiff_richtung %= 8
                elif event.key == pg.K_d:
                    self.schiff_richtung += 1
                    self.schiff_richtung %= 8
                elif event.key == pg.K_e:
                    # Aussteigen, wenn das Schiff nahe an einer Insel liegt
                    self.toggle_on_foot()
                # Upgrade-Tasten
                elif event.key == pg.K_1 and self.skill_points > 0:
                    self.speed_level += 1
                    self.skill_points -= 1
                elif event.key == pg.K_2 and self.skill_points > 0:
                    self.fire_rate_level += 1
                    self.skill_points -= 1
                elif event.key == pg.K_3 and self.skill_points > 0:
                    self.regen_level += 1
                    self.skill_points -= 1
                elif event.key == pg.K_4 and self.skill_points > 0:
                    self.max_health_level += 1
                    self.skill_points -= 1
                    # Erhöhe auch aktuelle Leben
                    self.health += 20
                elif event.key == pg.K_5 and self.skill_points > 0:
                    self.damage_level += 1
                    self.skill_points -= 1
            # Maus-Events für Karten-Drag
            elif event.type == pg.MOUSEBUTTONDOWN and self.show_big_minimap:
                if event.button == 1:  # Linke Maustaste
                    self.map_dragging = True
                    self.map_drag_start = pg.Vector2(event.pos)
                elif event.button == 4:  # Scrollrad hoch → reinzoomen
                    self.map_zoom_target = min(3.0, self.map_zoom_target * 1.25)
                elif event.button == 5:  # Scrollrad runter → rauszoomen
                    self.map_zoom_target = max(0.3, self.map_zoom_target / 1.25)
            elif event.type == pg.MOUSEWHEEL and self.show_big_minimap:
                if event.y > 0:
                    self.map_zoom_target = min(3.0, self.map_zoom_target * 1.25)
                elif event.y < 0:
                    self.map_zoom_target = max(0.3, self.map_zoom_target / 1.25)
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.map_dragging = False
            elif event.type == pg.MOUSEMOTION and self.map_dragging and self.show_big_minimap:
                current_pos = pg.Vector2(event.pos)
                delta = current_pos - self.map_drag_start
                self.map_drag_offset += delta
                self.map_drag_start = current_pos
        
        # Smooth Zoom der Weltkarte
        if self.show_big_minimap:
            zoom_diff = self.map_zoom_target - self.map_zoom
            self.map_zoom += zoom_diff * min(1, dt_seconds * 8)
        
        # Wenn große Minimap offen ist, Spiel pausieren
        if self.show_big_minimap:
            return
        
        # Fog of War aktualisieren - aktuelle Position als erkundet markieren
        current_pos = self.cords_schiff1
        grid_x = int(current_pos.x // self.fog_cell_size)
        grid_y = int(current_pos.y // self.fog_cell_size)
        # Erkunde auch benachbarte Zellen (Sichtradius)
        sight_range = 5  # 5 Zellen in jede Richtung
        for dx in range(-sight_range, sight_range + 1):
            for dy in range(-sight_range, sight_range + 1):
                self.explored_cells.add((grid_x + dx, grid_y + dy))
        
        # Berechne aktuelle Stats basierend auf Upgrades
        current_speed = self.base_speed * (1 + self.speed_level * 0.15)  # +15% pro Level
        current_speed_back = self.base_speed_back * (1 + self.speed_level * 0.15)
        current_shoot_cooldown = self.base_shoot_cooldown * (0.85 ** self.fire_rate_level)  # -15% pro Level
        current_repair_rate = self.base_repair_rate + self.regen_level * 1.5
        current_max_health = self.base_max_health + self.max_health_level * 20  # +20 HP pro Level
        current_damage = self.base_damage + self.damage_level * 10  # +10 Schaden pro Level

        # Temporäre Kisten-Boni
        current_speed *= (1 + self.crate_bonus_speed_pct)
        current_speed_back *= (1 + self.crate_bonus_speed_pct)
        current_shoot_cooldown *= max(0.35, 1 - self.crate_bonus_fire_rate_pct)
        current_repair_rate += self.crate_bonus_regen
        current_max_health += self.crate_bonus_max_health
        current_damage += self.crate_bonus_damage
        current_damage = int(current_damage * (1 + self.crate_bonus_damage_pct))

        # Schadensmodell: Je kaputter der Rumpf, desto schwächer und langsamer
        hp_ratio = max(0.0, min(1.0, self.health / max(1, current_max_health)))
        speed_damage_factor = 0.58 + 0.42 * hp_ratio
        damage_factor = 0.62 + 0.38 * hp_ratio
        current_speed *= speed_damage_factor
        current_speed_back *= speed_damage_factor
        current_damage = max(1, int(current_damage * damage_factor))
        
        # ==================== CREW-SYSTEM UPDATE ====================
        # Versuche Driver zu ersetzen wenn nötig
        driver_replacement_happened = self.crew.try_replace_driver(dt_seconds)
        gunner_replacement_happened = self.crew.try_replace_gunner(dt_seconds)
        if (driver_replacement_happened or gunner_replacement_happened) and hasattr(self, 'sfx'):
            self.sfx.play('levelup')  # Visuelles Feedback
        
        # Wenn Driver tot, können wir nicht fahren
        can_move = self.crew.driver_alive() and not self.crew.driver_needs_replacement
        
        # Wenn Schütze tot, können wir nicht schießen
        can_shoot = self.crew.gunner.is_alive and not self.crew.gunner_needs_replacement

        # Zusätzliche Crew-Effekte
        if not self.crew.loader.is_alive:
            current_shoot_cooldown *= 1.35
        if not self.crew.navigator.is_alive:
            current_speed *= 0.85
            current_speed_back *= 0.85
        if not self.crew.engineer.is_alive:
            current_repair_rate *= 0.6
        if not self.crew.boatswain.is_alive:
            current_damage = max(1, int(current_damage * 0.9))
        
        # Reduziere Geschwindigkeit wenn Driver gerade ersetzt wird
        if self.crew.driver_needs_replacement:
            replacement_progress = self.crew.driver_replacement_timer / self.crew.driver_replacement_duration
            current_speed *= (1 - replacement_progress)
            current_speed_back *= (1 - replacement_progress)

        # Aktive Reparatur: nur im Stand und bei gedrueckter R-Taste
        keys = pg.key.get_pressed()
        is_stationary = not keys[pg.K_w] and not keys[pg.K_s] and not keys[pg.K_a] and not keys[pg.K_d]
        wants_repair = keys[pg.K_r] and is_stationary and self.health < current_max_health
        if wants_repair:
            self.repair_hold_time += dt_seconds
            if self.repair_hold_time >= self.repair_channel_time:
                self.repairing = True
        else:
            self.repair_hold_time = 0.0
            self.repairing = False

        if self.repairing:
            self.health = min(current_max_health, self.health + current_repair_rate * dt_seconds)
        
        # Animation Timer aktualisieren
        self.animation_timer += dt_seconds
        
        # Schiffs-Modus
        old_cords = self.cords_schiff1.copy()
        old_richtung = self.schiff_richtung
        
        self.schiff = pg.transform.rotate(
            self.schiff1 if not self.moving else self.schiff2,
            self.schiff_richtung * -45,
        )

        # movement
        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff=pg.mask.from_surface(surface=self.schiff)
        
        # Prüfe ob Rotation zu Kollision führt
        offset = (self.schiff_rect.left - 0, self.schiff_rect.top - 0)
        if self.mask_insel.overlap(mask_schiff, offset):
            # Rotation zurücknehmen
            self.schiff_richtung = old_richtung
            self.schiff = pg.transform.rotate(
                self.schiff1 if not self.moving else self.schiff2,
                self.schiff_richtung * -45,
            )
            self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
            mask_schiff=pg.mask.from_surface(surface=self.schiff)
        else:
            # Prüfe Extra-Inseln
            rotation_collision = False
            for island_pos, island_scale, island_img, island_mask in self.extra_islands:
                island_rect = island_img.get_rect(center=island_pos)
                offset = (self.schiff_rect.left - island_rect.left, self.schiff_rect.top - island_rect.top)
                if island_mask.overlap(mask_schiff, offset):
                    rotation_collision = True
                    break
            
            if rotation_collision:
                # Rotation zurücknehmen
                self.schiff_richtung = old_richtung
                self.schiff = pg.transform.rotate(
                    self.schiff1 if not self.moving else self.schiff2,
                    self.schiff_richtung * -45,
                )
                self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
                mask_schiff=pg.mask.from_surface(surface=self.schiff)

        # actual movement with w and s
        if pg.key.get_pressed()[pg.K_w] and not self.repairing and can_move:
            self.cords_schiff1 += richtungen[self.schiff_richtung] * dt_seconds * current_speed
            self.moving = True
            
            # Sofort nach Bewegung Kollision prüfen
            self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
            mask_schiff=pg.mask.from_surface(surface=self.schiff)
            
            # Haupt-Insel
            offset = (self.schiff_rect.left - 0, self.schiff_rect.top - 0)
            if self.mask_insel.overlap(mask_schiff, offset):
                self.cords_schiff1 = old_cords
                self.take_damage(5)
            else:
                # Extra-Inseln prüfen
                collision = False
                for island_pos, island_scale, island_img, island_mask in self.extra_islands:
                    island_rect = island_img.get_rect(center=island_pos)
                    offset = (self.schiff_rect.left - island_rect.left, self.schiff_rect.top - island_rect.top)
                    if island_mask.overlap(mask_schiff, offset):
                        self.cords_schiff1 = old_cords
                        self.take_damage(5)
                        collision = True
                        break
        else:
            self.moving = False

        if pg.key.get_pressed()[pg.K_s] and not self.repairing and can_move:
            self.cords_schiff1 -= richtungen[self.schiff_richtung] * dt_seconds * current_speed_back
            
            # Sofort nach Bewegung Kollision prüfen
            self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
            mask_schiff=pg.mask.from_surface(surface=self.schiff)
            
            # Haupt-Insel
            offset = (self.schiff_rect.left - 0, self.schiff_rect.top - 0)
            if self.mask_insel.overlap(mask_schiff, offset):
                self.cords_schiff1 = old_cords
                self.take_damage(5)
            else:
                # Extra-Inseln prüfen
                for island_pos, island_scale, island_img, island_mask in self.extra_islands:
                    island_rect = island_img.get_rect(center=island_pos)
                    offset = (self.schiff_rect.left - island_rect.left, self.schiff_rect.top - island_rect.top)
                    if island_mask.overlap(mask_schiff, offset):
                        self.cords_schiff1 = old_cords
                        self.take_damage(5)
                        break
        
        # Schießen mit Leertaste
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt_seconds
        
        if pg.key.get_pressed()[pg.K_SPACE] and self.shoot_cooldown <= 0 and not self.repairing and can_shoot:
            # Breitseite schießen (links und rechts), inkl. Multishot-Artefakte
            shoot_dir = richtungen[self.schiff_richtung]
            left_dir = pg.Vector2(-shoot_dir.y, shoot_dir.x)
            right_dir = pg.Vector2(shoot_dir.y, -shoot_dir.x)
            shots_per_side = 1 + self.crate_bonus_extra_shots
            for base_dir in (left_dir, right_dir):
                for i in range(shots_per_side):
                    # Faecher-Streuung bei mehreren Schuessen
                    spread = 0.0 if shots_per_side == 1 else (i - (shots_per_side - 1) / 2) * 9.0
                    self.cannonballs.append(self._make_player_ball(self.cords_schiff1, base_dir.rotate(spread)))
            self.shoot_cooldown = current_shoot_cooldown
            if hasattr(self, 'sfx'):
                self.sfx.play('cannon')

        # Finale Position für weitere Kollisionen
        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff=pg.mask.from_surface(surface=self.schiff)
        
        # Stein-Kollision prüfen (mit Distance-Culling + gecachter Maske)
        for rock_pos, rock_img, rock_mask in self.rocks:
            if self.cords_schiff1.distance_squared_to(rock_pos) > 90000:  # 300px Radius
                continue
            rock_rect = rock_img.get_rect(center=rock_pos)
            offset = (self.schiff_rect.left - rock_rect.left, self.schiff_rect.top - rock_rect.top)
            if rock_mask.overlap(mask_schiff, offset):
                self.cords_schiff1 = old_cords
                # Zusaetzlich vom Stein wegdruecken, damit man nicht stecken bleibt
                push_dir = self.cords_schiff1 - rock_pos
                if push_dir.length_squared() > 0:
                    push_dir = push_dir.normalize()
                    self.cords_schiff1 += push_dir * 24
                self.take_damage(5)
                break
        
        # Falls wir trotz Ruecksetzen noch in einem Stein sind: mehrfach aus dem Stein schieben
        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff = pg.mask.from_surface(surface=self.schiff)
        for rock_pos, rock_img, rock_mask in self.rocks:
            if self.cords_schiff1.distance_squared_to(rock_pos) > 122500:
                continue
            rock_rect = rock_img.get_rect(center=rock_pos)
            offset = (self.schiff_rect.left - rock_rect.left, self.schiff_rect.top - rock_rect.top)
            if rock_mask.overlap(mask_schiff, offset):
                push = self.cords_schiff1 - rock_pos
                if push.length_squared() == 0:
                    push = pg.Vector2(1, 0)
                push = push.normalize()
                for _ in range(6):
                    self.cords_schiff1 += push * 8
                    self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
                    offset = (self.schiff_rect.left - rock_rect.left, self.schiff_rect.top - rock_rect.top)
                    if not rock_mask.overlap(mask_schiff, offset):
                        break
                break

        # NPC-Schiff Kollision mit Spieler prüfen
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue
            if self.cords_schiff1.distance_squared_to(npc_ship.pos) > 160000:  # 400px Culling
                continue
            collided = False
            if npc_ship.is_boss:
                player_hit_r = 34
                collided = self.cords_schiff1.distance_squared_to(npc_ship.pos) <= (npc_ship.hit_radius + player_hit_r) ** 2
            else:
                npc_img = npc_ship.get_image()
                npc_mask = npc_ship.get_mask()
                npc_rect = npc_img.get_rect(center=npc_ship.pos)
                offset = (self.schiff_rect.left - npc_rect.left, self.schiff_rect.top - npc_rect.top)
                collided = npc_mask.overlap(mask_schiff, offset) is not None

            if collided:
                # Spieler zurücksetzen
                self.cords_schiff1 = old_cords
                self.take_damage(5)
                # Ramm-Schaden-Artefakt: Gegner bei Kontakt beschaedigen
                if self.crate_bonus_ram_damage > 0:
                    npc_ship.health -= self.crate_bonus_ram_damage
                    self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -30), self.crate_bonus_ram_damage, (255, 200, 120)))
                    if npc_ship.health <= 0:
                        self._kill_enemy(npc_ship)
                # NPC wegschubsen
                push_dir = npc_ship.pos - self.cords_schiff1
                if push_dir.length() > 0:
                    push_dir = push_dir.normalize()
                    npc_ship.pos += push_dir * 10
                break
        
        # NPC-Schiffe aktualisieren (verfolgen den Spieler, mit Kollision)
        player_target = self.cords_schiff1
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue  # Tote Schiffe nicht mehr bewegen!
            was_aggroed = npc_ship.boss_aggroed if npc_ship.is_boss else False
            npc_ship.update(dt, self.world_size, player_target, self.mask_insel, self.insel, self.rocks, self.extra_islands)
            
            # Boss-Aggro Sound (nur beim ersten Mal)
            if npc_ship.is_boss and npc_ship.boss_aggroed and not was_aggroed:
                if hasattr(self, 'sfx'):
                    self.sfx.play('boss_spawn')
                if self.boss_arena is None:
                    self._start_boss_arena(npc_ship)
            
            # NPC versucht zu schießen
            ball = npc_ship.try_shoot(player_target)
            if ball is not None:
                self.cannonballs.append(ball)

        # Boss-Arena und Phasenangriffe
        self._update_boss_encounter(dt_seconds)
        
        # Kanonenkugeln aktualisieren
        for ball in self.cannonballs:
            ball.update(dt_seconds)
        
        # Kanonenkugeln gegen NPC-Schiffe prüfen (nur Spieler-Kugeln)
        # current_damage wurde weiter oben inklusive Damage-Model berechnet
        for ball in self.cannonballs:
            if ball.is_dead or ball.is_enemy:
                continue
            ball_hit_ids = getattr(ball, 'hit_ids', None)
            for npc_ship in self.npc_ships:
                if npc_ship.is_dead:
                    continue
                # Bereits von dieser (durchschlagenden) Kugel getroffen?
                if ball_hit_ids is not None and id(npc_ship) in ball_hit_ids:
                    continue
                # Pixel-perfekte Hitbox mit Mask-Kollision
                npc_img = npc_ship.get_image()
                npc_rect = npc_img.get_rect(center=npc_ship.pos)
                ball_r = getattr(ball, 'radius', 10)
                ball_rect = pg.Rect(int(ball.pos.x) - ball_r, int(ball.pos.y) - ball_r, ball_r * 2, ball_r * 2)

                # Schneller Rect-Check zuerst (Performance)
                if not npc_rect.inflate(20, 20).colliderect(ball_rect):
                    continue

                # Feste Hitbox pro Schiff (groessere Kugeln = groessere Reichweite)
                hit_radius = getattr(npc_ship, 'hit_radius', 46) + (ball_r - 10)
                if ball.pos.distance_squared_to(npc_ship.pos) <= hit_radius * hit_radius:
                    # Kritischer Treffer (Artefakt)
                    hit_dmg = current_damage
                    is_crit = self.crate_bonus_crit_chance > 0 and random.random() < self.crate_bonus_crit_chance
                    if is_crit:
                        hit_dmg = int(hit_dmg * (2.0 + self.crate_bonus_crit_mult))
                    npc_ship.health -= hit_dmg

                    # Lebensraub-Artefakt
                    if self.crate_bonus_lifesteal > 0:
                        self._heal(hit_dmg * self.crate_bonus_lifesteal)

                    # Durchschlag-Artefakt: Kugel merkt sich Treffer und lebt weiter
                    if ball_hit_ids is None:
                        ball.hit_ids = ball_hit_ids = set()
                    ball_hit_ids.add(id(npc_ship))
                    if getattr(ball, 'pierce', 0) > 0:
                        ball.pierce -= 1
                    else:
                        ball.is_dead = True

                    # === PREMIUM EFFEKTE ===
                    self.explosions.append(ExplosionEffect(ball.pos, color=(255, 150, 50), size=25))
                    if is_crit:
                        self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -34), hit_dmg, (255, 130, 40), text=f"{hit_dmg}!"))
                    else:
                        self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -30), hit_dmg, (255, 255, 0)))
                    self.screen_shake = 0.15
                    self.screen_shake_intensity = 5
                    if hasattr(self, 'sfx'):
                        self.sfx.play('hit')

                    # Explosivmunition-Artefakt: AoE-Schaden auf Gegner in der Naehe
                    explosive = getattr(ball, 'explosive', 0)
                    if explosive > 0:
                        self.explosions.append(ExplosionEffect(ball.pos, color=(255, 120, 40), size=int(explosive * 0.6)))
                        aoe_dmg = max(1, int(hit_dmg * 0.5))
                        for other in self.npc_ships:
                            if other is npc_ship or other.is_dead:
                                continue
                            if ball.pos.distance_squared_to(other.pos) <= explosive * explosive:
                                other.health -= aoe_dmg
                                self.damage_numbers.append(DamageNumber(other.pos + pg.Vector2(0, -30), aoe_dmg, (255, 170, 80)))
                                if other.health <= 0:
                                    self._kill_enemy(other)

                    if npc_ship.health <= 0:
                        self._kill_enemy(npc_ship)

                    if ball.is_dead:
                        break
        
        # Feindliche Kugeln gegen Spieler prüfen
        for ball in self.cannonballs:
            if ball.is_dead or not ball.is_enemy:
                continue
            # Distanz zum Spieler
            dist = ball.pos.distance_to(self.cords_schiff1)
            if dist < 40:  # Treffer-Radius
                base_hit = getattr(ball, 'boss_damage', 10)
                # Schaden der NPC-Boote steigt mit der Zeit
                hit_damage = max(1, int(round(base_hit * self.get_enemy_damage_mult())))
                self.take_damage(hit_damage)  # Schaden je nach Quelle
                ball.is_dead = True
                # Explosion und Shake bei Treffer auf Spieler
                self.explosions.append(ExplosionEffect(ball.pos, color=(255, 50, 50), size=20 if hit_damage <= 10 else 35))
                self.damage_numbers.append(DamageNumber(self.cords_schiff1 + pg.Vector2(0, -30), hit_damage, (255, 50, 50)))
                self.screen_shake = 0.2
                self.screen_shake_intensity = 8
        
        # Tote Kugeln entfernen
        self.cannonballs = [b for b in self.cannonballs if not b.is_dead]
        
        # Aufsammel-Radius (Basis + Ausguck-Artefakt)
        pickup_bonus = self.crate_bonus_pickup_radius

        # Gems aktualisieren und Kollision prüfen
        for gem in self.gems:
            if gem.collected:
                continue
            gem.update(dt_seconds)

            # Kollision mit Spieler
            dist = gem.pos.distance_to(self.cords_schiff1)
            if dist < 50 + pickup_bonus:  # Einsammel-Radius
                gem.collected = True
                self.total_gems += 1
                save_gems(self.total_gems)  # Sofort speichern
                if hasattr(self, 'sfx'):
                    self.sfx.play('gem_pickup')

        # Kisten aktualisieren und einsammeln
        for crate in self.crates:
            if crate.collected:
                continue
            crate.update(dt_seconds)

            if crate.pos.distance_to(self.cords_schiff1) < 55 + pickup_bonus:
                crate.collected = True
                self._apply_random_crate_item()
                if hasattr(self, 'sfx'):
                    self.sfx.play('perk_buy')

                boosted_max_hp = self._current_max_health()
                if self.health > boosted_max_hp:
                    self.health = boosted_max_hp

        # Gelegentlich neue Gems spawnen (sehr selten)
        self.gem_spawn_timer += dt_seconds
        if self.gem_spawn_timer >= self.gem_spawn_interval:
            self.gem_spawn_timer = 0
            # 20% Chance auf neuen Gem
            if random.random() < 0.2:
                insel_w, insel_h = self.insel.get_size()
                while True:
                    x = random.randint(-int(self.world_size.x // 2), int(self.world_size.x // 2))
                    y = random.randint(-int(self.world_size.y // 2), int(self.world_size.y // 2))
                    if not (0 < x < insel_w and 0 < y < insel_h):
                        break
                self.gems.append(Gem(pg.Vector2(x, y)))

        # Alle 30 Sekunden eine neue Kiste irgendwo auf dem Wasser spawnen
        self.crate_spawn_timer += dt_seconds
        if self.crate_spawn_timer >= self.crate_spawn_interval:
            self.crate_spawn_timer = 0
            insel_w, insel_h = self.insel.get_size()
            attempts = 0
            while attempts < 100:
                attempts += 1
                x = random.randint(-int(self.world_size.x // 2), int(self.world_size.x // 2))
                y = random.randint(-int(self.world_size.y // 2), int(self.world_size.y // 2))
                pos = pg.Vector2(x, y)
                if 0 < x < insel_w and 0 < y < insel_h:
                    continue
                if pos.distance_to(self.cords_schiff1) < 300:
                    continue
                break
            self.crates.append(StatCrate(pos))
        
        # Respawn-Timer für tote NPCs
        insel_size = self.insel.get_size()
        player_target = self.cords_schiff1  # Immer Schiffsposition (on_foot entfernt)
        difficulty = self.get_difficulty()
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                if not getattr(npc_ship, 'can_respawn', True):
                    continue
                npc_ship.respawn_timer += dt_seconds
                if npc_ship.respawn_timer >= npc_ship.respawn_duration:
                    npc_ship.respawn_near_island(insel_size, player_target, difficulty)
            else:
                if not getattr(npc_ship, 'can_respawn', True):
                    continue
                # Prüfe ob NPC zu weit vom Spieler weg ist → respawn in Spielernähe
                dist_to_player = npc_ship.pos.distance_to(player_target)
                if dist_to_player > 2500:  # Wenn weiter als 2500 Pixel
                    npc_ship.respawn_near_island(insel_size, player_target, difficulty)
        
        # camera follows ship (smooth)
        camera_target = self.cords_schiff1
        self.camera_pos += (camera_target - self.camera_pos) * min(1, dt * self.cam_lerp)

        # zoom logic
        target_zoom = self.move_zoom if self.moving else self.base_zoom
        self.zoom += (target_zoom - self.zoom) * min(1, dt * self.zoom_speed)

        # ==================== PREMIUM EFFEKTE UPDATE ====================
        # Kielwasser spawnen wenn sich bewegt
        if self.moving:
            self.wake_spawn_timer += dt_seconds
            if self.wake_spawn_timer >= self.wake_spawn_interval:
                self.wake_spawn_timer = 0
                # Partikel hinter dem Schiff
                ship_back = self.cords_schiff1 - richtungen[self.schiff_richtung] * 40
                offset = pg.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
                self.wake_particles.append(WakeParticle(ship_back + offset, size=random.randint(5, 10)))
        
        # Wake-Partikel aktualisieren
        for wake in self.wake_particles:
            wake.update(dt_seconds)
        self.wake_particles = [w for w in self.wake_particles if not w.is_dead]
        # Limit Partikel-Anzahl für Performance
        if len(self.wake_particles) > 100:
            self.wake_particles = self.wake_particles[-100:]
        
        # Explosionen aktualisieren
        for explosion in self.explosions:
            explosion.update(dt_seconds)
        self.explosions = [e for e in self.explosions if not e.is_dead]
        
        # Splashes aktualisieren
        for splash in self.splashes:
            splash.update(dt_seconds)
        self.splashes = [s for s in self.splashes if not s.is_dead]
        
        # Schadenszahlen aktualisieren
        for dmg_num in self.damage_numbers:
            dmg_num.update(dt_seconds)
        self.damage_numbers = [d for d in self.damage_numbers if not d.is_dead]
        
        # Schiff-Schadensmodell aktualisieren
        self.ship_damage_model.update_damage(self.health, self.base_max_health + self.max_health_level * 20)
        self.ship_damage_model.update(dt_seconds, self.cords_schiff1)
        
        # Screen Shake abklingen
        if self.screen_shake > 0:
            self.screen_shake -= dt_seconds
        
        # Wellen-Animation
        self.wave_offset += dt_seconds * 2
        
        # Sonnenstrahl-Animation
        self.sun_rays_timer += dt_seconds
        for ray in self.sun_rays:
            ray['angle'] += ray['speed'] * dt_seconds

        # Achievement-Popups aktualisieren
        if hasattr(self, 'achievement_popups'):
            for popup in self.achievement_popups:
                popup['timer'] -= dt_seconds
            self.achievement_popups = [p for p in self.achievement_popups if p['timer'] > 0]
        

    def draw(self, s):
        """
        Whatever you want to draw
        s is the surface or screen you may draw to
        """
        w,h = pg.display.get_window_size()
        # rect = self.text.get_rect(center = (w//2, h//2))

        w, h = s.get_size()

        # An Land: eigener Zeichen-Zweig (Insel-Erkundung)
        if self.on_foot:
            return self._draw_on_foot(s, w, h)

        camera_surface = pg.Surface((w, h), pg.SRCALPHA)

        sx, sy = self.schiff_rect.center

        # ocean (dynamisch an Bildschirmgroesse angepasst, deckt alles ab)
        self._fill_ocean(camera_surface, w, h, sx, sy)

        # island (Haupt-Insel)
        insel_pos = pg.Vector2(0, 0) - self.camera_pos + pg.Vector2(w // 2, h // 2)
        camera_surface.blit(self.insel, insel_pos)
        
        # Extra-Inseln zeichnen
        for island_pos, island_scale, island_img, _island_mask in self.extra_islands:
            island_screen_pos = island_pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            island_rect = island_img.get_rect(center=island_screen_pos)
            camera_surface.blit(island_img, island_rect)

        # rocks (Steine) - mit Screen-Culling
        for rock_pos, rock_img, _rock_mask in self.rocks:
            if abs(rock_pos.x - self.camera_pos.x) > w // 2 + 100 or abs(rock_pos.y - self.camera_pos.y) > h // 2 + 100:
                continue
            rock_screen_pos = rock_pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            rock_rect = rock_img.get_rect(center=rock_screen_pos)
            camera_surface.blit(rock_img, rock_rect)

        # Boss-Arena (falls aktiv)
        arena_boss = self._get_active_arena_boss()
        if self.boss_arena is not None and arena_boss is not None:
            center = self.boss_arena['center'] - self.camera_pos + pg.Vector2(w // 2, h // 2)
            radius = int(self.boss_arena['radius'])
            pulse = abs(math.sin(self.survival_time * 2.6)) * 0.4 + 0.6
            arena_col = (255, 90, 70, int(70 * pulse))
            pg.draw.circle(camera_surface, arena_col, (int(center.x), int(center.y)), radius, 5)
            pg.draw.circle(camera_surface, (255, 130, 90, int(35 * pulse)), (int(center.x), int(center.y)), max(20, radius - 40), 2)

        # NPC-Schiffe zeichnen (mit Screen-Culling)
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue
            if abs(npc_ship.pos.x - self.camera_pos.x) > w // 2 + 150 or abs(npc_ship.pos.y - self.camera_pos.y) > h // 2 + 150:
                continue
            npc_img = npc_ship.get_image()
            npc_screen_pos = npc_ship.pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            npc_rect = npc_img.get_rect(center=npc_screen_pos)

            if npc_ship.is_boss:
                pulse = abs(math.sin(self.survival_time * 3.8 + npc_ship.pos.x * 0.01)) * 0.35 + 0.65
                glow_radius = max(16, int(max(npc_rect.width, npc_rect.height) * 0.42))
                glow_size = glow_radius * 4
                glow_surf = pg.Surface((glow_size, glow_size), pg.SRCALPHA)
                gc = glow_size // 2
                pg.draw.circle(glow_surf, (255, 50, 35, int(70 * pulse)), (gc, gc), glow_radius)
                pg.draw.circle(glow_surf, (255, 120, 60, int(35 * pulse)), (gc, gc), int(glow_radius * 0.6))
                camera_surface.blit(glow_surf, (npc_screen_pos.x - gc, npc_screen_pos.y - gc))

            camera_surface.blit(npc_img, npc_rect)
            
            # Lebensleiste über dem NPC-Schiff (nicht für Bosse - die haben eigene Bar)
            if not npc_ship.is_boss:
                npc_bar_width = 40
                npc_bar_height = 6
                npc_bar_x = npc_screen_pos.x - npc_bar_width // 2
                npc_bar_y = npc_rect.top - 10
                
                # Hintergrund (dunkelgrau)
                pg.draw.rect(camera_surface, (50, 50, 50), (npc_bar_x, npc_bar_y, npc_bar_width, npc_bar_height))
                
                # Leben (grün)
                max_hp = getattr(npc_ship, 'max_health', 100)
                npc_health_width = int(npc_bar_width * (npc_ship.health / max(1, max_hp)))
                if npc_health_width > 0:
                    pg.draw.rect(camera_surface, (0, 200, 0), (npc_bar_x, npc_bar_y, npc_health_width, npc_bar_height))
                
                # Rahmen
                pg.draw.rect(camera_surface, (255, 255, 255), (npc_bar_x, npc_bar_y, npc_bar_width, npc_bar_height), 1)
            else:
                # Boss: Schädel-Symbol über dem Schiff
                skull_x = int(npc_screen_pos.x)
                skull_y = npc_rect.top - 20
                pg.draw.circle(camera_surface, (200, 50, 50), (skull_x, skull_y), 8)
                pg.draw.circle(camera_surface, (255, 255, 255), (skull_x - 3, skull_y - 2), 2)
                pg.draw.circle(camera_surface, (255, 255, 255), (skull_x + 3, skull_y - 2), 2)

        # Schiff zeichnen
        ship_pos = self.schiff_rect.topleft - self.camera_pos + pg.Vector2(w // 2, h // 2)
        camera_surface.blit(self.schiff, ship_pos)
        
        # Schiff-Schadenseffekte (Löcher) auf dem Schiff zeichnen
        self.ship_damage_model.draw_on_ship(camera_surface, ship_pos + pg.Vector2(self.schiff.get_width() // 2, self.schiff.get_height() // 2))
        
        # Gems zeichnen
        offset = self.camera_pos - pg.Vector2(w // 2, h // 2)
        for crate in self.crates:
            crate.draw(camera_surface, offset)
        for gem in self.gems:
            gem.draw(camera_surface, offset)
        
        # Kanonenkugeln zeichnen
        for ball in self.cannonballs:
            ball.draw(camera_surface, offset)
        
        # ==================== PREMIUM EFFEKTE ZEICHNEN ====================
        # Kielwasser zeichnen (hinter anderen Objekten)
        for wake in self.wake_particles:
            wake.draw(camera_surface, offset)
        
        # Explosionen zeichnen
        for explosion in self.explosions:
            explosion.draw(camera_surface, offset)
        
        # Splashes zeichnen
        for splash in self.splashes:
            splash.draw(camera_surface, offset)
        
        # Schadenszahlen zeichnen
        for dmg_num in self.damage_numbers:
            dmg_num.draw(camera_surface, offset)
        
        # Schiff-Feuer- und Raucheffekte zeichnen
        self.ship_damage_model.draw_effects(camera_surface, offset)
        
        # Sonnenstrahl-Overlay entfernt (Performance - kaum sichtbar aber teuer)

        # zoom
        scaled = pg.transform.scale(
            camera_surface,
            (int(w * self.zoom), int(h * self.zoom))
        )

        zoom_rect = scaled.get_rect(center=(w // 2, h // 2))
        
        # Screen Shake anwenden
        if self.screen_shake > 0:
            shake_x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            zoom_rect.x += int(shake_x)
            zoom_rect.y += int(shake_y)

        # Grundfarbe fuellen, damit Zoom/Screen-Shake keine schwarzen Raender zeigen
        if hasattr(self, '_ocean_bg_color'):
            s.fill(self._ocean_bg_color)
        s.blit(scaled, zoom_rect)
        
        # ==================== PREMIUM UI ====================
        # Berechne max health für Anzeige
        current_max_health = self.base_max_health + self.max_health_level * 20 + self.crate_bonus_max_health
        
        # UI Panel unten links (halbtransparent)
        ui_panel = pg.Surface((250, 100), pg.SRCALPHA)
        pg.draw.rect(ui_panel, (0, 0, 0, 150), (0, 0, 250, 100), border_radius=10)
        pg.draw.rect(ui_panel, (100, 100, 100, 200), (0, 0, 250, 100), width=2, border_radius=10)
        s.blit(ui_panel, (10, h - 110))

        # Lebensleiste
        bar_width = 200
        bar_height = 24
        bar_x = 30
        bar_y = h - 95

        pg.draw.rect(s, (0, 0, 0, 100), (bar_x + 2, bar_y + 2, bar_width, bar_height), border_radius=5)
        pg.draw.rect(s, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=5)

        health_width = int(bar_width * (self.health / max(1, current_max_health)))
        if health_width > 0:
            if self.health > current_max_health * 0.6:
                bar_color = (50, 200, 50)
            elif self.health > current_max_health * 0.3:
                bar_color = (200, 200, 50)
            else:
                bar_color = (200, 50, 50)
            pg.draw.rect(s, bar_color, (bar_x, bar_y + 2, health_width, bar_height - 4), border_radius=3)

        pg.draw.rect(s, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        hp_str = f"{int(self.health)}/{current_max_health}"
        hp_shadow = self.font_small.render(hp_str, True, (0, 0, 0))
        hp_text = self.font_small.render(hp_str, True, (255, 255, 255))
        text_x = bar_x + bar_width // 2 - hp_text.get_width() // 2
        s.blit(hp_shadow, (text_x + 1, bar_y + 4))
        s.blit(hp_text, (text_x, bar_y + 3))

        heart_color = (255, 80, 80) if self.health > current_max_health * 0.3 else (150, 50, 50)
        pg.draw.circle(s, heart_color, (bar_x - 15, bar_y + bar_height // 2), 8)
        pg.draw.circle(s, (255, 150, 150), (bar_x - 17, bar_y + bar_height // 2 - 2), 3)

        # EXP-Leiste
        exp_bar_y = h - 60
        exp_bar_height = 16
        
        # Schatten und Hintergrund
        pg.draw.rect(s, (0, 0, 0, 100), (bar_x + 2, exp_bar_y + 2, bar_width, exp_bar_height), border_radius=4)
        pg.draw.rect(s, (20, 20, 50), (bar_x, exp_bar_y, bar_width, exp_bar_height), border_radius=4)
        
        # EXP (einfacher blauer Balken statt Pixel-Gradient)
        exp_width = int(bar_width * (self.exp / self.exp_to_level))
        if exp_width > 0:
            pg.draw.rect(s, (50, 130, 220), (bar_x, exp_bar_y + 2, exp_width, exp_bar_height - 4), border_radius=3)
        
        pg.draw.rect(s, (150, 150, 200), (bar_x, exp_bar_y, bar_width, exp_bar_height), 2, border_radius=4)
        
        # Level Badge
        level_badge = pg.Surface((50, 25), pg.SRCALPHA)
        pg.draw.rect(level_badge, (50, 50, 150, 220), (0, 0, 50, 25), border_radius=5)
        pg.draw.rect(level_badge, (150, 150, 255), (0, 0, 50, 25), 2, border_radius=5)
        level_text = self.font_small.render(f"Lv{self.level}", True, (255, 255, 255))
        level_badge.blit(level_text, (25 - level_text.get_width() // 2, 3))
        s.blit(level_badge, (bar_x + bar_width + 10, exp_bar_y - 3))
        
        # Stats Panel oben links
        stats_panel = pg.Surface((160, 128), pg.SRCALPHA)
        pg.draw.rect(stats_panel, (0, 0, 0, 150), (0, 0, 160, 128), border_radius=8)
        pg.draw.rect(stats_panel, (100, 100, 100, 200), (0, 0, 160, 128), width=2, border_radius=8)
        s.blit(stats_panel, (10, 10))
        
        # Kill-Counter mit Icon
        skull_color = (200, 80, 80)
        pg.draw.circle(s, skull_color, (30, 35), 10)
        pg.draw.circle(s, (255, 255, 255), (27, 33), 3)
        pg.draw.circle(s, (255, 255, 255), (33, 33), 3)
        kill_text = self.font_main.render(f"{self.kills}", True, (255, 100, 100))
        s.blit(kill_text, (50, 22))
        
        # Gem-Counter mit Icon
        gem_color = (255, 200, 50)
        points = [(30, 50), (40, 60), (30, 70), (20, 60)]
        pg.draw.polygon(s, gem_color, points)
        pg.draw.polygon(s, (255, 255, 200), points, 2)
        pg.draw.circle(s, (255, 255, 255), (27, 57), 3)
        gem_text = self.font_main.render(f"{self.total_gems}", True, gem_color)
        s.blit(gem_text, (50, 52))

        # Muenzen-Counter mit Icon (Pro-Run-Waehrung)
        coin_color = (230, 180, 60)
        pg.draw.circle(s, coin_color, (30, 87), 9)
        pg.draw.circle(s, (255, 235, 150), (30, 87), 9, 2)
        pg.draw.circle(s, (255, 245, 200), (27, 84), 2)
        coin_text = self.font_main.render(f"{self.coins}", True, (255, 220, 120))
        s.blit(coin_text, (50, 78))

        # Survival-Zeit
        survival_minutes = int(self.survival_time // 60)
        survival_seconds = int(self.survival_time % 60)
        time_text = self.font_small.render(f"{survival_minutes}:{survival_seconds:02d}", True, (200, 200, 255))
        s.blit(time_text, (50, 106))

        # Aktive Piratenklasse
        pirate_name = getattr(self, 'selected_pirate_name', 'Balanced Captain')
        pirate_text = self.font_small.render(pirate_name, True, (140, 220, 255))
        s.blit(pirate_text, (10, 96))
        
        # Highscore-Anzeige unter dem Stats-Panel
        hs = self.highscore
        hs_time = hs.get('survival_time', 0)
        hs_min = int(hs_time // 60)
        hs_sec = int(hs_time % 60)
        hs_kills = hs.get('kills', 0)
        
        hs_panel = pg.Surface((160, 52), pg.SRCALPHA)
        pg.draw.rect(hs_panel, (0, 0, 0, 120), (0, 0, 160, 52), border_radius=8)
        pg.draw.rect(hs_panel, (255, 200, 50, 120), (0, 0, 160, 52), width=1, border_radius=8)
        
        # Prüfe ob aktueller Run den Highscore schlägt
        hs_panel_y = 115
        if getattr(self, 'xp_booster_active', False) and getattr(self, 'xp_booster_remaining', 0) > 0:
            hs_panel_y = 145  # Unter dem XP Booster
        s.blit(hs_panel, (10, hs_panel_y))
        
        # Krone/Pokal Icon
        crown_color = (255, 200, 50)
        cx, cy = 28, hs_panel_y + 16
        pg.draw.polygon(s, crown_color, [(cx-8, cy+4), (cx-6, cy-6), (cx-2, cy), (cx+2, cy-8), (cx+6, cy), (cx+10, cy-6), (cx+12, cy+4)])
        pg.draw.rect(s, crown_color, (cx-8, cy+4, 20, 4))
        
        hs_label = self.font_small.render("Highscore", True, (255, 220, 100))
        s.blit(hs_label, (48, hs_panel_y + 4))
        
        hs_info = self.font_small.render(f"{hs_min}:{hs_sec:02d}  |  {hs_kills} Kills", True, (200, 200, 220))
        s.blit(hs_info, (48, hs_panel_y + 26))
        
        # XP Booster Anzeige
        if getattr(self, 'xp_booster_active', False) and getattr(self, 'xp_booster_remaining', 0) > 0:
            boost_mins = int(self.xp_booster_remaining // 60)
            boost_secs = int(self.xp_booster_remaining % 60)
            boost_pulse = abs(math.sin(self.survival_time * 3)) * 0.3 + 0.7
            boost_color = (int(180 * boost_pulse), int(100 * boost_pulse), int(255 * boost_pulse))
            
            # Hintergrund-Box
            boost_box = pg.Surface((160, 28), pg.SRCALPHA)
            pg.draw.rect(boost_box, (40, 20, 80, 180), (0, 0, 160, 28), border_radius=6)
            pg.draw.rect(boost_box, boost_color, (0, 0, 160, 28), 2, border_radius=6)
            s.blit(boost_box, (10, 100))
            
            boost_text = f"2x XP  {boost_mins}:{boost_secs:02d}"
            boost_surf = self.font_small.render(boost_text, True, boost_color)
            s.blit(boost_surf, (18, 103))
        
        # ==================== BOSS HEALTH BAR ====================
        # Finde den nächsten lebenden Boss der aggroed ist oder nah genug
        active_boss = None
        for npc_ship in self.npc_ships:
            if npc_ship.is_boss and not npc_ship.is_dead:
                dist_to_boss = self.cords_schiff1.distance_to(npc_ship.pos)
                # Nur anzeigen wenn Boss aggroed oder innerhalb 600px
                if npc_ship.boss_aggroed or dist_to_boss < 600:
                    if active_boss is None or dist_to_boss < self.cords_schiff1.distance_to(active_boss.pos):
                        active_boss = npc_ship
        
        if active_boss is not None:
            boss_bar_w = min(400, w - 100)
            boss_bar_h = 28
            boss_bar_x = w // 2 - boss_bar_w // 2
            boss_bar_y = 20
            phase = 1
            if self.boss_arena is not None and self.boss_arena.get('boss') is active_boss:
                phase = int(self.boss_arena.get('phase', 1))
            
            # Hintergrund-Panel
            boss_panel = pg.Surface((boss_bar_w + 40, boss_bar_h + 40), pg.SRCALPHA)
            pg.draw.rect(boss_panel, (0, 0, 0, 180), (0, 0, boss_bar_w + 40, boss_bar_h + 40), border_radius=10)
            pg.draw.rect(boss_panel, (180, 50, 50, 200), (0, 0, boss_bar_w + 40, boss_bar_h + 40), 3, border_radius=10)
            s.blit(boss_panel, (boss_bar_x - 20, boss_bar_y - 10))
            
            # "BOSS" Titel
            boss_title = self.font_small.render("BOSS", True, (255, 80, 80))
            s.blit(boss_title, (boss_bar_x, boss_bar_y - 6))

            phase_text = self.font_small.render(f"Phase {phase}", True, (255, 180, 120))
            s.blit(phase_text, (boss_bar_x + 56, boss_bar_y - 6))
            
            # Distanz-Anzeige
            boss_dist = int(self.cords_schiff1.distance_to(active_boss.pos))
            dist_text = self.font_small.render(f"{boss_dist}m", True, (200, 200, 200))
            s.blit(dist_text, (boss_bar_x + boss_bar_w - dist_text.get_width(), boss_bar_y - 6))
            
            # Lebensbalken
            pg.draw.rect(s, (40, 10, 10), (boss_bar_x, boss_bar_y + 14, boss_bar_w, boss_bar_h), border_radius=5)
            boss_max = max(1, active_boss.max_health)
            boss_health_w = int(boss_bar_w * (active_boss.health / boss_max))
            if boss_health_w > 0:
                # Einfacher roter Balken statt Pixel-Gradient (PERFORMANCE)
                pg.draw.rect(s, (200, 50, 20), (boss_bar_x, boss_bar_y + 16, boss_health_w, boss_bar_h - 4), border_radius=3)
            
            pg.draw.rect(s, (255, 100, 80), (boss_bar_x, boss_bar_y + 14, boss_bar_w, boss_bar_h), 2, border_radius=5)
            
            # HP-Text
            boss_hp_str = f"{int(active_boss.health)}/{boss_max}"
            boss_hp_text = self.font_small.render(boss_hp_str, True, (255, 255, 255))
            s.blit(boss_hp_text, (boss_bar_x + boss_bar_w // 2 - boss_hp_text.get_width() // 2, boss_bar_y + 18))

        # ==================== ARTEFAKT-HUD (Marker, aktive Artefakte, Popup) ====================
        self._draw_crate_hud(s, w, h)

        # Hinweis zum Aussteigen, wenn das Schiff an einer Insel liegt
        if not self.on_foot and self._near_landing():
            hint = self.font_main.render("[E] An Land gehen", True, (255, 230, 140))
            hb = pg.Surface((hint.get_width() + 20, hint.get_height() + 10), pg.SRCALPHA)
            pg.draw.rect(hb, (18, 24, 40, 210), hb.get_rect(), border_radius=8)
            pg.draw.rect(hb, (120, 200, 255), hb.get_rect(), 2, border_radius=8)
            hb.blit(hint, (10, 5))
            s.blit(hb, ((w - hb.get_width()) // 2, h - 70))

        # ==================== CREW HUD (oben rechts) ====================
        self.crew.draw_hud(s, w, h)
        
        # ==================== SHIP-MODELL (neben Crew HUD) ====================
        self.crew.draw_ship_model(s, w, h)

        # Achievement-Popups
        if hasattr(self, 'achievement_popups') and self.achievement_popups:
            pop_font = pg.font.SysFont("Arial", 18, bold=True)
            py = 20
            for popup in self.achievement_popups[:3]:
                alpha_factor = min(1.0, popup['timer'] / 1.0)
                box_w = min(w - 40, 760)
                box_h = 32
                box_x = w // 2 - box_w // 2
                box = pg.Surface((box_w, box_h), pg.SRCALPHA)
                pg.draw.rect(box, (25, 45, 30, int(200 * alpha_factor)), (0, 0, box_w, box_h), border_radius=8)
                pg.draw.rect(box, (120, 220, 150, int(220 * alpha_factor)), (0, 0, box_w, box_h), 2, border_radius=8)
                s.blit(box, (box_x, py))
                txt = pop_font.render(popup['text'], True, (220, 255, 230))
                s.blit(txt, (box_x + 12, py + 6))
                py += 38
        
        # Skill-Punkte Anzeige (oben rechts) - verbessertes Design
        if self.skill_points > 0:
            skill_panel_w = 260
            skill_panel_h = 180
            skill_panel = pg.Surface((skill_panel_w, skill_panel_h), pg.SRCALPHA)
            pg.draw.rect(skill_panel, (0, 0, 0, 180), (0, 0, skill_panel_w, skill_panel_h), border_radius=10)
            pg.draw.rect(skill_panel, (255, 200, 50, 200), (0, 0, skill_panel_w, skill_panel_h), width=3, border_radius=10)

            # Über HP/XP-Leiste positionieren
            skill_panel_x = 10
            skill_panel_y = h - 300
            s.blit(skill_panel, (skill_panel_x, skill_panel_y))
            
            # Titel
            title_text = self.font_main.render(f"✨ Skill Points: {self.skill_points}", True, (255, 220, 100))
            s.blit(title_text, (skill_panel_x + 15, skill_panel_y + 10))
            
            upgrade_texts = [
                f"[1] 🚀 Speed ({self.speed_level})",
                f"[2] 🔥 Fire Rate ({self.fire_rate_level})",
                f"[3] � Repair ({self.regen_level})",
                f"[4] ❤️ Health ({self.max_health_level})",
                f"[5] 💥 Damage ({self.damage_level})"
            ]
            for i, text in enumerate(upgrade_texts):
                rendered = self.font_small.render(text, True, (255, 255, 255))
                s.blit(rendered, (skill_panel_x + 18, skill_panel_y + 46 + i * 26))

        # Reparatur-Hinweis
        if self.health < current_max_health and not self.is_dead:
            if self.repairing:
                repair_text = "Repairing..."
                repair_col = (120, 255, 170)
            else:
                repair_text = "Hold R while standing still to repair"
                repair_col = (170, 210, 240)
            repair_surf = self.font_small.render(repair_text, True, repair_col)
            s.blit(repair_surf, (30, h - 130))
        
        # ==================== KLEINE MINIMAP (unten rechts) ====================
        minimap_size = 170
        minimap_padding = 15
        minimap_x = w - minimap_size - minimap_padding
        minimap_y = h - minimap_size - minimap_padding

        # Runder Minimap-Hintergrund
        minimap = pg.Surface((minimap_size, minimap_size), pg.SRCALPHA)

        # Ozean-Gradient als Hintergrund
        center = minimap_size // 2
        for r in range(center, 0, -1):
            t = r / center
            cr = int(10 + 20 * (1 - t))
            cg = int(25 + 35 * (1 - t))
            cb = int(55 + 50 * (1 - t))
            pg.draw.circle(minimap, (cr, cg, cb, 220), (center, center), r)

        # Subtile Wellen-Textur
        wave_timer = getattr(self, 'wave_offset', 0)
        for wy in range(0, minimap_size, 8):
            wave_x_off = math.sin(wy * 0.15 + wave_timer * 2) * 3
            pg.draw.line(minimap, (30, 55, 100, 40),
                         (int(wave_x_off), wy), (minimap_size + int(wave_x_off), wy))

        # Skalierung und Sichtweite
        mini_view_range = 800
        scale = minimap_size / (mini_view_range * 2)
        mini_offset_x = self.cords_schiff1.x - mini_view_range
        mini_offset_y = self.cords_schiff1.y - mini_view_range

        # Insel auf Minimap — skaliertes echtes Bild statt Rechteck
        insel_w, insel_h = self.insel.get_size()
        insel_mini_x = (0 - mini_offset_x) * scale
        insel_mini_y = (0 - mini_offset_y) * scale
        insel_mini_w = max(1, int(insel_w * scale))
        insel_mini_h = max(1, int(insel_h * scale))
        if (insel_mini_x + insel_mini_w > 0 and insel_mini_x < minimap_size and
            insel_mini_y + insel_mini_h > 0 and insel_mini_y < minimap_size and
            insel_mini_w > 2 and insel_mini_h > 2):
            # Cache skaliertes Bild für Performance
            cache_key = (insel_mini_w, insel_mini_h)
            if not hasattr(self, '_mini_insel_cache') or self._mini_insel_cache_key != cache_key:
                self._mini_insel_cache = pg.transform.smoothscale(self.insel, cache_key)
                self._mini_insel_cache_key = cache_key
            minimap.blit(self._mini_insel_cache, (insel_mini_x, insel_mini_y))

        # Extra-Inseln auf Minimap — skalierte echte Bilder
        for island_pos, island_scale, island_img, _island_mask in self.extra_islands:
            ei_mini_x = (island_pos.x - mini_offset_x) * scale
            ei_mini_y = (island_pos.y - mini_offset_y) * scale
            ei_mini_w = max(1, int(island_img.get_width() * scale))
            ei_mini_h = max(1, int(island_img.get_height() * scale))
            if (ei_mini_x + ei_mini_w > -ei_mini_w and ei_mini_x < minimap_size + ei_mini_w and
                ei_mini_y + ei_mini_h > -ei_mini_h and ei_mini_y < minimap_size + ei_mini_h and
                ei_mini_w > 2 and ei_mini_h > 2):
                ei_scaled = pg.transform.smoothscale(island_img, (ei_mini_w, ei_mini_h))
                minimap.blit(ei_scaled, (ei_mini_x - ei_mini_w // 2, ei_mini_y - ei_mini_h // 2))

        # Gems auf Minimap (als kleine goldene Punkte)
        for gem in getattr(self, 'gems', []):
            if gem.collected:
                continue
            gx = (gem.pos.x - mini_offset_x) * scale
            gy = (gem.pos.y - mini_offset_y) * scale
            if 4 < gx < minimap_size - 4 and 4 < gy < minimap_size - 4:
                pg.draw.circle(minimap, (255, 220, 60, 180), (int(gx), int(gy)), 2)

        # Steine auf Minimap (als stilisierte Punkte)
        for rock_pos, _rock_img, _rock_mask in self.rocks:
            rock_mini_x = (rock_pos.x - mini_offset_x) * scale
            rock_mini_y = (rock_pos.y - mini_offset_y) * scale
            if 4 < rock_mini_x < minimap_size - 4 and 4 < rock_mini_y < minimap_size - 4:
                pg.draw.circle(minimap, (90, 85, 75, 180), (int(rock_mini_x), int(rock_mini_y)), 2)

        # NPC-Schiffe auf Minimap (mit Glow und Boss-Highlight)
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue
            npc_mini_x = (npc_ship.pos.x - mini_offset_x) * scale
            npc_mini_y = (npc_ship.pos.y - mini_offset_y) * scale
            if 3 < npc_mini_x < minimap_size - 3 and 3 < npc_mini_y < minimap_size - 3:
                nx, ny = int(npc_mini_x), int(npc_mini_y)
                is_boss = getattr(npc_ship, 'is_boss', False)
                if is_boss:
                    # Boss: größerer roter Punkt mit Glow
                    pg.draw.circle(minimap, (255, 30, 30, 60), (nx, ny), 6)
                    pg.draw.circle(minimap, (255, 50, 50), (nx, ny), 4)
                    pg.draw.circle(minimap, (255, 200, 200), (nx, ny), 4, 1)
                else:
                    # Normal: kleiner roter Punkt
                    pg.draw.circle(minimap, (255, 60, 60, 80), (nx, ny), 4)
                    pg.draw.circle(minimap, (255, 80, 80), (nx, ny), 3)

        # Spieler auf Minimap — Pfeil mit Glow
        player_cx = minimap_size // 2
        player_cy = minimap_size // 2
        direction = richtungen[self.schiff_richtung]
        arrow_len = 9
        arrow_w = 6

        tip = (player_cx + direction.x * arrow_len, player_cy + direction.y * arrow_len)
        perp = pg.Vector2(-direction.y, direction.x)
        left = (player_cx - direction.x * arrow_len * 0.5 + perp.x * arrow_w,
                player_cy - direction.y * arrow_len * 0.5 + perp.y * arrow_w)
        right = (player_cx - direction.x * arrow_len * 0.5 - perp.x * arrow_w,
                 player_cy - direction.y * arrow_len * 0.5 - perp.y * arrow_w)

        # Glow
        pg.draw.circle(minimap, (50, 255, 100, 40), (player_cx, player_cy), 12)
        # Pfeil
        pg.draw.polygon(minimap, (50, 255, 100), [tip, left, right])
        pg.draw.polygon(minimap, (200, 255, 220), [tip, left, right], 1)

        # Kreis-Maske über die Minimap legen (runde Form)
        # Schnelle Methode: schwarzes Surface mit transparentem Kreis als Rahmen
        frame_surf = pg.Surface((minimap_size, minimap_size), pg.SRCALPHA)
        frame_surf.fill((0, 0, 0, 255))  # Komplett schwarz
        pg.draw.circle(frame_surf, (0, 0, 0, 0), (center, center), center - 2)  # Loch stanzen
        minimap.blit(frame_surf, (0, 0))  # Schwarz überall außerhalb des Kreises

        # Äußerer Ring (Kompass-Stil)
        pg.draw.circle(minimap, (80, 100, 140), (center, center), center - 1, 3)
        pg.draw.circle(minimap, (140, 170, 220, 120), (center, center), center - 3, 1)

        # Kompass-Markierungen (N, S, O, W)
        compass_font = pg.font.SysFont("Arial", 11, bold=True)
        compass_labels = [("N", 0, -1), ("S", 0, 1), ("E", 1, 0), ("W", -1, 0)]
        for label, dx, dy in compass_labels:
            cx = center + int(dx * (center - 12))
            cy = center + int(dy * (center - 12))
            lbl = compass_font.render(label, True, (180, 200, 230))
            minimap.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

        # Glanz-Effekt oben
        shine = pg.Surface((minimap_size, minimap_size // 2), pg.SRCALPHA)
        for sy in range(minimap_size // 4):
            a = max(0, 25 - sy)
            pg.draw.line(shine, (255, 255, 255, a), (0, sy), (minimap_size, sy))
        minimap.blit(shine, (0, 0))

        s.blit(minimap, (minimap_x, minimap_y))

        # "MAP" Label unter der Minimap
        map_label = self.font_small.render("M - Map", True, (140, 160, 200))
        s.blit(map_label, (minimap_x + minimap_size // 2 - map_label.get_width() // 2, minimap_y + minimap_size + 4))

        # ==================== GROSSE WELTKARTE (wenn M gedrückt) ====================
        if self.show_big_minimap:
            # Halbtransparenter Overlay mit Vignette
            overlay = pg.Surface((w, h), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            s.blit(overlay, (0, 0))

            big_map_size = min(w, h) - 100
            big_map_x = (w - big_map_size) // 2
            big_map_y = (h - big_map_size) // 2
            bm_center = big_map_size // 2

            big_map = pg.Surface((big_map_size, big_map_size), pg.SRCALPHA)

            # Ozean-Gradient Hintergrund (dunkel für unerkundete Bereiche)
            for by in range(0, big_map_size, 2):
                t = by / big_map_size
                br = int(4 + 10 * t)
                bg_c = int(8 + 18 * t)
                bb = int(22 + 30 * t)
                pg.draw.line(big_map, (br, bg_c, bb, 255), (0, by), (big_map_size, by))
                pg.draw.line(big_map, (br, bg_c, bb, 255), (0, by + 1), (big_map_size, by + 1))

            # Skalierung mit Zoom
            base_view_range = 1500
            view_range = base_view_range / self.map_zoom
            big_scale = big_map_size / (view_range * 2)
            drag_world_offset_x = self.map_drag_offset.x / big_scale
            drag_world_offset_y = self.map_drag_offset.y / big_scale
            center_offset_x = self.cords_schiff1.x - view_range - drag_world_offset_x
            center_offset_y = self.cords_schiff1.y - view_range - drag_world_offset_y

            # Fog of War — erkundete Bereiche als animiertes Wasser
            wave_t = getattr(self, 'wave_offset', 0)
            for (cell_x, cell_y) in self.explored_cells:
                world_x = cell_x * self.fog_cell_size
                world_y = cell_y * self.fog_cell_size
                map_x = (world_x - center_offset_x) * big_scale
                map_y = (world_y - center_offset_y) * big_scale
                cell_size_scaled = max(1, self.fog_cell_size * big_scale)
                if -cell_size_scaled < map_x < big_map_size and -cell_size_scaled < map_y < big_map_size:
                    # Animierte Wasserfarbe
                    wave_v = math.sin(wave_t * 1.5 + cell_x * 0.3 + cell_y * 0.2) * 8
                    wr = int(18 + wave_v)
                    wg = int(42 + wave_v * 1.5)
                    wb = int(82 + wave_v * 2)
                    pg.draw.rect(big_map, (wr, wg, wb),
                                 (map_x, map_y, cell_size_scaled + 1, cell_size_scaled + 1))

            # Grid-Linien (subtil, nur bei höherem Zoom)
            if self.map_zoom > 0.6:
                grid_spacing_world = 500  # 500px Weltkoordinaten
                grid_alpha = min(40, int(20 * (self.map_zoom - 0.4)))
                # Vertikale Linien
                start_world_x = int(center_offset_x / grid_spacing_world) * grid_spacing_world
                for gx_world in range(start_world_x, int(center_offset_x + view_range * 2) + grid_spacing_world, grid_spacing_world):
                    gx_map = (gx_world - center_offset_x) * big_scale
                    if 0 < gx_map < big_map_size:
                        pg.draw.line(big_map, (80, 120, 180, grid_alpha),
                                     (int(gx_map), 0), (int(gx_map), big_map_size))
                # Horizontale Linien
                start_world_y = int(center_offset_y / grid_spacing_world) * grid_spacing_world
                for gy_world in range(start_world_y, int(center_offset_y + view_range * 2) + grid_spacing_world, grid_spacing_world):
                    gy_map = (gy_world - center_offset_y) * big_scale
                    if 0 < gy_map < big_map_size:
                        pg.draw.line(big_map, (80, 120, 180, grid_alpha),
                                     (0, int(gy_map)), (big_map_size, int(gy_map)))

            # Haupt-Insel — skaliertes echtes Bild
            insel_w, insel_h = self.insel.get_size()
            insel_mini_x = (0 - center_offset_x) * big_scale
            insel_mini_y = (0 - center_offset_y) * big_scale
            insel_mini_w = max(1, int(insel_w * big_scale))
            insel_mini_h = max(1, int(insel_h * big_scale))
            if (insel_mini_x + insel_mini_w > 0 and insel_mini_x < big_map_size and
                insel_mini_y + insel_mini_h > 0 and insel_mini_y < big_map_size):
                if insel_mini_w > 2 and insel_mini_h > 2:
                    # Cache für schnelleres Zeichnen
                    bm_cache_key = ('big_insel', insel_mini_w, insel_mini_h)
                    if not hasattr(self, '_big_insel_cache') or self._big_insel_cache_key != bm_cache_key:
                        self._big_insel_cache = pg.transform.smoothscale(self.insel, (insel_mini_w, insel_mini_h))
                        self._big_insel_cache_key = bm_cache_key
                    big_map.blit(self._big_insel_cache, (insel_mini_x, insel_mini_y))
                    # Label für Haupt-Insel
                    if insel_mini_w > 40:
                        il_f = pg.font.SysFont("Arial", max(10, min(16, insel_mini_w // 10)), bold=True)
                        il_t = il_f.render("Home Island", True, (255, 240, 200))
                        il_x = insel_mini_x + insel_mini_w // 2 - il_t.get_width() // 2
                        il_y = insel_mini_y + insel_mini_h + 4
                        # Schatten
                        il_s = il_f.render("Home Island", True, (0, 0, 0))
                        big_map.blit(il_s, (il_x + 1, il_y + 1))
                        big_map.blit(il_t, (il_x, il_y))

            # Extra-Inseln als skalierte echte Bilder + Labels
            for idx, (island_pos, island_scale, island_img, _island_mask) in enumerate(self.extra_islands):
                ei_x = (island_pos.x - center_offset_x) * big_scale
                ei_y = (island_pos.y - center_offset_y) * big_scale
                ei_w = max(1, int(island_img.get_width() * big_scale))
                ei_h = max(1, int(island_img.get_height() * big_scale))
                if (ei_x + ei_w > -ei_w and ei_x < big_map_size + ei_w and
                    ei_y + ei_h > -ei_h and ei_y < big_map_size + ei_h and
                    ei_w > 2 and ei_h > 2):
                    ei_scaled = pg.transform.smoothscale(island_img, (ei_w, ei_h))
                    big_map.blit(ei_scaled, (ei_x - ei_w // 2, ei_y - ei_h // 2))
                    # Label
                    if ei_w > 25:
                        ei_label_f = pg.font.SysFont("Arial", max(9, min(13, ei_w // 8)))
                        ei_label_t = ei_label_f.render(f"Island {idx + 2}", True, (200, 220, 180))
                        big_map.blit(ei_label_t, (ei_x - ei_label_t.get_width() // 2, ei_y + ei_h // 2 + 3))

            # Gems (nur erkundet, mit Glow)
            for gem in getattr(self, 'gems', []):
                if gem.collected:
                    continue
                gem_gx = int(gem.pos.x // self.fog_cell_size)
                gem_gy = int(gem.pos.y // self.fog_cell_size)
                if (gem_gx, gem_gy) not in self.explored_cells:
                    continue
                gx = (gem.pos.x - center_offset_x) * big_scale
                gy = (gem.pos.y - center_offset_y) * big_scale
                if 5 < gx < big_map_size - 5 and 5 < gy < big_map_size - 5:
                    # Glow
                    pulse = abs(math.sin(wave_t * 3 + gx * 0.1)) * 0.4 + 0.6
                    glow_r = int(6 * pulse)
                    pg.draw.circle(big_map, (255, 220, 50, int(40 * pulse)), (int(gx), int(gy)), glow_r)
                    pg.draw.circle(big_map, (255, 210, 50), (int(gx), int(gy)), 3)
                    pg.draw.circle(big_map, (255, 255, 180), (int(gx), int(gy)), 2)

            # Steine (nur erkundet)
            for rock_pos, _rock_img, _rock_mask in self.rocks:
                rock_grid_x = int(rock_pos.x // self.fog_cell_size)
                rock_grid_y = int(rock_pos.y // self.fog_cell_size)
                if (rock_grid_x, rock_grid_y) in self.explored_cells:
                    rx = (rock_pos.x - center_offset_x) * big_scale
                    ry = (rock_pos.y - center_offset_y) * big_scale
                    if 3 < rx < big_map_size - 3 and 3 < ry < big_map_size - 3:
                        r_size = max(2, int(3 * self.map_zoom))
                        pg.draw.circle(big_map, (70, 65, 55), (int(rx), int(ry)), r_size + 1)
                        pg.draw.circle(big_map, (100, 95, 80), (int(rx), int(ry)), r_size)
                        pg.draw.circle(big_map, (130, 120, 105), (int(rx), int(ry)), max(1, r_size - 1), 1)

            # NPC-Schiffe (erkundet) — mit Richtungspfeilen
            self.map_hover_info = None
            mouse_pos = pg.mouse.get_pos()
            mouse_map_x = mouse_pos[0] - big_map_x
            mouse_map_y = mouse_pos[1] - big_map_y

            for npc_ship in self.npc_ships:
                if npc_ship.is_dead:
                    continue
                npc_gx = int(npc_ship.pos.x // self.fog_cell_size)
                npc_gy = int(npc_ship.pos.y // self.fog_cell_size)
                if (npc_gx, npc_gy) not in self.explored_cells:
                    continue
                nx = (npc_ship.pos.x - center_offset_x) * big_scale
                ny = (npc_ship.pos.y - center_offset_y) * big_scale
                if 5 < nx < big_map_size - 5 and 5 < ny < big_map_size - 5:
                    is_boss = getattr(npc_ship, 'is_boss', False)
                    npc_r = max(4, int(5 * self.map_zoom))
                    if is_boss:
                        # Boss: pulsierender roter Kreis
                        boss_pulse = abs(math.sin(wave_t * 4)) * 0.3 + 0.7
                        boss_r = int(npc_r * 2 * boss_pulse)
                        pg.draw.circle(big_map, (255, 20, 20, int(35 * boss_pulse)), (int(nx), int(ny)), boss_r + 6)
                        pg.draw.circle(big_map, (255, 40, 40), (int(nx), int(ny)), npc_r + 2)
                        pg.draw.circle(big_map, (255, 180, 180), (int(nx), int(ny)), npc_r + 2, 2)
                        # Totenkopf-Symbol
                        skull_f = pg.font.SysFont("Arial", max(10, int(12 * self.map_zoom)), bold=True)
                        skull_t = skull_f.render("☠", True, (255, 255, 255))
                        big_map.blit(skull_t, (int(nx) - skull_t.get_width() // 2, int(ny) - skull_t.get_height() // 2))
                    else:
                        # Normaler Feind: Roter Punkt mit Richtung
                        pg.draw.circle(big_map, (255, 50, 50, 50), (int(nx), int(ny)), npc_r + 3)
                        pg.draw.circle(big_map, (255, 70, 70), (int(nx), int(ny)), npc_r)
                        # Richtungslinie
                        if hasattr(npc_ship, 'direction') and self.map_zoom > 0.7:
                            npc_dir = npc_ship.direction
                            end_x = nx + npc_dir.x * (npc_r + 5)
                            end_y = ny + npc_dir.y * (npc_r + 5)
                            pg.draw.line(big_map, (255, 120, 120), (int(nx), int(ny)), (int(end_x), int(end_y)), 2)

                    # Hover-Tooltip
                    if abs(mouse_map_x - nx) < 15 and abs(mouse_map_y - ny) < 15:
                        dist_to_player = npc_ship.pos.distance_to(self.cords_schiff1)
                        hp_pct = max(0, npc_ship.health / getattr(npc_ship, 'max_health', 100))
                        label = "BOSS" if is_boss else "Feind"
                        self.map_hover_info = (mouse_pos[0], mouse_pos[1], f"{label}  HP: {int(hp_pct * 100)}%  Dist: {int(dist_to_player)}px")

            # Spieler — animierter Pfeil mit Puls und Sichtradius
            player_bx = bm_center + int(self.map_drag_offset.x)
            player_by = bm_center + int(self.map_drag_offset.y)
            if 10 < player_bx < big_map_size - 10 and 10 < player_by < big_map_size - 10:
                # Sichtradius-Kreis (dezent)
                sight_world = 5 * self.fog_cell_size  # 5 Zellen Sichtweite
                sight_pixels = int(sight_world * big_scale)
                if sight_pixels > 10:
                    sight_surf = pg.Surface((sight_pixels * 2, sight_pixels * 2), pg.SRCALPHA)
                    pg.draw.circle(sight_surf, (80, 200, 255, 15), (sight_pixels, sight_pixels), sight_pixels)
                    pg.draw.circle(sight_surf, (80, 200, 255, 35), (sight_pixels, sight_pixels), sight_pixels, 1)
                    big_map.blit(sight_surf, (player_bx - sight_pixels, player_by - sight_pixels))

                # Pulsierender Glow
                pulse = abs(math.sin(wave_t * 2.5)) * 0.4 + 0.6
                glow_size = int(20 * pulse)
                pg.draw.circle(big_map, (50, 255, 100, int(20 * pulse)), (player_bx, player_by), glow_size)
                pg.draw.circle(big_map, (50, 255, 100, int(10 * pulse)), (player_bx, player_by), glow_size + 8)

                # Pfeil mit Richtungsanzeige
                b_dir = richtungen[self.schiff_richtung]
                b_len = max(10, int(14 * self.map_zoom))
                b_w = max(6, int(9 * self.map_zoom))
                b_tip = (player_bx + b_dir.x * b_len, player_by + b_dir.y * b_len)
                b_perp = pg.Vector2(-b_dir.y, b_dir.x)
                b_left = (player_bx - b_dir.x * b_len * 0.5 + b_perp.x * b_w,
                          player_by - b_dir.y * b_len * 0.5 + b_perp.y * b_w)
                b_right = (player_bx - b_dir.x * b_len * 0.5 - b_perp.x * b_w,
                           player_by - b_dir.y * b_len * 0.5 - b_perp.y * b_w)
                # Schatten
                shadow_off = 2
                pg.draw.polygon(big_map, (0, 0, 0, 80),
                                [(b_tip[0] + shadow_off, b_tip[1] + shadow_off),
                                 (b_left[0] + shadow_off, b_left[1] + shadow_off),
                                 (b_right[0] + shadow_off, b_right[1] + shadow_off)])
                pg.draw.polygon(big_map, (50, 255, 100), [b_tip, b_left, b_right])
                pg.draw.polygon(big_map, (200, 255, 220), [b_tip, b_left, b_right], 2)

            # Kompass-Rose (oben rechts in der Karte)
            compass_cx = big_map_size - 40
            compass_cy = 40
            compass_r = 28
            # Hintergrund
            pg.draw.circle(big_map, (10, 20, 40, 200), (compass_cx, compass_cy), compass_r + 4)
            pg.draw.circle(big_map, (60, 90, 140), (compass_cx, compass_cy), compass_r + 4, 2)
            # Himmelsrichtungen
            compass_font = pg.font.SysFont("Arial", 11, bold=True)
            for label, dx, dy, col in [("N", 0, -1, (255, 80, 80)), ("S", 0, 1, (180, 200, 230)),
                                        ("O", 1, 0, (180, 200, 230)), ("W", -1, 0, (180, 200, 230))]:
                # Linie
                lx1 = compass_cx + dx * 8
                ly1 = compass_cy + dy * 8
                lx2 = compass_cx + dx * (compass_r - 2)
                ly2 = compass_cy + dy * (compass_r - 2)
                pg.draw.line(big_map, col, (lx1, ly1), (lx2, ly2), 2 if label == "N" else 1)
                # Buchstabe
                c_surf = compass_font.render(label, True, col)
                cx_pos = compass_cx + int(dx * (compass_r + 10)) - c_surf.get_width() // 2
                cy_pos = compass_cy + int(dy * (compass_r + 10)) - c_surf.get_height() // 2
                big_map.blit(c_surf, (cx_pos, cy_pos))
            # Zentrum
            pg.draw.circle(big_map, (200, 220, 255), (compass_cx, compass_cy), 3)

            # Distanz-Skala (unten rechts in der Karte)
            scale_bar_world = 500  # 500 px in der Welt
            scale_bar_px = int(scale_bar_world * big_scale)
            if 20 < scale_bar_px < big_map_size // 2:
                sb_x = big_map_size - scale_bar_px - 20
                sb_y = big_map_size - 25
                pg.draw.line(big_map, (150, 170, 210), (sb_x, sb_y), (sb_x + scale_bar_px, sb_y), 2)
                pg.draw.line(big_map, (150, 170, 210), (sb_x, sb_y - 4), (sb_x, sb_y + 4), 1)
                pg.draw.line(big_map, (150, 170, 210), (sb_x + scale_bar_px, sb_y - 4), (sb_x + scale_bar_px, sb_y + 4), 1)
                sc_f = pg.font.SysFont("Arial", 11)
                sc_t = sc_f.render(f"{scale_bar_world}m", True, (150, 170, 210))
                big_map.blit(sc_t, (sb_x + scale_bar_px // 2 - sc_t.get_width() // 2, sb_y - 15))

            # Koordinaten-Anzeige (unten links)
            coord_f = pg.font.SysFont("Arial", 11)
            px_world_x = int(self.cords_schiff1.x)
            px_world_y = int(self.cords_schiff1.y)
            coord_t = coord_f.render(f"Pos: {px_world_x}, {px_world_y}", True, (130, 150, 180))
            big_map.blit(coord_t, (10, big_map_size - 20))

            # Äußerer Rahmen (dekorativ, doppelt)
            pg.draw.rect(big_map, (50, 75, 120), (0, 0, big_map_size, big_map_size), 3, border_radius=6)
            pg.draw.rect(big_map, (90, 130, 190, 80), (4, 4, big_map_size - 8, big_map_size - 8), 1, border_radius=4)
            # Ecken-Deko (kleine Ornamente)
            corner_size = 12
            for cx, cy in [(6, 6), (big_map_size - 6, 6), (6, big_map_size - 6), (big_map_size - 6, big_map_size - 6)]:
                pg.draw.circle(big_map, (120, 160, 220), (cx, cy), corner_size // 2, 1)

            # Fog-of-War Rand-Blending (weicher Übergang am Kartenrand)
            edge_fade = pg.Surface((big_map_size, big_map_size), pg.SRCALPHA)
            fade_w = 15
            for i in range(fade_w):
                a = int(180 * (1 - i / fade_w))
                pg.draw.rect(edge_fade, (0, 0, 0, a), (i, i, big_map_size - 2 * i, big_map_size - 2 * i), 1)
            big_map.blit(edge_fade, (0, 0))

            s.blit(big_map, (big_map_x, big_map_y))

            # ===== UI-Elemente ÜBER der Karte =====

            # Titel-Leiste
            title_bar_w = big_map_size + 20
            title_bar_h = 48
            title_bar_x = big_map_x - 10
            title_bar_y = big_map_y - 56
            title_bar = pg.Surface((title_bar_w, title_bar_h), pg.SRCALPHA)
            # Gradient
            for ty in range(title_bar_h):
                t = ty / title_bar_h
                pg.draw.line(title_bar, (8 + int(15 * t), 16 + int(20 * t), 38 + int(30 * t), 235),
                             (0, ty), (title_bar_w, ty))
            pg.draw.rect(title_bar, (60, 90, 140, 150), (0, 0, title_bar_w, title_bar_h), 2, border_radius=10)
            # Gold-Akzent unten
            pg.draw.line(title_bar, (180, 150, 60, 120), (10, title_bar_h - 2), (title_bar_w - 10, title_bar_h - 2), 1)
            s.blit(title_bar, (title_bar_x, title_bar_y))

            title_f = pg.font.SysFont("Arial", 22, bold=True)
            title_text = title_f.render("WORLD MAP", True, (220, 200, 140))
            title_shadow = title_f.render("WORLD MAP", True, (10, 8, 2))
            s.blit(title_shadow, (title_bar_x + 47, title_bar_y + 13))
            s.blit(title_text, (title_bar_x + 46, title_bar_y + 12))

            # Anker-Icon (stilisiert)
            anker_x = title_bar_x + 22
            anker_y = title_bar_y + title_bar_h // 2
            pg.draw.line(s, (200, 180, 130), (anker_x, anker_y - 10), (anker_x, anker_y + 10), 2)
            pg.draw.circle(s, (200, 180, 130), (anker_x, anker_y - 12), 4, 2)
            pg.draw.line(s, (200, 180, 130), (anker_x - 7, anker_y + 6), (anker_x + 7, anker_y + 6), 2)

            # Zoom-Anzeige rechts im Titel
            zoom_pct = int(self.map_zoom * 100)
            zoom_f = pg.font.SysFont("Arial", 14, bold=True)
            zoom_t = zoom_f.render(f"Zoom: {zoom_pct}%", True, (150, 170, 210))
            s.blit(zoom_t, (title_bar_x + title_bar_w - zoom_t.get_width() - 16, title_bar_y + 16))

            # Steuerungshinweise im Titel
            hint_f = pg.font.SysFont("Arial", 12)
            hint_items = [
                ("Drag", "Move"), ("Scroll", "Zoom"), ("C", "Center"), ("M", "Close")
            ]
            hx = title_bar_x + title_bar_w - zoom_t.get_width() - 30
            for key, desc in reversed(hint_items):
                desc_s = hint_f.render(desc + "  ", True, (110, 130, 160))
                key_s = hint_f.render(key, True, (170, 190, 220))
                hx -= desc_s.get_width()
                s.blit(desc_s, (hx, title_bar_y + 33))
                hx -= key_s.get_width() + 2
                # Key-Hintergrund
                kb = pg.Surface((key_s.get_width() + 6, key_s.get_height() + 2), pg.SRCALPHA)
                pg.draw.rect(kb, (40, 55, 80, 180), (0, 0, kb.get_width(), kb.get_height()), border_radius=3)
                s.blit(kb, (hx - 3, title_bar_y + 32))
                s.blit(key_s, (hx, title_bar_y + 33))
                hx -= 8

            # Legende (untere Leiste)
            legend_bar_w = big_map_size + 20
            legend_bar_h = 34
            legend_bar_x = big_map_x - 10
            legend_bar_y = big_map_y + big_map_size + 8
            legend_bar = pg.Surface((legend_bar_w, legend_bar_h), pg.SRCALPHA)
            pg.draw.rect(legend_bar, (10, 18, 38, 220), (0, 0, legend_bar_w, legend_bar_h), border_radius=8)
            pg.draw.rect(legend_bar, (50, 70, 110, 120), (0, 0, legend_bar_w, legend_bar_h), 1, border_radius=8)
            s.blit(legend_bar, (legend_bar_x, legend_bar_y))

            legend_f = pg.font.SysFont("Arial", 13)
            legend_items = [
                ((50, 255, 100), "You"),
                ((255, 70, 70), "Enemies"),
                ((255, 50, 50), "Boss ☠"),
                ((255, 210, 50), "Gems"),
                ((100, 95, 80), "Rocks"),
                ((18, 42, 82), "Explored"),
                ((8, 18, 32), "Fog"),
            ]
            lx = legend_bar_x + 14
            for color, text in legend_items:
                pg.draw.circle(s, color, (lx + 6, legend_bar_y + legend_bar_h // 2), 5)
                pg.draw.circle(s, (200, 220, 240, 120), (lx + 6, legend_bar_y + legend_bar_h // 2), 5, 1)
                lbl = legend_f.render(text, True, (175, 190, 215))
                s.blit(lbl, (lx + 16, legend_bar_y + legend_bar_h // 2 - lbl.get_height() // 2))
                lx += lbl.get_width() + 34

            # Tooltip bei Hover über NPC
            if self.map_hover_info:
                tx, ty, ttext = self.map_hover_info
                tt_f = pg.font.SysFont("Arial", 14, bold=True)
                tt_surf = tt_f.render(ttext, True, (255, 230, 200))
                tt_w = tt_surf.get_width() + 16
                tt_h = tt_surf.get_height() + 10
                tt_bg = pg.Surface((tt_w, tt_h), pg.SRCALPHA)
                pg.draw.rect(tt_bg, (15, 25, 50, 230), (0, 0, tt_w, tt_h), border_radius=6)
                pg.draw.rect(tt_bg, (100, 140, 200, 150), (0, 0, tt_w, tt_h), 1, border_radius=6)
                s.blit(tt_bg, (tx + 15, ty - tt_h - 5))
                s.blit(tt_surf, (tx + 23, ty - tt_h))
        
        # Tod-Screen - Premium Version
        if self.is_dead:
            # Einfacher halbtransparenter roter Overlay (ohne teure Vignette)
            overlay = pg.Surface((w, h), pg.SRCALPHA)
            overlay.fill((20, 0, 0, 160))
            s.blit(overlay, (0, 0))
            
            # Totenkopf-Symbol
            skull_y = h // 2 - 80
            pg.draw.circle(s, (200, 200, 200), (w // 2, skull_y), 40)
            pg.draw.circle(s, (50, 50, 50), (w // 2 - 12, skull_y - 5), 10)
            pg.draw.circle(s, (50, 50, 50), (w // 2 + 12, skull_y - 5), 10)
            pg.draw.ellipse(s, (50, 50, 50), (w // 2 - 8, skull_y + 15, 16, 10))
            
            # "GAME OVER" Text
            game_over_font = pg.font.SysFont("Arial", 64, bold=True)
            game_over_text = game_over_font.render("GAME OVER", True, (180, 0, 0))
            shadow = game_over_font.render("GAME OVER", True, (50, 0, 0))
            s.blit(shadow, (w // 2 - game_over_text.get_width() // 2 + 4, h // 2 + 4))
            s.blit(game_over_text, (w // 2 - game_over_text.get_width() // 2, h // 2))
            
            # Neuer Highscore Banner
            if self.is_new_highscore:
                banner_pulse = abs(math.sin(self.death_timer * 4)) * 0.3 + 0.7
                banner_color = (int(255 * banner_pulse), int(200 * banner_pulse), int(50 * banner_pulse))
                banner_font = pg.font.SysFont("Arial", 32, bold=True)
                banner_text = banner_font.render("\u2605 NEW HIGHSCORE! \u2605", True, banner_color)
                banner_shadow = banner_font.render("\u2605 NEW HIGHSCORE! \u2605", True, (50, 40, 0))
                s.blit(banner_shadow, (w // 2 - banner_text.get_width() // 2 + 2, h // 2 + 62))
                s.blit(banner_text, (w // 2 - banner_text.get_width() // 2, h // 2 + 60))
            
            # Statistiken
            stats_y = h // 2 + 100 if self.is_new_highscore else h // 2 + 80
            survival_minutes = int(self.survival_time // 60)
            survival_seconds = int(self.survival_time % 60)
            
            # Highscore-Vergleich
            hs = self.highscore
            hs_time = hs.get('survival_time', 0)
            hs_min = int(hs_time // 60)
            hs_sec = int(hs_time % 60)
            
            stats = [
                f"Survival Time: {survival_minutes}:{survival_seconds:02d}",
                f"Kills: {self.kills}",
                f"Level Reached: {self.level}",
                f"Gems Collected: {self.total_gems}",
                f"Best Run: {hs_min}:{hs_sec:02d}  |  {hs.get('kills', 0)} Kills"
            ]
            for i, stat in enumerate(stats):
                # Letzte Zeile (Highscore) in Gold
                if i == len(stats) - 1:
                    stat_color = (255, 220, 100)
                else:
                    stat_color = (200, 200, 200)
                stat_surf = self.font_main.render(stat, True, stat_color)
                s.blit(stat_surf, (w // 2 - stat_surf.get_width() // 2, stats_y + i * 30))
            
            # Countdown zum Menü
            remaining = max(0, self.death_duration - self.death_timer)
            countdown_text = self.font_small.render(f"Back to menu in {remaining:.1f}s...", True, (150, 150, 150))
            s.blit(countdown_text, (w // 2 - countdown_text.get_width() // 2, h - 50))
