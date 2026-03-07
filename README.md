# Piraten RPG

Du bist ein Admiral und du befreist Inseln von Piraten.

- Du hast ein Schiff mit Matrosen, Kanonen und anderen Waffen
- Wenn dein Schiff untergeht, ist das Spiel vorbei
- Du kannst andere Schiffe versenken und/oder plündern und die Schätze bergen

---

## Voraussetzungen

- **Python 3.13+** — [python.org/downloads](https://www.python.org/downloads/)
  - Bei der Installation **"Add python.exe to PATH"** aktivieren

---

## Setup

### Option A — Virtuelle Umgebung (empfohlen)

```powershell
# Repo klonen und in den Ordner wechseln
git clone https://github.com/theRealProHacker/2drpg.git
cd 2drpg

# Virtuelle Umgebung erstellen
python -m venv .venv

# Aktivieren (PowerShell)
.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install pygame numpy pgsm
```

> **Linux / macOS:** statt `.venv\Scripts\Activate.ps1` → `source .venv/bin/activate`

### Option B — Globale Installation

```powershell
pip install pygame numpy pgsm
```

---

## Spiel starten

```powershell
# Bei venv: erst aktivieren, dann starten
.venv\Scripts\Activate.ps1
python game.py
```

Oder direkt ohne vorherige Aktivierung:

```powershell
.venv\Scripts\python.exe game.py
```

---

## Build (Windows-Executable)

Mit [PyInstaller](https://pyinstaller.org/) lässt sich eine eigenständige `.exe` erstellen:

```powershell
# PyInstaller installieren (falls nicht vorhanden)
pip install pyinstaller

# Executable bauen
pyinstaller pirates.spec
```

Die fertige Anwendung liegt danach in `dist/Pirates/`. Starte sie mit `dist/Pirates/Pirates.exe`.

---

## Projektstruktur

```
2drpg/
├── game.py               # Einstiegspunkt – Spielschleife & Fenstererstellung
├── sounds.py             # Prozedurale Soundeffekte (numpy + pygame)
├── spritesheet.py        # Spritesheet-Loader
├── circle_collision.py   # Kollisionserkennung
├── gems_save.json        # Spielstand (Gems, Perks, Highscore, Profil)
├── pirates.spec          # PyInstaller-Konfiguration
├── states/
│   ├── menu.py           # Hauptmenü, Perk-System
│   ├── play.py           # Gameplay (Schiffe, Inseln, Kampf)
│   ├── pause.py          # Pause-Bildschirm mit Stats & Upgrades
│   └── profile.py        # Talentbaum & Fortschritt
└── assets/               # Grafiken, Spritesheets, Sounds
```

---

## Abhängigkeiten

| Paket | Version | Zweck |
|-------|---------|-------|
| pygame | 2.6.1+ | Spielframework |
| numpy | 2.x | Prozedurale Soundgenerierung |
| StateManager | — | Spielzustands-Verwaltung |

### Entwicklung (optional)

| Paket | Zweck |
|-------|-------|
| pyinstaller | Executable-Build |
| ruff | Linter / Formatter |