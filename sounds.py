"""
Programmatisch generierte Sound-Effekte für das Piratenspiel.
Verwendet numpy + pygame.sndarray um Sounds ohne externe Dateien zu erzeugen.
"""
import numpy as np
import pygame as pg

SAMPLE_RATE = 44100


def _make_sound(samples):
    """Erzeugt einen pygame.mixer.Sound aus einem numpy-Array (mono, float -1..1)"""
    # Clamp & convert to int16 stereo
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    # Stereo: gleicher Kanal links und rechts
    stereo = np.column_stack((int_samples, int_samples))
    return pg.sndarray.make_sound(stereo)


def _envelope(length, attack=0.01, decay=0.1, sustain_level=0.7, release=0.1):
    """Erzeugt eine ADSR-Hüllkurve"""
    t = np.linspace(0, length, int(SAMPLE_RATE * length), endpoint=False)
    env = np.ones_like(t)
    
    for i, ti in enumerate(t):
        if ti < attack:
            env[i] = ti / attack
        elif ti < attack + decay:
            env[i] = 1.0 - (1.0 - sustain_level) * ((ti - attack) / decay)
        elif ti > length - release:
            env[i] = sustain_level * ((length - ti) / release)
        else:
            env[i] = sustain_level
    
    return t, env


def generate_cannon_sound():
    """Kanonenschuss - tiefer Boom mit Rauschen"""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Tiefer Boom (60Hz abfallend auf 30Hz)
    freq = 60 * np.exp(-t * 5)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    boom = np.sin(phase) * 0.6
    
    # Explosion Rauschen
    noise = np.random.uniform(-1, 1, len(t)) * 0.4
    
    # Hüllkurve - schneller Attack, schneller Decay
    env = np.exp(-t * 12)
    
    sound = (boom + noise) * env * 0.7
    return _make_sound(sound)


def generate_explosion_sound():
    """Explosion - lauter tieferer Knall"""
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Tiefer Knall
    freq = 80 * np.exp(-t * 4)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    boom = np.sin(phase) * 0.7
    
    # Viel Rauschen
    noise = np.random.uniform(-1, 1, len(t)) * 0.5
    
    # Hüllkurve
    env = np.exp(-t * 6)
    
    sound = (boom + noise) * env * 0.8
    return _make_sound(sound)


def generate_hit_sound():
    """Treffer-Sound - kurzer Impact"""
    duration = 0.15
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Kurzer Knack
    freq = 200 * np.exp(-t * 20)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    hit = np.sin(phase) * 0.5
    
    noise = np.random.uniform(-1, 1, len(t)) * 0.3
    env = np.exp(-t * 25)
    
    sound = (hit + noise) * env * 0.6
    return _make_sound(sound)


def generate_damage_sound():
    """Schaden nehmen - dumpfer Aufprall"""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    freq = 120 * np.exp(-t * 10)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    thud = np.sin(phase) * 0.6
    
    noise = np.random.uniform(-1, 1, len(t)) * 0.2
    env = np.exp(-t * 15)
    
    sound = (thud + noise) * env * 0.5
    return _make_sound(sound)


def generate_gem_pickup_sound():
    """Gem einsammeln - heller aufsteigender Ton"""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Aufsteigender Ton (800Hz -> 1600Hz)
    freq = 800 + 800 * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase) * 0.3
    
    # Harmonik
    tone += np.sin(phase * 2) * 0.15
    tone += np.sin(phase * 3) * 0.08
    
    env = np.exp(-t * 5) * (1 - np.exp(-t * 100))  # Kurzer Attack
    
    sound = tone * env * 0.5
    return _make_sound(sound)


def generate_levelup_sound():
    """Level Up - aufsteigender Dreiklang"""
    duration = 0.6
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    sound = np.zeros_like(t)
    
    # Drei aufsteigende Töne (C-E-G)
    notes = [523, 659, 784]  # C5, E5, G5
    for i, freq in enumerate(notes):
        start = int(i * SAMPLE_RATE * 0.15)
        end = min(len(t), start + int(SAMPLE_RATE * 0.3))
        segment_t = np.arange(end - start) / SAMPLE_RATE
        
        tone = np.sin(2 * np.pi * freq * segment_t) * 0.25
        tone += np.sin(2 * np.pi * freq * 2 * segment_t) * 0.12
        
        env_seg = np.exp(-segment_t * 5) * (1 - np.exp(-segment_t * 80))
        sound[start:end] += tone * env_seg
    
    return _make_sound(sound * 0.6)


def generate_death_sound():
    """Tod - abfallender Ton mit Verzerrung"""
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Abfallender Ton
    freq = 400 * np.exp(-t * 2)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase) * 0.5
    
    # Verzerrung
    noise = np.random.uniform(-1, 1, len(t)) * 0.3
    
    env = np.exp(-t * 2)
    
    sound = (tone + noise) * env * 0.6
    return _make_sound(sound)


def generate_menu_select_sound():
    """Menü Navigation - kurzer Klick"""
    duration = 0.08
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    tone = np.sin(2 * np.pi * 600 * t) * 0.2
    tone += np.sin(2 * np.pi * 900 * t) * 0.1
    
    env = np.exp(-t * 40)
    
    sound = tone * env * 0.4
    return _make_sound(sound)


def generate_menu_confirm_sound():
    """Menü Bestätigen - kurzer Aufwärts-Ton"""
    duration = 0.15
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    freq = 500 + 300 * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase) * 0.25
    tone += np.sin(phase * 1.5) * 0.12
    
    env = np.exp(-t * 10) * (1 - np.exp(-t * 200))
    
    sound = tone * env * 0.5
    return _make_sound(sound)


def generate_wheel_spin_sound():
    """Glücksrad drehen - Ticker-Sound"""
    duration = 0.06
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    tone = np.sin(2 * np.pi * 1200 * t) * 0.15
    env = np.exp(-t * 50)
    
    sound = tone * env * 0.3
    return _make_sound(sound)


def generate_wheel_win_sound():
    """Glücksrad Gewinn - Fanfare"""
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    sound = np.zeros_like(t)
    
    # Aufsteigende Fanfare
    notes = [523, 659, 784, 1047]  # C5-E5-G5-C6
    for i, freq in enumerate(notes):
        start = int(i * SAMPLE_RATE * 0.1)
        end = min(len(t), start + int(SAMPLE_RATE * 0.25))
        segment_t = np.arange(end - start) / SAMPLE_RATE
        
        tone = np.sin(2 * np.pi * freq * segment_t) * 0.2
        tone += np.sin(2 * np.pi * freq * 2 * segment_t) * 0.1
        
        env_seg = np.exp(-segment_t * 4) * (1 - np.exp(-segment_t * 100))
        sound[start:end] += tone * env_seg
    
    return _make_sound(sound * 0.5)


def generate_boss_spawn_sound():
    """Boss Warnung - tiefer bedrohlicher Ton"""
    duration = 0.8
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Tiefer Brumm-Ton
    tone = np.sin(2 * np.pi * 80 * t) * 0.4
    tone += np.sin(2 * np.pi * 120 * t) * 0.25
    tone += np.sin(2 * np.pi * 160 * t) * 0.15
    
    # Leichtes Vibrato
    vibrato = np.sin(2 * np.pi * 5 * t) * 0.1
    tone *= (1 + vibrato)
    
    env = (1 - np.exp(-t * 10)) * np.exp(-t * 2)
    
    sound = tone * env * 0.6
    return _make_sound(sound)


def generate_perk_buy_sound():
    """Perk kaufen - Kassa-Sound"""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Zwei aufeinanderfolgende Töne
    sound = np.zeros_like(t)
    
    # Erster Ton
    mask1 = t < 0.12
    sound[mask1] = np.sin(2 * np.pi * 880 * t[mask1]) * 0.3
    
    # Zweiter Ton (höher)
    mask2 = (t >= 0.12) & (t < 0.3)
    sound[mask2] = np.sin(2 * np.pi * 1100 * t[mask2]) * 0.3
    
    env = np.exp(-t * 8) * (1 - np.exp(-t * 200))
    
    sound = sound * env * 0.5
    return _make_sound(sound)


def generate_error_sound():
    """Fehler/Ablehnung - kurzer tiefer Buzz"""
    duration = 0.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    tone = np.sin(2 * np.pi * 150 * t) * 0.3
    tone += np.sin(2 * np.pi * 155 * t) * 0.3  # Leicht verstimmt = Schwebung
    
    env = np.exp(-t * 10)
    
    sound = tone * env * 0.4
    return _make_sound(sound)


def _synth_note(t_arr, freq, start, dur, timbre='strings', vibrato=0.0):
    """Hilfsfunktion: erzeugt eine einzelne Note mit Timbre"""
    mask = (t_arr >= start) & (t_arr < start + dur)
    if not np.any(mask):
        return np.zeros_like(t_arr)
    local_t = t_arr[mask] - start
    
    # ADSR Hüllkurve
    att = min(0.04, dur * 0.1)
    rel = min(0.12, dur * 0.25)
    env = np.ones_like(local_t)
    env = np.where(local_t < att, local_t / att, env)
    env = np.where(local_t > dur - rel, (dur - local_t) / rel, env)
    env = np.clip(env, 0, 1)
    
    # Vibrato
    vib = 1.0
    if vibrato > 0:
        vib = 1.0 + vibrato * np.sin(2 * np.pi * 5.5 * local_t)
    
    f = freq * vib
    
    if timbre == 'strings':
        # Warmer Streicher-Sound (Sägezahn-Annäherung)
        wave = (
            np.sin(2 * np.pi * f * local_t) * 0.45 +
            np.sin(2 * np.pi * f * 2 * local_t) * 0.25 +
            np.sin(2 * np.pi * f * 3 * local_t) * 0.15 +
            np.sin(2 * np.pi * f * 4 * local_t) * 0.08 +
            np.sin(2 * np.pi * f * 5 * local_t) * 0.04
        )
    elif timbre == 'brass':
        # Kraftvoller Blechbläser-Sound
        wave = (
            np.sin(2 * np.pi * f * local_t) * 0.5 +
            np.sin(2 * np.pi * f * 2 * local_t) * 0.35 +
            np.sin(2 * np.pi * f * 3 * local_t) * 0.2 +
            np.sin(2 * np.pi * f * 4 * local_t) * 0.15 +
            np.sin(2 * np.pi * f * 5 * local_t) * 0.1 +
            np.sin(2 * np.pi * f * 6 * local_t) * 0.05
        )
    elif timbre == 'bass':
        # Tiefer, voller Bass
        wave = (
            np.sin(2 * np.pi * f * local_t) * 0.7 +
            np.sin(2 * np.pi * f * 2 * local_t) * 0.2 +
            np.sin(2 * np.pi * f * 0.5 * local_t) * 0.15
        )
    elif timbre == 'fiddle':
        # Geigen/Fiddle-Klang (nasaler, obertonreicher)
        wave = (
            np.sin(2 * np.pi * f * local_t) * 0.35 +
            np.sin(2 * np.pi * f * 2 * local_t) * 0.3 +
            np.sin(2 * np.pi * f * 3 * local_t) * 0.2 +
            np.sin(2 * np.pi * f * 4 * local_t) * 0.12 +
            np.sin(2 * np.pi * f * 5 * local_t) * 0.08 +
            np.sin(2 * np.pi * f * 7 * local_t) * 0.03
        )
    else:
        wave = np.sin(2 * np.pi * f * local_t)
    
    result = np.zeros_like(t_arr)
    result[mask] = wave * env
    return result


def _drum_hit(t_arr, start, drum_type='kick'):
    """Erzeugt einen perkussiven Schlag"""
    dur = 0.15 if drum_type == 'kick' else 0.08
    mask = (t_arr >= start) & (t_arr < start + dur)
    if not np.any(mask):
        return np.zeros_like(t_arr)
    local_t = t_arr[mask] - start
    env = np.exp(-local_t * (30 if drum_type == 'kick' else 50))
    
    if drum_type == 'kick':
        freq = 80 * np.exp(-local_t * 15)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        wave = np.sin(phase) * 0.7 + np.random.uniform(-0.3, 0.3, len(local_t))
    else:  # snare / hat
        wave = np.random.uniform(-1, 1, len(local_t))
    
    result = np.zeros_like(t_arr)
    result[mask] = wave * env
    return result


def generate_menu_music():
    """Epische Piraten-Musik für das Menü - dramatisch und majestätisch (Loop-fähig)"""
    # 16 Sekunden bei ~130 BPM (ca. 0.46s pro Beat)
    duration = 16.0
    bpm = 130
    beat = 60.0 / bpm  # ~0.46s
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # ====== EPISCHE MELODIE (Fiddle/Streicher) ======
    # "He's a Pirate"-inspirierte D-Moll Melodie, zwei 8-Beat Phrasen
    # Phrase 1: Aufsteigende dramatische Linie
    melody_notes = [
        # Phrase 1 (Beats 0-7): Dramatischer Aufstieg
        (293.66, 0,    0.8),   # D4
        (349.23, 1,    0.4),   # F4
        (349.23, 1.5,  0.4),   # F4
        (349.23, 2,    0.8),   # F4
        (392.00, 3,    0.4),   # G4
        (392.00, 3.5,  0.4),   # G4
        (392.00, 4,    0.8),   # G4
        (440.00, 5,    0.4),   # A4
        (466.16, 5.5,  0.4),   # Bb4
        (440.00, 6,    1.8),   # A4 (lang gehalten)
        
        # Phrase 2 (Beats 8-15): Epischer Höhepunkt & Auflösung
        (440.00, 8,    0.8),   # A4
        (523.25, 9,    0.4),   # C5
        (523.25, 9.5,  0.4),   # C5
        (523.25, 10,   0.8),   # C5
        (587.33, 11,   0.4),   # D5  (Höhepunkt!)
        (523.25, 11.5, 0.4),   # C5
        (466.16, 12,   0.8),   # Bb4
        (440.00, 13,   0.4),   # A4
        (392.00, 13.5, 0.4),   # G4
        (349.23, 14,   0.8),   # F4
        (329.63, 15,   0.4),   # E4
        (293.66, 15.5, 0.4),   # D4 (zurück zum Anfang)
    ]
    
    melody = np.zeros_like(t)
    for freq, beat_pos, dur_beats in melody_notes:
        start = beat_pos * beat
        dur = dur_beats * beat
        melody += _synth_note(t, freq, start, dur, 'fiddle', vibrato=0.003)
    
    # ====== HARMONIE / POWER CHORDS (Brass) ======
    # Akkord-Stabs auf starken Beats für episches Gefühl
    harmony_chords = [
        # Beat, Dauer, Noten (Frequenzen)
        (0,  1.8, [146.83, 220.00, 293.66]),   # Dm (D3, A3, D4)
        (2,  1.8, [174.61, 261.63, 349.23]),   # F  (F3, C4, F4)
        (4,  1.8, [130.81, 196.00, 261.63]),   # C  (C3, G3, C4)
        (6,  1.8, [146.83, 220.00, 293.66]),   # Dm (D3, A3, D4)
        (8,  1.8, [174.61, 261.63, 349.23]),   # F  (F3, C4, F4)
        (10, 1.8, [196.00, 293.66, 392.00]),   # G  (G3, D4, G4)  
        (12, 1.8, [174.61, 220.00, 293.66]),   # Dm/F
        (14, 1.8, [130.81, 196.00, 329.63]),   # C/E → Spannung zurück zu D
    ]
    
    harmony = np.zeros_like(t)
    for beat_pos, dur_beats, freqs in harmony_chords:
        start = beat_pos * beat
        dur = dur_beats * beat
        for freq in freqs:
            harmony += _synth_note(t, freq, start, dur, 'brass') * 0.3
    
    # ====== TREIBENDER BASS (Achtel-Noten) ======
    bass_pattern = [
        # (Freq, Beat-Position, Dauer in Beats)
        # Dm
        (73.42, 0, 0.45), (73.42, 0.5, 0.45),     # D2
        (73.42, 1, 0.45), (73.42, 1.5, 0.45),
        # F
        (87.31, 2, 0.45), (87.31, 2.5, 0.45),     # F2
        (87.31, 3, 0.45), (87.31, 3.5, 0.45),
        # C
        (65.41, 4, 0.45), (65.41, 4.5, 0.45),     # C2
        (65.41, 5, 0.45), (65.41, 5.5, 0.45),
        # Dm
        (73.42, 6, 0.45), (73.42, 6.5, 0.45),     # D2
        (73.42, 7, 0.45), (73.42, 7.5, 0.45),
        # F
        (87.31, 8, 0.45), (87.31, 8.5, 0.45),
        (87.31, 9, 0.45), (87.31, 9.5, 0.45),
        # G
        (98.00, 10, 0.45), (98.00, 10.5, 0.45),   # G2
        (98.00, 11, 0.45), (98.00, 11.5, 0.45),
        # Dm/F
        (87.31, 12, 0.45), (87.31, 12.5, 0.45),
        (73.42, 13, 0.45), (73.42, 13.5, 0.45),
        # C → D
        (65.41, 14, 0.45), (65.41, 14.5, 0.45),
        (69.30, 15, 0.45), (73.42, 15.5, 0.45),   # C#2 → D2 (Aufstieg)
    ]
    
    bass = np.zeros_like(t)
    for freq, beat_pos, dur_beats in bass_pattern:
        start = beat_pos * beat
        dur = dur_beats * beat
        bass += _synth_note(t, freq, start, dur, 'bass')
    
    # ====== PERCUSSION / TROMMELN ======
    drums = np.zeros_like(t)
    for i in range(int(duration / beat)):
        b = i * beat
        # Kick auf jeden Beat
        drums += _drum_hit(t, b, 'kick') * 0.4
        # Snare auf Beats 2 und 4 (jeden 2. Beat)
        if i % 2 == 1:
            drums += _drum_hit(t, b, 'snare') * 0.3
        # Hi-Hat Achtel
        drums += _drum_hit(t, b, 'snare') * 0.08
        drums += _drum_hit(t, b + beat * 0.5, 'snare') * 0.06
    
    # ====== STREICHER-PAD (Breite, warme Fläche) ======
    pad_chords = [
        (0,  4, [293.66, 349.23, 440.00]),    # Dm
        (4,  4, [261.63, 329.63, 392.00]),    # C/E  
        (8,  4, [349.23, 440.00, 523.25]),    # F
        (12, 4, [293.66, 349.23, 440.00]),    # Dm
    ]
    pad = np.zeros_like(t)
    for beat_pos, dur_beats, freqs in pad_chords:
        start = beat_pos * beat
        dur = dur_beats * beat
        for freq in freqs:
            pad += _synth_note(t, freq, start, dur, 'strings', vibrato=0.002)
    
    # ====== ZUSAMMENMIXEN ======
    sound = (
        melody  * 0.40 +   # Fiddle-Melodie (lauter)
        harmony * 0.22 +   # Brass-Akkorde
        bass    * 0.30 +   # Treibender Bass
        drums   * 0.25 +   # Percussion
        pad     * 0.12     # Streicher-Pad
    )
    
    # Master-Kompression (soft clipping)
    sound = np.tanh(sound * 1.8) * 0.8
    
    # Loop-Fade für nahtlosen Übergang
    fade_len = int(SAMPLE_RATE * 0.15)
    sound[:fade_len] *= np.linspace(0, 1, fade_len)
    sound[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    return _make_sound(sound)


def generate_battle_music():
    """Epische Kampf/Segel-Musik für das Gameplay - schnell und intensiv (Loop-fähig)"""
    duration = 12.0
    bpm = 150  # Schneller als Menü
    beat = 60.0 / bpm  # 0.4s
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # ====== SCHNELLE FIDDLE-MELODIE ======
    melody_notes = [
        # Phrase 1: Hektische Achtel-Figur
        (293.66, 0,    0.4),   # D4
        (349.23, 0.5,  0.4),   # F4
        (440.00, 1,    0.4),   # A4
        (349.23, 1.5,  0.4),   # F4
        (293.66, 2,    0.4),   # D4
        (349.23, 2.5,  0.4),   # F4
        (392.00, 3,    0.4),   # G4
        (349.23, 3.5,  0.4),   # F4
        
        # Phrase 2: Aufstieg
        (329.63, 4,    0.4),   # E4
        (392.00, 4.5,  0.4),   # G4
        (466.16, 5,    0.4),   # Bb4
        (392.00, 5.5,  0.4),   # G4
        (329.63, 6,    0.4),   # E4
        (349.23, 6.5,  0.4),   # F4
        (293.66, 7,    0.9),   # D4 (lang)
        
        # Phrase 3: Wiederholung mit Variation
        (440.00, 8,    0.4),   # A4
        (523.25, 8.5,  0.4),   # C5
        (587.33, 9,    0.4),   # D5
        (523.25, 9.5,  0.4),   # C5
        (440.00, 10,   0.4),   # A4
        (392.00, 10.5, 0.4),   # G4
        (349.23, 11,   0.4),   # F4
        (329.63, 11.5, 0.4),   # E4
    ]
    
    melody = np.zeros_like(t)
    for freq, beat_pos, dur_beats in melody_notes:
        start = beat_pos * beat
        dur = dur_beats * beat
        melody += _synth_note(t, freq, start, dur, 'fiddle', vibrato=0.004)
    
    # ====== POWER-AKKORDE (Brass, kürzer/aggressiver) ======
    power_chords = [
        (0,  1.5, [146.83, 220.00, 293.66]),    # Dm
        (2,  1.5, [130.81, 196.00, 261.63]),    # C
        (4,  1.5, [116.54, 174.61, 233.08]),    # Bb
        (6,  1.5, [130.81, 196.00, 261.63]),    # C
        (8,  1.5, [146.83, 220.00, 293.66]),    # Dm
        (10, 1.5, [130.81, 196.00, 329.63]),    # C/E
    ]
    
    harmony = np.zeros_like(t)
    for beat_pos, dur_beats, freqs in power_chords:
        start = beat_pos * beat
        dur = dur_beats * beat
        for freq in freqs:
            harmony += _synth_note(t, freq, start, dur, 'brass') * 0.25
    
    # ====== SCHNELLER BASS (Achtel) ======
    bass_seq = [
        73.42, 73.42,  # Dm
        65.41, 65.41,  # C
        58.27, 58.27,  # Bb
        65.41, 65.41,  # C
        73.42, 73.42,  # Dm
        65.41, 65.41,  # C
    ]
    
    bass = np.zeros_like(t)
    for i, freq in enumerate(bass_seq):
        for sub in range(4):  # 4 Achtel pro 2 Beats
            beat_pos = i * 2 + sub * 0.5
            if beat_pos * beat >= duration:
                break
            start = beat_pos * beat
            dur = 0.45 * beat
            bass += _synth_note(t, freq, start, dur, 'bass')
    
    # ====== AGGRESIVE DRUMS ======
    drums = np.zeros_like(t)
    total_beats = int(duration / beat)
    for i in range(total_beats):
        b = i * beat
        # Kick
        drums += _drum_hit(t, b, 'kick') * 0.45
        # Snare auf 2 und 4
        if i % 2 == 1:
            drums += _drum_hit(t, b, 'snare') * 0.35
        # Schnelle Hi-Hats (Sechzehntel-Feeling)
        for sub in [0, 0.25, 0.5, 0.75]:
            drums += _drum_hit(t, b + sub * beat, 'snare') * 0.05
    
    # ====== ZUSAMMENMIXEN ======
    sound = (
        melody  * 0.38 +
        harmony * 0.20 +
        bass    * 0.30 +
        drums   * 0.28
    )
    
    # Soft clipping
    sound = np.tanh(sound * 1.8) * 0.8
    
    # Loop-Fade
    fade_len = int(SAMPLE_RATE * 0.1)
    sound[:fade_len] *= np.linspace(0, 1, fade_len)
    sound[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    return _make_sound(sound)


def generate_ocean_ambience():
    """Ozean-Ambiente - leises Meeresrauschen (Loop-fähig)"""
    duration = 3.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Rauschen mit tiefem Filter-Effekt (simuliert)
    noise = np.random.uniform(-1, 1, len(t))
    
    # Einfacher Tiefpass durch gleitenden Durchschnitt
    window = 200
    filtered = np.convolve(noise, np.ones(window) / window, mode='same')
    
    # Wellenförmige Lautstärkenmodulation
    wave = 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)
    
    sound = filtered * wave * 0.12
    return _make_sound(sound)


# ==================== SOUND MANAGER ====================
class SoundManager:
    """Verwaltet alle Spiel-Sounds"""
    
    def __init__(self):
        # Mixer initialisieren mit guten Werten
        if not pg.mixer.get_init():
            pg.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)
        
        # Alle Sounds vorab generieren
        print("Sounds werden generiert...")
        self.cannon = generate_cannon_sound()
        self.explosion = generate_explosion_sound()
        self.hit = generate_hit_sound()
        self.damage = generate_damage_sound()
        self.gem_pickup = generate_gem_pickup_sound()
        self.levelup = generate_levelup_sound()
        self.death = generate_death_sound()
        self.menu_select = generate_menu_select_sound()
        self.menu_confirm = generate_menu_confirm_sound()
        self.wheel_tick = generate_wheel_spin_sound()
        self.wheel_win = generate_wheel_win_sound()
        self.boss_spawn = generate_boss_spawn_sound()
        self.perk_buy = generate_perk_buy_sound()
        self.error = generate_error_sound()
        self.ocean = generate_ocean_ambience()
        self.menu_music = generate_menu_music()
        self.battle_music = generate_battle_music()
        
        # Master-Lautstärken (0.0 - 1.0)
        self._music_master = 1.0
        self._sfx_master = 1.0
        
        # Base volumes (zum Skalieren)
        self._base_volumes = {
            'cannon': 0.4, 'explosion': 0.5, 'hit': 0.35, 'damage': 0.45,
            'gem_pickup': 0.5, 'levelup': 0.6, 'death': 0.6,
            'menu_select': 0.3, 'menu_confirm': 0.4, 'wheel_tick': 0.25,
            'wheel_win': 0.5, 'boss_spawn': 0.5, 'perk_buy': 0.45, 'error': 0.35,
        }
        self._base_music_volumes = {
            'ocean': 0.15, 'menu_music': 0.45, 'battle_music': 0.35,
        }
        
        # Lautstärken setzen
        for name, vol in self._base_volumes.items():
            getattr(self, name).set_volume(vol)
        for name, vol in self._base_music_volumes.items():
            getattr(self, name).set_volume(vol)
        
        # Genug Kanäle reservieren (Standard ist nur 8!)
        pg.mixer.set_num_channels(16)
        
        # Reservierte Kanäle für Musik/Ambiente (können nicht von .play() gestohlen werden)
        # Kanal 0 = Ocean, Kanal 1 = Menu-Musik, Kanal 2 = Battle-Musik
        pg.mixer.set_reserved(3)
        self._ocean_channel = pg.mixer.Channel(0)
        self._menu_music_channel = pg.mixer.Channel(1)
        self._battle_music_channel = pg.mixer.Channel(2)
        self._ocean_playing = False
        self._menu_music_playing = False
        self._battle_music_playing = False
        
        print("Sounds geladen!")
    
    def play(self, sound_name):
        """Spielt einen Sound ab"""
        snd = getattr(self, sound_name, None)
        if snd is not None:
            snd.play()
    
    def ensure_music_playing(self):
        """Prüft ob Musik-Kanäle noch laufen und startet sie ggf. neu.
        Sollte regelmäßig im Update aufgerufen werden."""
        if self._ocean_playing and not self._ocean_channel.get_busy():
            self._ocean_channel.play(self.ocean, loops=-1)
        if self._menu_music_playing and not self._menu_music_channel.get_busy():
            self._menu_music_channel.play(self.menu_music, loops=-1)
        if self._battle_music_playing and not self._battle_music_channel.get_busy():
            self._battle_music_channel.play(self.battle_music, loops=-1)
    
    def set_music_volume(self, vol):
        """Setzt die Master-Lautstärke für Musik (0.0 - 1.0)"""
        self._music_master = max(0.0, min(1.0, vol))
        for name, base in self._base_music_volumes.items():
            getattr(self, name).set_volume(base * self._music_master)
    
    def set_sfx_volume(self, vol):
        """Setzt die Master-Lautstärke für Sound-Effekte (0.0 - 1.0)"""
        self._sfx_master = max(0.0, min(1.0, vol))
        for name, base in self._base_volumes.items():
            getattr(self, name).set_volume(base * self._sfx_master)
    
    def start_ocean_ambience(self):
        """Startet das Ozean-Ambiente als Loop auf reserviertem Kanal"""
        if not self._ocean_playing:
            self._ocean_channel.play(self.ocean, loops=-1)
            self._ocean_playing = True
    
    def stop_ocean_ambience(self):
        """Stoppt das Ozean-Ambiente"""
        if self._ocean_playing:
            self._ocean_channel.fadeout(1000)
            self._ocean_playing = False
    
    def start_menu_music(self):
        """Startet die Menü-Musik als Loop auf reserviertem Kanal"""
        if not self._menu_music_playing:
            self._menu_music_channel.play(self.menu_music, loops=-1)
            self._menu_music_playing = True
    
    def stop_menu_music(self):
        """Stoppt die Menü-Musik"""
        if self._menu_music_playing:
            self._menu_music_channel.fadeout(500)
            self._menu_music_playing = False
    
    def start_battle_music(self):
        """Startet die Kampf/Segel-Musik als Loop auf reserviertem Kanal"""
        if not self._battle_music_playing:
            self._battle_music_channel.play(self.battle_music, loops=-1)
            self._battle_music_playing = True
    
    def stop_battle_music(self):
        """Stoppt die Kampf-Musik"""
        if self._battle_music_playing:
            self._battle_music_channel.fadeout(800)
            self._battle_music_playing = False


# Globale Instanz (wird beim ersten Import angelegt wenn mixer bereit ist)
_sound_manager = None


def get_sound_manager():
    """Gibt den globalen SoundManager zurück (lazy init)"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager
