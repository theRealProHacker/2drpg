from time import time
import random
import json
import os
import math

import pygame as pg
from StateManager import State

from spritesheet import spritesheet
from sounds import get_sound_manager

# Pfad für persistente Gem-Speicherung
GEM_SAVE_FILE = "gems_save.json"


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
        
        # Alpha basierend auf Lebenszeit
        alpha = 255
        if self.fade:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Größe basierend auf Lebenszeit
        size = self.size
        if self.shrink:
            size = int(self.max_size * (self.lifetime / self.max_lifetime))
        
        if size > 0:
            # Zeichne Partikel mit Alpha
            surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
            color_with_alpha = (*self.color[:3], alpha)
            pg.draw.circle(surf, color_with_alpha, (size, size), size)
            surface.blit(surf, (int(screen_pos.x) - size, int(screen_pos.y) - size))


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
        alpha = int(150 * (1 - progress))
        size = int(self.max_size * (1 + progress * 2))
        
        if size > 0 and alpha > 0:
            surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
            pg.draw.circle(surf, (200, 220, 255, alpha), (size, size), size)
            pg.draw.circle(surf, (255, 255, 255, alpha // 2), (size, size), size, 2)
            surface.blit(surf, (int(screen_pos.x) - size, int(screen_pos.y) - size))


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
    def __init__(self, pos, damage, color=(255, 50, 50)):
        self.pos = pg.Vector2(pos)
        self.damage = damage
        self.color = color
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.velocity = pg.Vector2(random.uniform(-20, 20), -80)
        self.is_dead = False
        self.font = pg.font.SysFont("Arial", 24, bold=True)
    
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
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Schatten
        shadow_text = self.font.render(str(int(self.damage)), True, (0, 0, 0))
        shadow_text.set_alpha(alpha)
        surface.blit(shadow_text, (int(screen_pos.x) + 2, int(screen_pos.y) + 2))
        
        # Text
        text = self.font.render(str(int(self.damage)), True, self.color)
        text.set_alpha(alpha)
        surface.blit(text, (int(screen_pos.x), int(screen_pos.y)))


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


def load_perks():
    """Lädt die Perk-Level aus der Datei"""
    data = _load_full_save()
    return data.get('perks', {})


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
        
        # Glow-Effekt
        glow_size = int(self.radius * 3 + abs(math.sin(self.sparkle_timer * 4)) * 10)
        glow_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
        glow_alpha = int(50 + abs(math.sin(self.sparkle_timer * 4)) * 30)
        pg.draw.circle(glow_surf, (*self.color, glow_alpha), (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (int(screen_pos.x) - glow_size, int(screen_pos.y) - glow_size))
        
        # Sparkles zeichnen
        for sparkle in self.sparkles:
            sp_pos = screen_pos + sparkle['pos']
            alpha = int(255 * (sparkle['life'] / 0.5))
            spark_surf = pg.Surface((sparkle['size'] * 2, sparkle['size'] * 2), pg.SRCALPHA)
            pg.draw.circle(spark_surf, (255, 255, 255, alpha), (sparkle['size'], sparkle['size']), sparkle['size'])
            surface.blit(spark_surf, (int(sp_pos.x) - sparkle['size'], int(sp_pos.y) - sparkle['size']))
        
        # Glitzer-Effekt für Hauptfarbe
        sparkle = abs(math.sin(self.sparkle_timer * 5)) * 0.3 + 0.7
        color = tuple(int(c * sparkle) for c in self.color)
        
        # Diamant-Form zeichnen (3D-Effekt)
        x, y = int(screen_pos.x), int(screen_pos.y)
        
        # Schatten
        shadow_points = [
            (x + 3, y - self.radius + 5),
            (x + self.radius + 3, y + 3),
            (x + 3, y + self.radius // 2 + 3),
            (x - self.radius + 3, y + 3),
        ]
        pg.draw.polygon(surface, (0, 0, 0, 80), shadow_points)
        
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
        
        # Trail zeichnen
        for i, (trail_pos, trail_age) in enumerate(self.trail):
            trail_screen = trail_pos - offset
            alpha = int(150 * (i / len(self.trail)))
            size = int(self.radius * 0.3 * (i / len(self.trail)))
            if size > 0:
                trail_surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
                if self.is_enemy:
                    pg.draw.circle(trail_surf, (200, 100, 50, alpha), (size, size), size)
                else:
                    pg.draw.circle(trail_surf, (150, 150, 100, alpha), (size, size), size)
                surface.blit(trail_surf, (int(trail_screen.x) - size, int(trail_screen.y) - size))
        
        if self.is_enemy:
            # Feuer-Effekt für feindliche Kugeln
            glow_surf = pg.Surface((self.radius * 4, self.radius * 4), pg.SRCALPHA)
            pg.draw.circle(glow_surf, (255, 100, 50, 80), (self.radius * 2, self.radius * 2), self.radius * 2)
            pg.draw.circle(glow_surf, (255, 150, 50, 120), (self.radius * 2, self.radius * 2), self.radius + 2)
            surface.blit(glow_surf, (int(screen_pos.x) - self.radius * 2, int(screen_pos.y) - self.radius * 2))
            pg.draw.circle(surface, pg.Color(200, 80, 30), (int(screen_pos.x), int(screen_pos.y)), self.radius)
            pg.draw.circle(surface, pg.Color(255, 150, 50), (int(screen_pos.x), int(screen_pos.y)), self.radius - 3)
        else:
            # Goldene Kugel für Spieler
            glow_surf = pg.Surface((self.radius * 4, self.radius * 4), pg.SRCALPHA)
            pg.draw.circle(glow_surf, (255, 200, 100, 60), (self.radius * 2, self.radius * 2), self.radius * 2)
            surface.blit(glow_surf, (int(screen_pos.x) - self.radius * 2, int(screen_pos.y) - self.radius * 2))
            pg.draw.circle(surface, pg.Color(80, 80, 80), (int(screen_pos.x), int(screen_pos.y)), self.radius)
            pg.draw.circle(surface, pg.Color(150, 130, 80), (int(screen_pos.x), int(screen_pos.y)), self.radius - 2)
            # Glanzpunkt
            pg.draw.circle(surface, pg.Color(255, 255, 200), (int(screen_pos.x) - 2, int(screen_pos.y) - 2), 3)


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
        self.schiff_mit_boss = pg.transform.scale(
            self.schiff_mit,
            (int(self.schiff_mit.get_width() * 1.8), int(self.schiff_mit.get_height() * 1.8))
        )
        
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
        
        # Insel-Zuordnung (wird später gesetzt)
        self.home_island = 0
        
        # Erstes Ziel setzen
        self.pick_new_target()
    
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
        
        # Hilfsfunktion: NPC-Image und Mask nur einmal berechnen
        npc_img = self.get_image()
        npc_mask = pg.mask.from_surface(npc_img)
        npc_rect = npc_img.get_rect(center=self.pos)
        
        # Kollision mit Haupt-Insel prüfen
        if insel_mask is not None and insel_surf is not None:
            offset = (npc_rect.left, npc_rect.top)
            if insel_mask.overlap(npc_mask, offset):
                collision = True
                insel_w, insel_h = insel_surf.get_size()
                collision_point = pg.Vector2(insel_w // 2, insel_h // 2)
        
        # Kollision mit Extra-Inseln prüfen
        if not collision and extra_islands is not None:
            for island_pos, island_scale, island_img in extra_islands:
                island_mask = pg.mask.from_surface(island_img)
                island_rect = island_img.get_rect(center=island_pos)
                offset = (npc_rect.left - island_rect.left, npc_rect.top - island_rect.top)
                if island_mask.overlap(npc_mask, offset):
                    collision = True
                    collision_point = pg.Vector2(island_pos)
                    break
        
        # Kollision mit Steinen prüfen
        if not collision and rocks is not None:
            for rock_pos, rock_img in rocks:
                rock_mask = pg.mask.from_surface(rock_img)
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
        # Boss-Schiffe sind größer
        if self.is_boss:
            return pg.transform.rotate(self.schiff_mit_boss, self.richtung * -45)
        # Immer mit Segel zeigen (fährt immer)
        return pg.transform.rotate(self.schiff_mit, self.richtung * -45)
    
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
        """Respawnt das NPC-Schiff in der Nähe der Insel mit Schwierigkeits-Skalierung"""
        insel_w, insel_h = insel_size
        
        # Spawn im Ring um die Insel (nicht auf der Insel, nicht zu weit weg)
        while True:
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(max(insel_w, insel_h) // 2 + 100, max(insel_w, insel_h) // 2 + 600)
            x = insel_w // 2 + distance * pg.math.Vector2(1, 0).rotate_rad(angle).x
            y = insel_h // 2 + distance * pg.math.Vector2(1, 0).rotate_rad(angle).y
            pos = pg.Vector2(x, y)
            
            # Nicht zu nah am Spieler
            if pos.distance_to(player_pos) < 300:
                continue
            
            break
        
        self.pos = pos
        
        # Boss-Chance: 3% (steigt leicht mit Schwierigkeit, max ~8%)
        boss_chance = 0.03 + min(0.05, difficulty * 0.01)
        self.is_boss = random.random() < boss_chance
        self.boss_aggroed = False
        
        if self.is_boss:
            # Boss: 5x HP, etwas schneller, stärkerer Schuss, größere Reichweite
            self.health = int(500 * difficulty)
            self.max_health = int(500 * difficulty)
            self.shoot_cooldown_duration = max(0.3, 1.0 / difficulty)
            self.speed = int(110 * min(1.5, 0.8 + difficulty * 0.2))
            self.shoot_range = int(450 + difficulty * 15)
            self.boss_damage = int(25 * (1 + (difficulty - 1) * 0.3))  # Schaden skaliert
            self.boss_aggro_range = int(450 + difficulty * 20)
            self.respawn_duration = max(10.0, 20.0 - difficulty)  # Schnellerer Respawn
        else:
            # Normales Schiff
            self.health = int(100 * difficulty)
            self.max_health = int(100 * difficulty)
            self.shoot_cooldown_duration = max(0.5, 1.5 / difficulty)
            self.speed = int(100 * min(2.0, 0.8 + difficulty * 0.4))
            self.shoot_range = int(400 + difficulty * 10)
            self.boss_damage = int(10 * (1 + (difficulty - 1) * 0.25))  # Schaden skaliert
            self.respawn_duration = max(5.0, 10.0 - difficulty * 0.5)  # Schnellerer Respawn
        
        self.is_dead = False
        self.respawn_timer = 0
        self.shoot_cooldown = random.uniform(0, 1.0)
        self.pick_new_target()
    
    def scale_to_difficulty(self, difficulty):
        """Skaliert die Stats eines lebenden NPCs zur aktuellen Schwierigkeit"""
        if self.is_boss:
            new_max = int(500 * difficulty)
            self.shoot_cooldown_duration = max(0.3, 1.0 / difficulty)
            self.speed = int(110 * min(1.5, 0.8 + difficulty * 0.2))
            self.shoot_range = int(450 + difficulty * 15)
            self.boss_damage = int(25 * (1 + (difficulty - 1) * 0.3))
            self.boss_aggro_range = int(450 + difficulty * 20)
        else:
            new_max = int(100 * difficulty)
            self.shoot_cooldown_duration = max(0.5, 1.5 / difficulty)
            self.speed = int(100 * min(2.0, 0.8 + difficulty * 0.4))
            self.shoot_range = int(400 + difficulty * 10)
            self.boss_damage = int(10 * (1 + (difficulty - 1) * 0.25))
        
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
        self.insel = pg.image.load("assets/Insel.png")
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
        
        # Kanonenkugeln
        self.cannonballs = []
        self.shoot_cooldown = 0
        self.shoot_cooldown_duration = 0.3  # 0.3 Sekunden zwischen Schüssen
        
        # EXP-System
        self.exp = 0
        self.exp_to_level = 100  # EXP für nächstes Level
        self.level = 1
        
        # Skill-Punkte und Upgrades
        self.skill_points = 0
        self.speed_level = 0  # Boot-Geschwindigkeit
        self.fire_rate_level = 0  # Schussgeschwindigkeit
        self.regen_level = 0  # Regeneration
        self.max_health_level = 0  # Maximale Leben
        self.damage_level = 0  # Kugel-Schaden
        
        # Kill-Counter
        self.kills = 0
        
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
        
        # Fog of War - Erkundete Bereiche
        # Grid-basiert: jede Zelle ist 100x100 Pixel
        self.fog_cell_size = 100
        self.explored_cells = set()  # Set von (grid_x, grid_y) Tupeln
        
        # Basis-Werte
        self.base_speed = 300  # Vorwärts
        self.base_speed_back = 150  # Rückwärts
        self.base_shoot_cooldown = 0.3
        self.base_regen = 0  # HP pro Sekundes
        self.base_max_health = 100
        self.base_damage = 25
        
        # Gem-System (persistent über Runs)
        self.total_gems = load_gems()  # Gesamtanzahl aus Datei laden
        self.gems = self.generate_gems()  # Gems für diesen Run
        self.gem_spawn_timer = 0
        self.gem_spawn_interval = 30.0  # Alle 30 Sekunden Chance auf neuen Gem
        
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
        
        # Charakter-Status
        self.on_foot = False  # Ob Spieler zu Fuß ist
        self.player_foot_pos = pg.Vector2(0, 0)  # Position wenn zu Fuß
        self.foot_direction = 0  # 0=rechts, 1=oben, 2=links, 3=unten
        self.animation_timer = 0
        self.animation_speed = 0.15  # Sekunden pro Frame
        
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

    def generate_rocks(self):
        """Generiert zufällige Steinpositionen überall in der Welt"""
        rocks = []
        
        # Mindestabstand zwischen Steinen
        min_distance = 150
        
        # Viel mehr Steine!
        num_rocks = random.randint(60, 100)
        
        # Insel-Rect für Kollisionsprüfung
        insel_w, insel_h = self.insel.get_width(), self.insel.get_height()
        insel_rect = self.insel.get_rect(topleft=(0, 0))
        
        attempts = 0
        max_attempts = 2000
        
        while len(rocks) < num_rocks and attempts < max_attempts:
            attempts += 1
            
            # Zufällige Position um die Insel herum (in einem großen Bereich)
            # Insel ist bei (0,0) bis (insel_w, insel_h)
            x = random.randint(-1000, insel_w + 2000)
            y = random.randint(-1000, insel_h + 2000)
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
            for island_pos, island_scale, island_img in self.extra_islands:
                island_rect = island_img.get_rect(center=island_pos)
                island_offset = (rock_rect.left - island_rect.left, rock_rect.top - island_rect.top)
                island_mask = pg.mask.from_surface(island_img)
                if island_mask.overlap(scaled_mask, island_offset):
                    collision_with_extra_island = True
                    break
            
            if collision_with_extra_island:
                continue
            
            # Prüfe Mindestabstand zu anderen Steinen
            valid = True
            for rock_pos, _ in rocks:
                distance = new_pos.distance_to(rock_pos)
                if distance < min_distance:
                    valid = False
                    break
            
            if valid:
                # Speichere Position und pre-rendered Bild
                rocks.append((new_pos, scaled_img))
        
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
                
                islands.append((new_pos, scale, island_img))
        
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
        
        print(f"NPC-Schiffe generiert: {len(ships)}")  # Debug
        return ships

    def take_damage(self, amount):
        """Nimmt Schaden wenn Cooldown abgelaufen ist"""
        if self.damage_cooldown <= 0:
            self.health -= amount
            self.damage_cooldown = self.damage_cooldown_duration
            if hasattr(self, 'sfx'):
                self.sfx.play('damage')
            
            if self.health <= 0:
                self.health = 0
                self.is_dead = True
                self.death_timer = 0
                # Highscore speichern
                self.is_new_highscore = save_highscore(
                    self.survival_time, self.kills, self.level, self.total_gems
                )
                if self.is_new_highscore:
                    self.highscore = load_highscore()
                if hasattr(self, 'sfx'):
                    self.sfx.play('death')
    
    def toggle_on_foot(self):
        """Wechselt zwischen Schiff und zu Fuß"""
        if self.on_foot:
            # Wieder einsteigen - nur wenn nahe genug am Boot
            distance_to_ship = self.player_foot_pos.distance_to(self.cords_schiff1)
            if distance_to_ship < 100:  # Muss innerhalb 100 Pixel vom Boot sein
                self.on_foot = False
                self.cords_schiff1 = self.player_foot_pos.copy()
            # Wenn zu weit weg, passiert nichts
        else:
            # Prüfe ob nahe an einer Insel
            near_island = False
            
            # Hauptinsel prüfen - erweiterte Maske für größeren Bereich
            insel_rect = self.insel.get_rect(topleft=(0, 0))
            # Erweitere den Bereich um 200 Pixel
            check_rect = insel_rect.inflate(400, 400)
            if check_rect.collidepoint(self.cords_schiff1.x, self.cords_schiff1.y):
                near_island = True
            
            # Extra-Inseln prüfen
            if not near_island:
                for island_data in self.extra_islands:
                    island_pos = island_data[0]
                    island_img = island_data[2]
                    island_rect = island_img.get_rect(center=island_pos)
                    check_rect = island_rect.inflate(400, 400)
                    if check_rect.collidepoint(self.cords_schiff1.x, self.cords_schiff1.y):
                        near_island = True
                        break
            
            if near_island:
                # Aussteigen - finde nächsten Land-Punkt
                self.on_foot = True
                
                # Suche nach einem Land-Punkt in der Nähe des Schiffs
                found_land = False
                search_radius = 200  # Suche in 200 Pixel Radius
                
                for angle_deg in range(0, 360, 15):  # Alle 15 Grad
                    for distance in range(50, search_radius, 20):  # Alle 20 Pixel
                        angle_rad = angle_deg * 3.14159 / 180
                        test_x = self.cords_schiff1.x + distance * pg.math.Vector2(1, 0).rotate_rad(angle_rad).x
                        test_y = self.cords_schiff1.y + distance * pg.math.Vector2(1, 0).rotate_rad(angle_rad).y
                        
                        # Prüfe Haupt-Insel
                        insel_rect = self.insel.get_rect(topleft=(0, 0))
                        if insel_rect.collidepoint(test_x, test_y):
                            local_x = int(test_x - insel_rect.left)
                            local_y = int(test_y - insel_rect.top)
                            if 0 <= local_x < self.insel.get_width() and 0 <= local_y < self.insel.get_height():
                                if self.mask_insel.get_at((local_x, local_y)):
                                    self.player_foot_pos = pg.Vector2(test_x, test_y)
                                    found_land = True
                                    break
                        
                        # Prüfe Extra-Inseln
                        if not found_land:
                            for island_pos, _, island_img in self.extra_islands:
                                island_rect = island_img.get_rect(center=island_pos)
                                if island_rect.collidepoint(test_x, test_y):
                                    island_mask = pg.mask.from_surface(island_img)
                                    local_x = int(test_x - island_rect.left)
                                    local_y = int(test_y - island_rect.top)
                                    if 0 <= local_x < island_img.get_width() and 0 <= local_y < island_img.get_height():
                                        if island_mask.get_at((local_x, local_y)):
                                            self.player_foot_pos = pg.Vector2(test_x, test_y)
                                            found_land = True
                                            break
                    
                    if found_land:
                        break
                
                # Falls kein Land gefunden wurde (sollte nicht passieren), benutze Schiffsposition
                if not found_land:
                    self.player_foot_pos = self.cords_schiff1.copy()
    
    def get_difficulty(self):
        """Berechnet die aktuelle Schwierigkeit basierend auf Survival-Zeit"""
        # Startet bei 1.0, erhöht sich alle 60 Sekunden um 0.5
        # Nach 5 Minuten: 3.5x Stärke
        minutes_survived = self.survival_time / 60.0
        return 1.0 + (minutes_survived * 0.5)
    
    def _scale_living_npcs(self):
        """Skaliert lebende NPCs zur aktuellen Schwierigkeit (alle 10 Sekunden)"""
        difficulty = self.get_difficulty()
        for npc_ship in self.npc_ships:
            if not npc_ship.is_dead:
                npc_ship.scale_to_difficulty(difficulty)
    
    def _maybe_spawn_extra_npcs(self):
        """Spawnt zusätzliche NPCs bei höherer Schwierigkeit"""
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
            insel_radius = max(insel_w, insel_h) // 2
            island_pos = random.choice(self.island_ship_status)[0]
            
            angle = random.uniform(0, 2 * 3.14159)
            dist = insel_radius + random.uniform(200, 600)
            x = island_pos.x + dist * pg.math.Vector2(1, 0).rotate_rad(angle).x
            y = island_pos.y + dist * pg.math.Vector2(1, 0).rotate_rad(angle).y
            pos = pg.Vector2(x, y)
            
            if pos.distance_to(self.cords_schiff1) > 300:
                farbe = random.choice(segel_farben)
                ship = NPCShip(pos, self.schiff1, self.schiff2, farbe, self.world_size)
                ship.home_island = 0
                ship.respawn_near_island(self.insel.get_size(), self.cords_schiff1, difficulty)
                ship.pos = pos  # Position beibehalten
                self.npc_ships.append(ship)
    
    def restart_game(self):
        """Startet das Spiel neu"""
        # Perks laden und auf Basis-Werte anwenden
        perks = load_perks()
        hull_lvl = perks.get('hull', 0)
        cannons_lvl = perks.get('cannons', 0)
        sails_lvl = perks.get('sails', 0)
        repair_lvl = perks.get('repair', 0)
        reload_lvl = perks.get('reload', 0)
        self.xp_boost_perk = perks.get('xp_boost', 0)  # Für XP-Berechnung speichern
        
        # Basis-Werte mit Perks
        self.base_max_health = 100 + hull_lvl * 20
        self.base_damage = 25 + cannons_lvl * 10
        self.base_speed = 300 * (1 + sails_lvl * 0.10)
        self.base_speed_back = 150 * (1 + sails_lvl * 0.10)
        self.base_regen = 0 + repair_lvl * 1
        self.base_shoot_cooldown = 0.3 * (0.90 ** reload_lvl)
        
        self.health = self.base_max_health
        self.is_dead = False
        self.death_timer = 0
        self.survival_time = 0  # Survival-Zeit zurücksetzen
        # Startposition außerhalb der Insel
        insel_w, insel_h = self.insel.get_size()
        self.cords_schiff1 = pg.Vector2(insel_w + 200, insel_h // 2)
        self.schiff_richtung = 0
        self.camera_pos = pg.Vector2(self.cords_schiff1)
        
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
        self.is_new_highscore = False
        self.highscore = load_highscore()  # Highscore neu laden
        self.explored_cells = set()  # Fog of War zurücksetzen
        self.show_big_minimap = False
        self.gems = self.generate_gems()  # Neue Gems für neuen Run
        self.gem_spawn_timer = 0
        self.total_gems = load_gems()  # Gems neu laden (nach Perk-Käufen aktuell)
        
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
        
        # Musik am Laufen halten (falls Kanal unerwartet stoppt)
        if hasattr(self, 'sfx'):
            self.sfx.ensure_music_playing()
        
        # Survival-Zeit erhöhen (für Schwierigkeits-Skalierung)
        if not self.is_dead:
            self.survival_time += dt_seconds
            
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
                elif event.key == pg.K_c and self.show_big_minimap:
                    # Zentriere die Karte auf dem Spieler
                    self.map_drag_offset = pg.Vector2(0, 0)
                elif event.key == pg.K_a:
                    self.schiff_richtung -= 1
                    self.schiff_richtung %= 8
                elif event.key == pg.K_d:
                    self.schiff_richtung += 1
                    self.schiff_richtung %= 8
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
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.map_dragging = False
            elif event.type == pg.MOUSEMOTION and self.map_dragging and self.show_big_minimap:
                current_pos = pg.Vector2(event.pos)
                delta = current_pos - self.map_drag_start
                self.map_drag_offset += delta
                self.map_drag_start = current_pos
        
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
        current_regen = self.base_regen + self.regen_level * 2  # +2 HP/s pro Level
        current_max_health = self.base_max_health + self.max_health_level * 20  # +20 HP pro Level
        current_damage = self.base_damage + self.damage_level * 10  # +10 Schaden pro Level
        
        # Regeneration anwenden
        if current_regen > 0 and self.health < current_max_health:
            self.health = min(current_max_health, self.health + current_regen * dt_seconds)
        
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
            for island_pos, island_scale, island_img in self.extra_islands:
                island_mask = pg.mask.from_surface(island_img)
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
        if pg.key.get_pressed()[pg.K_w]:
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
                for island_pos, island_scale, island_img in self.extra_islands:
                    island_mask = pg.mask.from_surface(island_img)
                    island_rect = island_img.get_rect(center=island_pos)
                    offset = (self.schiff_rect.left - island_rect.left, self.schiff_rect.top - island_rect.top)
                    if island_mask.overlap(mask_schiff, offset):
                        self.cords_schiff1 = old_cords
                        self.take_damage(5)
                        collision = True
                        break
        else:
            self.moving = False

        if pg.key.get_pressed()[pg.K_s]:
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
                for island_pos, island_scale, island_img in self.extra_islands:
                    island_mask = pg.mask.from_surface(island_img)
                    island_rect = island_img.get_rect(center=island_pos)
                    offset = (self.schiff_rect.left - island_rect.left, self.schiff_rect.top - island_rect.top)
                    if island_mask.overlap(mask_schiff, offset):
                        self.cords_schiff1 = old_cords
                        self.take_damage(5)
                        break
        
        # Schießen mit Leertaste
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt_seconds
        
        if pg.key.get_pressed()[pg.K_SPACE] and self.shoot_cooldown <= 0:
            # Breitseite schießen (links und rechts)
            shoot_dir = richtungen[self.schiff_richtung]
            left_dir = pg.Vector2(-shoot_dir.y, shoot_dir.x)
            right_dir = pg.Vector2(shoot_dir.y, -shoot_dir.x)
            self.cannonballs.append(Cannonball(self.cords_schiff1, left_dir))
            self.cannonballs.append(Cannonball(self.cords_schiff1, right_dir))
            self.shoot_cooldown = current_shoot_cooldown
            if hasattr(self, 'sfx'):
                self.sfx.play('cannon')

        # Finale Position für weitere Kollisionen
        self.schiff_rect = self.schiff.get_rect(center=self.cords_schiff1)
        mask_schiff=pg.mask.from_surface(surface=self.schiff)
        
        # Stein-Kollision prüfen
        for rock_pos, rock_img in self.rocks:
            rock_mask = pg.mask.from_surface(rock_img)
            rock_rect = rock_img.get_rect(center=rock_pos)
            offset = (self.schiff_rect.left - rock_rect.left, self.schiff_rect.top - rock_rect.top)
            if rock_mask.overlap(mask_schiff, offset):
                self.cords_schiff1 = old_cords
                self.take_damage(5)
                break
        
        # NPC-Schiff Kollision mit Spieler prüfen
        for npc_ship in self.npc_ships:
            npc_img = npc_ship.get_image()
            npc_mask = pg.mask.from_surface(npc_img)
            npc_rect = npc_img.get_rect(center=npc_ship.pos)
            
            offset = (self.schiff_rect.left - npc_rect.left, self.schiff_rect.top - npc_rect.top)
            if npc_mask.overlap(mask_schiff, offset):
                # Spieler zurücksetzen
                self.cords_schiff1 = old_cords
                self.take_damage(5)
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
            
            # NPC versucht zu schießen
            ball = npc_ship.try_shoot(player_target)
            if ball is not None:
                self.cannonballs.append(ball)
        
        # Kanonenkugeln aktualisieren
        for ball in self.cannonballs:
            ball.update(dt_seconds)
        
        # Kanonenkugeln gegen NPC-Schiffe prüfen (nur Spieler-Kugeln)
        current_damage = self.base_damage + self.damage_level * 10  # Hier nochmal berechnen
        for ball in self.cannonballs:
            if ball.is_dead or ball.is_enemy:
                continue
            for npc_ship in self.npc_ships:
                if npc_ship.is_dead:
                    continue
                # Pixel-perfekte Hitbox mit Mask-Kollision
                npc_img = npc_ship.get_image()
                npc_rect = npc_img.get_rect(center=npc_ship.pos)
                # Kugel als kleiner Kreis (Radius 10)
                ball_rect = pg.Rect(int(ball.pos.x) - 10, int(ball.pos.y) - 10, 20, 20)
                
                # Schneller Rect-Check zuerst (Performance)
                if not npc_rect.inflate(20, 20).colliderect(ball_rect):
                    continue
                
                # Mask-basierte Kollision
                npc_mask = pg.mask.from_surface(npc_img)
                ball_surf = pg.Surface((20, 20), pg.SRCALPHA)
                pg.draw.circle(ball_surf, (255, 255, 255), (10, 10), 10)
                ball_mask = pg.mask.from_surface(ball_surf)
                offset = (ball_rect.left - npc_rect.left, ball_rect.top - npc_rect.top)
                
                if npc_mask.overlap(ball_mask, offset):
                    npc_ship.health -= current_damage  # Schaden basierend auf Upgrade
                    ball.is_dead = True
                    
                    # === PREMIUM EFFEKTE ===
                    # Explosion bei Treffer
                    self.explosions.append(ExplosionEffect(ball.pos, color=(255, 150, 50), size=25))
                    # Schadenszahl
                    self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -30), current_damage, (255, 255, 0)))
                    # Screen Shake
                    self.screen_shake = 0.15
                    self.screen_shake_intensity = 5
                    if hasattr(self, 'sfx'):
                        self.sfx.play('hit')
                    
                    if npc_ship.health <= 0:
                        npc_ship.is_dead = True
                        self.kills += 1  # Kill-Counter erhöhen
                        # Große Explosion beim Tod
                        self.explosions.append(ExplosionEffect(npc_ship.pos, color=(255, 100, 30), size=40))
                        self.screen_shake = 0.3
                        self.screen_shake_intensity = 12
                        if hasattr(self, 'sfx'):
                            self.sfx.play('explosion')
                        
                        # Prüfe ob alle Schiffe dieser Insel tot sind
                        if hasattr(npc_ship, 'home_island'):
                            island_idx = npc_ship.home_island
                            all_dead = True
                            for other_ship in self.npc_ships:
                                if hasattr(other_ship, 'home_island') and other_ship.home_island == island_idx and not other_ship.is_dead:
                                    all_dead = False
                                    break
                            if all_dead and island_idx < len(self.island_ship_status):
                                # Markiere dass diese Insel keine Schiffe mehr hat
                                island_pos, _ = self.island_ship_status[island_idx]
                                self.island_ship_status[island_idx] = (island_pos, False)
                        
                        # EXP geben - skaliert mit Schwierigkeit + XP-Boost Perk
                        difficulty = self.get_difficulty()
                        base_exp = 25 if not npc_ship.is_boss else 200
                        xp_multiplier = 1.0 + getattr(self, 'xp_boost_perk', 0) * 0.15
                        # Temporärer XP-Booster aus Login-Streak (verdoppelt)
                        if getattr(self, 'xp_booster_active', False) and getattr(self, 'xp_booster_remaining', 0) > 0:
                            xp_multiplier *= 2.0
                        scaled_exp = int(base_exp * difficulty * xp_multiplier)
                        self.exp += scaled_exp
                        # Zeige XP-Zahl
                        xp_color = (50, 200, 255) if not npc_ship.is_boss else (255, 215, 0)
                        self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -50), scaled_exp, xp_color))
                        
                        # Boss gibt 20 Gems!
                        if npc_ship.is_boss:
                            self.total_gems += 20
                            save_gems(self.total_gems)
                            self.damage_numbers.append(DamageNumber(npc_ship.pos + pg.Vector2(0, -80), 20, (255, 220, 50)))
                            self.screen_shake = 0.5
                            self.screen_shake_intensity = 20
                        if self.exp >= self.exp_to_level:
                            self.exp -= self.exp_to_level
                            self.level += 1
                            self.exp_to_level = int(self.exp_to_level * 1.5)  # Mehr EXP für nächstes Level
                            self.skill_points += 1  # Skill-Punkt bei Level-Up
                            if hasattr(self, 'sfx'):
                                self.sfx.play('levelup')
                    break
        
        # Feindliche Kugeln gegen Spieler prüfen
        for ball in self.cannonballs:
            if ball.is_dead or not ball.is_enemy:
                continue
            # Distanz zum Spieler
            dist = ball.pos.distance_to(self.cords_schiff1)
            if dist < 40:  # Treffer-Radius
                hit_damage = getattr(ball, 'boss_damage', 10)
                self.take_damage(hit_damage)  # Schaden je nach Quelle
                ball.is_dead = True
                # Explosion und Shake bei Treffer auf Spieler
                self.explosions.append(ExplosionEffect(ball.pos, color=(255, 50, 50), size=20 if hit_damage <= 10 else 35))
                self.damage_numbers.append(DamageNumber(self.cords_schiff1 + pg.Vector2(0, -30), hit_damage, (255, 50, 50)))
                self.screen_shake = 0.2
                self.screen_shake_intensity = 8
        
        # Tote Kugeln entfernen
        self.cannonballs = [b for b in self.cannonballs if not b.is_dead]
        
        # Gems aktualisieren und Kollision prüfen
        for gem in self.gems:
            if gem.collected:
                continue
            gem.update(dt_seconds)
            
            # Kollision mit Spieler
            dist = gem.pos.distance_to(self.cords_schiff1)
            if dist < 50:  # Einsammel-Radius
                gem.collected = True
                self.total_gems += 1
                save_gems(self.total_gems)  # Sofort speichern
                if hasattr(self, 'sfx'):
                    self.sfx.play('gem_pickup')
        
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
        
        # Respawn-Timer für tote NPCs
        insel_size = self.insel.get_size()
        player_target = self.cords_schiff1  # Immer Schiffsposition (on_foot entfernt)
        difficulty = self.get_difficulty()
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                npc_ship.respawn_timer += dt_seconds
                if npc_ship.respawn_timer >= npc_ship.respawn_duration:
                    npc_ship.respawn_near_island(insel_size, player_target, difficulty)
            else:
                # Prüfe ob NPC zu weit vom Spieler weg ist
                dist_to_player = npc_ship.pos.distance_to(player_target)
                if dist_to_player > 1500:  # Wenn weiter als 1500 Pixel
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
        
        # Screen Shake abklingen
        if self.screen_shake > 0:
            self.screen_shake -= dt_seconds
        
        # Wellen-Animation
        self.wave_offset += dt_seconds * 2
        
        # Sonnenstrahl-Animation
        self.sun_rays_timer += dt_seconds
        for ray in self.sun_rays:
            ray['angle'] += ray['speed'] * dt_seconds
        

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

        # island (Haupt-Insel)
        insel_pos = pg.Vector2(0, 0) - self.camera_pos + pg.Vector2(w // 2, h // 2)
        camera_surface.blit(self.insel, insel_pos)
        
        # Extra-Inseln zeichnen
        for island_pos, island_scale, island_img in self.extra_islands:
            island_screen_pos = island_pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            island_rect = island_img.get_rect(center=island_screen_pos)
            camera_surface.blit(island_img, island_rect)

        # rocks (Steine)
        for rock_pos, rock_img in self.rocks:
            rock_screen_pos = rock_pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            rock_rect = rock_img.get_rect(center=rock_screen_pos)
            camera_surface.blit(rock_img, rock_rect)

        # NPC-Schiffe zeichnen
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue
            npc_img = npc_ship.get_image()
            npc_screen_pos = npc_ship.pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
            npc_rect = npc_img.get_rect(center=npc_screen_pos)
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
        
        # Gems zeichnen
        offset = self.camera_pos - pg.Vector2(w // 2, h // 2)
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
        
        # Sonnenstrahl-Overlay (subtil)
        sun_overlay = pg.Surface((w, h), pg.SRCALPHA)
        for ray in self.sun_rays:
            ray_x = w // 2 + int(math.cos(ray['angle']) * w)
            ray_y = 0
            points = [
                (ray_x - ray['width'] // 2, 0),
                (ray_x + ray['width'] // 2, 0),
                (ray_x + ray['width'] // 4, h),
                (ray_x - ray['width'] // 4, h)
            ]
            pg.draw.polygon(sun_overlay, (255, 255, 200, ray['alpha']), points)
        camera_surface.blit(sun_overlay, (0, 0))

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
        
        s.blit(scaled, zoom_rect)
        
        # ==================== PREMIUM UI ====================
        # Berechne max health für Anzeige
        current_max_health = self.base_max_health + self.max_health_level * 20
        
        # UI Panel unten links (halbtransparent)
        ui_panel = pg.Surface((250, 100), pg.SRCALPHA)
        pg.draw.rect(ui_panel, (0, 0, 0, 150), (0, 0, 250, 100), border_radius=10)
        pg.draw.rect(ui_panel, (100, 100, 100, 200), (0, 0, 250, 100), width=2, border_radius=10)
        s.blit(ui_panel, (10, h - 110))
        
        # Lebensleiste (mit Gradient-Effekt)
        bar_width = 200
        bar_height = 24
        bar_x = 30
        bar_y = h - 95
        
        # Schatten
        pg.draw.rect(s, (0, 0, 0, 100), (bar_x + 2, bar_y + 2, bar_width, bar_height), border_radius=5)
        # Hintergrund
        pg.draw.rect(s, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        
        # Leben (grüner Gradient)
        health_width = int(bar_width * (self.health / current_max_health))
        if health_width > 0:
            # Farbe basierend auf Leben
            if self.health > 60:
                bar_color = (50, 200, 50)
                bar_color2 = (100, 255, 100)
            elif self.health > 30:
                bar_color = (200, 200, 50)
                bar_color2 = (255, 255, 100)
            else:
                bar_color = (200, 50, 50)
                bar_color2 = (255, 100, 100)
            
            # Gradient-Balken
            for i in range(health_width):
                t = i / max(1, health_width)
                color = (
                    int(bar_color[0] + (bar_color2[0] - bar_color[0]) * t * 0.3),
                    int(bar_color[1] + (bar_color2[1] - bar_color[1]) * t * 0.3),
                    int(bar_color[2] + (bar_color2[2] - bar_color[2]) * t * 0.3)
                )
                pg.draw.line(s, color, (bar_x + i, bar_y + 2), (bar_x + i, bar_y + bar_height - 2))
            
            # Glanz oben
            gloss = pg.Surface((health_width, bar_height // 3), pg.SRCALPHA)
            gloss.fill((255, 255, 255, 60))
            s.blit(gloss, (bar_x, bar_y))
        
        # Rahmen
        pg.draw.rect(s, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)
        
        # HP-Text mit Schatten
        hp_str = f"{int(self.health)}/{current_max_health}"
        hp_shadow = self.font_small.render(hp_str, True, (0, 0, 0))
        hp_text = self.font_small.render(hp_str, True, (255, 255, 255))
        text_x = bar_x + bar_width // 2 - hp_text.get_width() // 2
        s.blit(hp_shadow, (text_x + 1, bar_y + 4))
        s.blit(hp_text, (text_x, bar_y + 3))
        
        # Herz-Icon
        heart_color = (255, 80, 80) if self.health > 30 else (150, 50, 50)
        pg.draw.circle(s, heart_color, (bar_x - 15, bar_y + bar_height // 2), 8)
        pg.draw.circle(s, (255, 150, 150), (bar_x - 17, bar_y + bar_height // 2 - 2), 3)
        
        # EXP-Leiste
        exp_bar_y = h - 60
        exp_bar_height = 16
        
        # Schatten und Hintergrund
        pg.draw.rect(s, (0, 0, 0, 100), (bar_x + 2, exp_bar_y + 2, bar_width, exp_bar_height), border_radius=4)
        pg.draw.rect(s, (20, 20, 50), (bar_x, exp_bar_y, bar_width, exp_bar_height), border_radius=4)
        
        # EXP (blauer Gradient)
        exp_width = int(bar_width * (self.exp / self.exp_to_level))
        if exp_width > 0:
            for i in range(exp_width):
                t = i / max(1, exp_width)
                color = (
                    int(30 + 50 * t),
                    int(100 + 80 * t),
                    int(200 + 55 * t)
                )
                pg.draw.line(s, color, (bar_x + i, exp_bar_y + 2), (bar_x + i, exp_bar_y + exp_bar_height - 2))
        
        pg.draw.rect(s, (150, 150, 200), (bar_x, exp_bar_y, bar_width, exp_bar_height), 2, border_radius=4)
        
        # Level Badge
        level_badge = pg.Surface((50, 25), pg.SRCALPHA)
        pg.draw.rect(level_badge, (50, 50, 150, 220), (0, 0, 50, 25), border_radius=5)
        pg.draw.rect(level_badge, (150, 150, 255), (0, 0, 50, 25), 2, border_radius=5)
        level_text = self.font_small.render(f"Lv{self.level}", True, (255, 255, 255))
        level_badge.blit(level_text, (25 - level_text.get_width() // 2, 3))
        s.blit(level_badge, (bar_x + bar_width + 10, exp_bar_y - 3))
        
        # Stats Panel oben links
        stats_panel = pg.Surface((160, 100), pg.SRCALPHA)
        pg.draw.rect(stats_panel, (0, 0, 0, 150), (0, 0, 160, 100), border_radius=8)
        pg.draw.rect(stats_panel, (100, 100, 100, 200), (0, 0, 160, 100), width=2, border_radius=8)
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
        
        # Survival-Zeit und Schwierigkeit
        survival_minutes = int(self.survival_time // 60)
        survival_seconds = int(self.survival_time % 60)
        difficulty = self.get_difficulty()
        time_text = self.font_small.render(f"{survival_minutes}:{survival_seconds:02d}", True, (200, 200, 255))
        s.blit(time_text, (50, 82))
        # Schwierigkeits-Indikator (Farbe je nach Level)
        diff_color = (100 + min(155, int(difficulty * 30)), max(0, 255 - int(difficulty * 40)), 100)
        diff_text = self.font_small.render(f"x{difficulty:.1f}", True, diff_color)
        s.blit(diff_text, (100, 82))
        
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
            
            # Hintergrund-Panel
            boss_panel = pg.Surface((boss_bar_w + 40, boss_bar_h + 40), pg.SRCALPHA)
            pg.draw.rect(boss_panel, (0, 0, 0, 180), (0, 0, boss_bar_w + 40, boss_bar_h + 40), border_radius=10)
            pg.draw.rect(boss_panel, (180, 50, 50, 200), (0, 0, boss_bar_w + 40, boss_bar_h + 40), 3, border_radius=10)
            s.blit(boss_panel, (boss_bar_x - 20, boss_bar_y - 10))
            
            # "BOSS" Titel
            boss_title = self.font_small.render("BOSS", True, (255, 80, 80))
            s.blit(boss_title, (boss_bar_x, boss_bar_y - 6))
            
            # Distanz-Anzeige
            boss_dist = int(self.cords_schiff1.distance_to(active_boss.pos))
            dist_text = self.font_small.render(f"{boss_dist}m", True, (200, 200, 200))
            s.blit(dist_text, (boss_bar_x + boss_bar_w - dist_text.get_width(), boss_bar_y - 6))
            
            # Lebensbalken
            pg.draw.rect(s, (40, 10, 10), (boss_bar_x, boss_bar_y + 14, boss_bar_w, boss_bar_h), border_radius=5)
            boss_max = max(1, active_boss.max_health)
            boss_health_w = int(boss_bar_w * (active_boss.health / boss_max))
            if boss_health_w > 0:
                # Rot-Orange Gradient
                for i in range(boss_health_w):
                    t = i / max(1, boss_health_w)
                    r = int(180 + 60 * t)
                    g = int(30 + 40 * math.sin(t * 3.14))
                    b = 20
                    pg.draw.line(s, (r, g, b), (boss_bar_x + i, boss_bar_y + 16), (boss_bar_x + i, boss_bar_y + 14 + boss_bar_h - 2))
                # Glanz
                gloss = pg.Surface((boss_health_w, boss_bar_h // 3), pg.SRCALPHA)
                gloss.fill((255, 255, 255, 40))
                s.blit(gloss, (boss_bar_x, boss_bar_y + 14))
            
            pg.draw.rect(s, (255, 100, 80), (boss_bar_x, boss_bar_y + 14, boss_bar_w, boss_bar_h), 2, border_radius=5)
            
            # HP-Text
            boss_hp_str = f"{int(active_boss.health)}/{boss_max}"
            boss_hp_text = self.font_small.render(boss_hp_str, True, (255, 255, 255))
            s.blit(boss_hp_text, (boss_bar_x + boss_bar_w // 2 - boss_hp_text.get_width() // 2, boss_bar_y + 18))
        
        # Skill-Punkte Anzeige (oben rechts) - verbessertes Design
        if self.skill_points > 0:
            skill_panel = pg.Surface((230, 180), pg.SRCALPHA)
            pg.draw.rect(skill_panel, (0, 0, 0, 180), (0, 0, 230, 180), border_radius=10)
            pg.draw.rect(skill_panel, (255, 200, 50, 200), (0, 0, 230, 180), width=3, border_radius=10)
            s.blit(skill_panel, (w - 240, 10))
            
            # Titel
            title_text = self.font_main.render(f"✨ Skill-Punkte: {self.skill_points}", True, (255, 220, 100))
            s.blit(title_text, (w - 225, 20))
            
            upgrade_texts = [
                f"[1] 🚀 Speed ({self.speed_level})",
                f"[2] 🔥 Feuerrate ({self.fire_rate_level})",
                f"[3] 💚 Regen ({self.regen_level})",
                f"[4] ❤️ Leben ({self.max_health_level})",
                f"[5] 💥 Schaden ({self.damage_level})"
            ]
            for i, text in enumerate(upgrade_texts):
                rendered = self.font_small.render(text, True, (255, 255, 255))
                s.blit(rendered, (w - 220, 50 + i * 26))
        
        # Minimap (unten rechts) - zentriert auf Spieler
        minimap_size = 150
        minimap_x = w - minimap_size - 20
        minimap_y = h - minimap_size - 20
        
        # Minimap Surface mit Transparenz
        minimap = pg.Surface((minimap_size, minimap_size), pg.SRCALPHA)
        minimap.fill((20, 40, 80, 200))  # Dunkelblaues Wasser
        
        # Skalierung und Sichtweite
        mini_view_range = 800  # Sichtweite in Welt-Pixeln
        scale = minimap_size / (mini_view_range * 2)
        
        # Offset für Spieler-Zentrierung
        mini_offset_x = self.cords_schiff1.x - mini_view_range
        mini_offset_y = self.cords_schiff1.y - mini_view_range
        
        # Insel auf Minimap (als skaliertes Bild)
        insel_w, insel_h = self.insel.get_size()
        insel_mini_x = (0 - mini_offset_x) * scale
        insel_mini_y = (0 - mini_offset_y) * scale
        insel_mini_w = int(insel_w * scale)
        insel_mini_h = int(insel_h * scale)
        # Nur zeichnen wenn im sichtbaren Bereich und Größe > 0
        if (insel_mini_x + insel_mini_w > 0 and insel_mini_x < minimap_size and 
            insel_mini_y + insel_mini_h > 0 and insel_mini_y < minimap_size and
            insel_mini_w > 0 and insel_mini_h > 0):
            insel_mini_scaled = pg.transform.scale(self.insel, (insel_mini_w, insel_mini_h))
            minimap.blit(insel_mini_scaled, (insel_mini_x, insel_mini_y))
        
        # Extra-Inseln auf Minimap
        for island_pos, island_scale, island_img in self.extra_islands:
            ei_mini_x = (island_pos.x - mini_offset_x) * scale
            ei_mini_y = (island_pos.y - mini_offset_y) * scale
            ei_mini_w = int(island_img.get_width() * scale)
            ei_mini_h = int(island_img.get_height() * scale)
            if (ei_mini_x + ei_mini_w > -ei_mini_w and ei_mini_x < minimap_size + ei_mini_w and
                ei_mini_y + ei_mini_h > -ei_mini_h and ei_mini_y < minimap_size + ei_mini_h and
                ei_mini_w > 2 and ei_mini_h > 2):
                ei_scaled = pg.transform.scale(island_img, (ei_mini_w, ei_mini_h))
                minimap.blit(ei_scaled, (ei_mini_x - ei_mini_w // 2, ei_mini_y - ei_mini_h // 2))
        
        # Steine auf Minimap (als graue Punkte)
        for rock_pos, rock_img in self.rocks:
            rock_mini_x = (rock_pos.x - mini_offset_x) * scale
            rock_mini_y = (rock_pos.y - mini_offset_y) * scale
            if 0 <= rock_mini_x <= minimap_size and 0 <= rock_mini_y <= minimap_size:
                pg.draw.circle(minimap, (100, 100, 100), (int(rock_mini_x), int(rock_mini_y)), 2)
        
        # NPC-Schiffe auf Minimap (als rote Punkte)
        for npc_ship in self.npc_ships:
            if npc_ship.is_dead:
                continue
            npc_mini_x = (npc_ship.pos.x - mini_offset_x) * scale
            npc_mini_y = (npc_ship.pos.y - mini_offset_y) * scale
            # Nur zeichnen wenn innerhalb der Minimap
            if 0 <= npc_mini_x <= minimap_size and 0 <= npc_mini_y <= minimap_size:
                pg.draw.circle(minimap, (255, 50, 50), (int(npc_mini_x), int(npc_mini_y)), 3)
        
        # Spieler auf Minimap (als Pfeil in der Mitte)
        player_mini_x = minimap_size // 2
        player_mini_y = minimap_size // 2
        
        # Pfeil basierend auf Schiff-Richtung
        arrow_length = 8
        arrow_width = 5
        # Richtungsvektor (0 = unten, im Uhrzeigersinn)
        direction = richtungen[self.schiff_richtung]
        
        # Pfeilspitze
        tip_x = player_mini_x + direction.x * arrow_length
        tip_y = player_mini_y + direction.y * arrow_length
        
        # Pfeil-Seiten (senkrecht zur Richtung)
        perp = pg.Vector2(-direction.y, direction.x)
        left_x = player_mini_x - direction.x * arrow_length * 0.5 + perp.x * arrow_width
        left_y = player_mini_y - direction.y * arrow_length * 0.5 + perp.y * arrow_width
        right_x = player_mini_x - direction.x * arrow_length * 0.5 - perp.x * arrow_width
        right_y = player_mini_y - direction.y * arrow_length * 0.5 - perp.y * arrow_width
        
        # Pfeil zeichnen
        pg.draw.polygon(minimap, (50, 255, 50), [
            (tip_x, tip_y),
            (left_x, left_y),
            (right_x, right_y)
        ])
        pg.draw.polygon(minimap, (255, 255, 255), [
            (tip_x, tip_y),
            (left_x, left_y),
            (right_x, right_y)
        ], 1)
        
        # Rahmen
        pg.draw.rect(minimap, (255, 255, 255), (0, 0, minimap_size, minimap_size), 2)
        
        # Minimap zeichnen
        s.blit(minimap, (minimap_x, minimap_y))
        
        # Große Minimap (wenn M gedrückt)
        if self.show_big_minimap:
            # Halbtransparenter schwarzer Overlay
            overlay = pg.Surface((w, h), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            s.blit(overlay, (0, 0))
            
            # Große Minimap in der Mitte
            big_map_size = min(w, h) - 100  # Fast bildschirmfüllend
            big_map_x = (w - big_map_size) // 2
            big_map_y = (h - big_map_size) // 2
            
            big_map = pg.Surface((big_map_size, big_map_size), pg.SRCALPHA)
            big_map.fill((10, 20, 40, 255))  # Dunkler Hintergrund (nicht erkundet)
            
            # Skalierung - größerer Zoom damit man mehr Details sieht
            view_range = 1500  # Sichtweite in Welt-Pixeln vom Spieler aus
            big_scale = big_map_size / (view_range * 2)
            
            # Offset für Spieler-Zentrierung (mit Drag-Offset)
            drag_world_offset_x = self.map_drag_offset.x / big_scale
            drag_world_offset_y = self.map_drag_offset.y / big_scale
            center_offset_x = self.cords_schiff1.x - view_range - drag_world_offset_x
            center_offset_y = self.cords_schiff1.y - view_range - drag_world_offset_y
            
            # Fog of War zeichnen - nur erkundete Bereiche zeigen
            for (cell_x, cell_y) in self.explored_cells:
                # Zell-Position in Welt-Koordinaten
                world_x = cell_x * self.fog_cell_size
                world_y = cell_y * self.fog_cell_size
                
                # In Minimap-Koordinaten umrechnen (zentriert auf Spieler)
                map_x = (world_x - center_offset_x) * big_scale
                map_y = (world_y - center_offset_y) * big_scale
                cell_size_scaled = self.fog_cell_size * big_scale
                
                # Nur zeichnen wenn im sichtbaren Bereich
                if -cell_size_scaled < map_x < big_map_size and -cell_size_scaled < map_y < big_map_size:
                    # Erkundeter Bereich als dunkelblau (Wasser)
                    pg.draw.rect(big_map, (20, 40, 80), 
                                (map_x, map_y, cell_size_scaled + 1, cell_size_scaled + 1))
            
            # Insel zeichnen (immer, ohne Fog of War Check - Insel ist Orientierungspunkt)
            insel_w, insel_h = self.insel.get_size()
            
            # Insel als skaliertes Bild auf der Karte (zentriert auf Spieler)
            insel_mini_x = (0 - center_offset_x) * big_scale
            insel_mini_y = (0 - center_offset_y) * big_scale
            insel_mini_w = int(insel_w * big_scale)
            insel_mini_h = int(insel_h * big_scale)
            
            # Nur zeichnen wenn im sichtbaren Bereich
            if (insel_mini_x + insel_mini_w > 0 and insel_mini_x < big_map_size and 
                insel_mini_y + insel_mini_h > 0 and insel_mini_y < big_map_size):
                if insel_mini_w > 0 and insel_mini_h > 0:
                    insel_scaled = pg.transform.scale(self.insel, (insel_mini_w, insel_mini_h))
                    big_map.blit(insel_scaled, (insel_mini_x, insel_mini_y))
            
            # Extra-Inseln auf großer Karte
            for island_pos, island_scale, island_img in self.extra_islands:
                ei_x = (island_pos.x - center_offset_x) * big_scale
                ei_y = (island_pos.y - center_offset_y) * big_scale
                ei_w = int(island_img.get_width() * big_scale)
                ei_h = int(island_img.get_height() * big_scale)
                if (ei_x + ei_w > -ei_w and ei_x < big_map_size + ei_w and
                    ei_y + ei_h > -ei_h and ei_y < big_map_size + ei_h and
                    ei_w > 2 and ei_h > 2):
                    ei_scaled = pg.transform.scale(island_img, (ei_w, ei_h))
                    big_map.blit(ei_scaled, (ei_x - ei_w // 2, ei_y - ei_h // 2))
            
            # Steine (nur wenn erkundet) - kleinere Punkte
            for rock_pos, rock_img in self.rocks:
                rock_grid_x = int(rock_pos.x // self.fog_cell_size)
                rock_grid_y = int(rock_pos.y // self.fog_cell_size)
                if (rock_grid_x, rock_grid_y) in self.explored_cells:
                    rock_mini_x = (rock_pos.x - center_offset_x) * big_scale
                    rock_mini_y = (rock_pos.y - center_offset_y) * big_scale
                    if 0 < rock_mini_x < big_map_size and 0 < rock_mini_y < big_map_size:
                        pg.draw.circle(big_map, (100, 100, 100), (int(rock_mini_x), int(rock_mini_y)), 5)
            
            # Spieler (Position mit Drag-Offset)
            player_mini_x = big_map_size // 2 + int(self.map_drag_offset.x)
            player_mini_y = big_map_size // 2 + int(self.map_drag_offset.y)
            # Nur zeichnen wenn im sichtbaren Bereich
            if 0 < player_mini_x < big_map_size and 0 < player_mini_y < big_map_size:
                pg.draw.circle(big_map, (50, 255, 50), (player_mini_x, player_mini_y), 8)
                pg.draw.circle(big_map, (255, 255, 255), (player_mini_x, player_mini_y), 8, 2)
            
            # Rahmen
            pg.draw.rect(big_map, (255, 255, 255), (0, 0, big_map_size, big_map_size), 3)
            
            s.blit(big_map, (big_map_x, big_map_y))
            
            # Titel
            title_text = self.font_title.render("Weltkarte - Ziehen zum Bewegen, C zum Zentrieren, M zum Schließen", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(w // 2, big_map_y - 30))
            s.blit(title_text, title_rect)
            
            # Legende
            legend_texts = [
                ("Grün = Du", (50, 255, 50)),
                ("Dunkel = Nicht erkundet", (10, 20, 40)),
            ]
            for i, (text, color) in enumerate(legend_texts):
                legend = self.font_small.render(text, True, color)
                s.blit(legend, (big_map_x + 10, big_map_y + big_map_size + 10 + i * 20))
        
        # Tod-Screen - Premium Version
        if self.is_dead:
            # Halbtransparenter roter Overlay
            overlay = pg.Surface((w, h), pg.SRCALPHA)
            # Vignetten-Effekt
            for radius in range(0, max(w, h), 20):
                alpha = min(200, int(radius / max(w, h) * 255))
                pg.draw.circle(overlay, (20, 0, 0, alpha), (w // 2, h // 2), max(w, h) - radius)
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
                banner_text = banner_font.render("\u2605 NEUER HIGHSCORE! \u2605", True, banner_color)
                banner_shadow = banner_font.render("\u2605 NEUER HIGHSCORE! \u2605", True, (50, 40, 0))
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
                f"Überlebenszeit: {survival_minutes}:{survival_seconds:02d}",
                f"Kills: {self.kills}",
                f"Level erreicht: {self.level}",
                f"Gems gesammelt: {self.total_gems}",
                f"Bester Run: {hs_min}:{hs_sec:02d}  |  {hs.get('kills', 0)} Kills"
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
            countdown_text = self.font_small.render(f"Zuruck zum Menu in {remaining:.1f}s...", True, (150, 150, 150))
            s.blit(countdown_text, (w // 2 - countdown_text.get_width() // 2, h - 50))
