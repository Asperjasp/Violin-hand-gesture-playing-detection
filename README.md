
# 🎻 Violin Auto-Playing with Hand Gestures

A computer vision application that uses **hand gestures** to play the **violin** using **MIDI output**.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Hand Gesture Notation](#hand-gesture-notation)
- [MIDI Mapping](#midi-mapping)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Database Integration](#database-integration)
- [Development Roadmap](#development-roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Introduction

The idea for this project is to develop a computer vision application capable of using **hand gestures** to play the **violin** using **MIDI Formatting**. By leveraging real-time hand tracking, users can simulate violin playing through intuitive gestures that map to musical notes and expressions.

---

## ✨ Features

- **Real-time Hand Tracking**: Uses MediaPipe for accurate hand landmark detection
- **Dual Hand Recognition**: Left hand for pitch/position, right hand for bowing
- **MIDI Output**: Generates standard MIDI signals compatible with any DAW or synthesizer
- **Position Detection**: Supports 1st, 2nd, and 3rd violin positions
- **String Selection**: All four violin strings (G, D, A, E) accessible
- **Pitch Modification**: Sharp/flat adjustments through finger orientation
- **Performance Logging**: Database integration for tracking practice sessions

---

## Orchestration 🖱️



## 🖐️ Hand Gesture Notation

For this purpose, we have come up with the following notation:

| Parameter                     | Hand       | Gesture / CV Metric                                        | Range / Condition                                                                       | Musical Action                                                                                            |
| ----------------------------- | ---------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| String Selection              | Right Hand | Number of Extended Fingers (Index through Pinky)           | 1, 2, 3, or 4                                                                           | Maps to the string: 1 (E), 2 (A), 3 (D), 4 (G)                                                            |
| Bow Trigger (ON/OFF)          | Right Hand | Thumb-Index Pinch Distance                                 | Distance < $\epsilon$ (Threshold)                                                       | Note ON (Start playing the selected note)                                                                 |
| Bow Stop                      | Right Hand | Thumb-Index Pinch Distance                                 | Distance > $\epsilon$ (Threshold)                                                       | Note OFF (Stop playing the note)                                                                          |
| Violin Position               | Left Hand  | Normalized $Y$-Coordinate of Thumb Tip ($Y_{Thumb, Norm}$) | Discrete Zones based on calibration: $Y_{Low}$ (1st), $Y_{Mid}$ (2nd), $Y_{High}$ (3rd) | Sets the Base Semitone Shift for all notes (e.g., 2nd Position shifts pitch by 2 semitones from 1st Pos) |
| Finger Count                  | Left Hand  | Number of Pressed Fingers (Index through Pinky)            | 0, 1, 2, 3, or 4                                                                        | Sets the number of semitones above the open string defined by the Finger Count map                        |
| Pitch Displacement (Advanced) | Left Hand  | Finger Orientation (Z-Axis/Roll)                           | Upwards ($\approx$ Flat) / Downwards ($\approx$ Sharp)                                  | Adjusts the final pitch by $\pm 1$ semitone (e.g., to play F instead of F$\sharp$)                        |

---

## 🎵 MIDI Mapping

The following table shows the MIDI note mapping for each string and position:

| String Name | Base MIDI Note (Open String) | Position Shift (Sem. from 1st Pos) | Finger Count (Sem. from Open String) |
| ----------- | ---------------------------- | ---------------------------------- | ------------------------------------ |
| E           | 76 (E5)                      | 1st Pos: 0, 2nd Pos: 2, 3rd Pos: 4 | 0: Open, 1: +2, 2: +4, 3: +6, 4: +8  |
| A           | 69 (A4)                      | 1st Pos: 0, 2nd Pos: 2, 3rd Pos: 4 | 0: Open, 1: +2, 2: +4, 3: +6, 4: +8  |
| D           | 62 (D4)                      | 1st Pos: 0, 2nd Pos: 2, 3rd Pos: 4 | 0: Open, 1: +2, 2: +4, 3: +6, 4: +8  |
| G           | 55 (G3)                      | 1st Pos: 0, 2nd Pos: 2, 3rd Pos: 4 | 0: Open, 1: +2, 2: +4, 3: +6, 4: +8  |

### MIDI Note Calculation Formula

```
Final_MIDI_Note = Base_Note + Position_Shift + Finger_Semitones + Pitch_Displacement
```

Where:
- **Base_Note**: Open string MIDI value (G=55, D=62, A=69, E=76)
- **Position_Shift**: 0 (1st), 2 (2nd), or 4 (3rd position)
- **Finger_Semitones**: 0, 2, 4, 6, or 8 based on finger count
- **Pitch_Displacement**: -1, 0, or +1 for flat/natural/sharp

---

## 🔊 Audio Synthesis

The application includes a built-in audio synthesizer for testing without external MIDI software. Use the `--audio` flag to enable direct sound output.

### How Sound is Generated

The `AudioPlayer` class (`src/music/audio_player.py`) generates violin-like tones using **additive synthesis**:

```
MIDI Note → Frequency (Hz) → Waveform Generation → ADSR Envelope → Speaker
```

### 1. Harmonic Series (Timbre)

Real violin strings produce not just a fundamental frequency, but a series of **harmonics** (overtones). Our synthesizer mimics this:

```python
harmonics = [
    (1, 1.0),    # Fundamental frequency (strongest)
    (2, 0.6),    # 2nd harmonic (octave above)
    (3, 0.4),    # 3rd harmonic
    (4, 0.25),   # 4th harmonic
    (5, 0.15),   # 5th harmonic
    ...
]
```

Each harmonic is a sine wave at a multiple of the fundamental frequency:

$$f_n = n \times f_0$$

Where $f_0$ is the fundamental frequency and $n$ is the harmonic number.

### 2. ADSR Envelope (Note Shape)

To prevent abrupt "clicks" and give notes a natural shape, we apply an **ADSR envelope**:

```
Volume
   │
1.0├──╮
   │   ╲
0.8├────╲────────────────╮
   │                      ╲
0.0├──────────────────────────
   └─────┬──┬──────────┬──┬───→ Time
         A  D    S      R

A = Attack  (0.08s) - Note starts, volume rises
D = Decay   (0.10s) - Initial peak fades to sustain
S = Sustain (0.80)  - Steady playing level
R = Release (0.15s) - Note ends, volume fades out
```

### 3. Vibrato (Expression)

A subtle pitch oscillation adds realism:

$$vibrato = 1.0 + 0.003 \times \sin(2\pi \times 5.5 \times t)$$

This creates a ±0.3% pitch variation at 5.5 Hz (typical violin vibrato rate).

### 4. Note Debouncing

To prevent rapid note flickering from hand tremors, a **debounce** filter is applied:

- Notes cannot change faster than every **150ms**
- Position changes are filtered at **200ms**

This prevents the "crushed fly" sound effect from rapid start/stop cycles.

### Limitations vs. Real Violin

| Aspect | Our Synth | Real Violin |
|--------|-----------|-------------|
| Sound Source | Pure sine waves | Bow friction (stick-slip) |
| Harmonics | Static ratios | Dynamic with bow pressure |
| Resonance | None | Wood body resonance |
| Noise | Clean signal | Rosin, bow hair texture |
| Expression | Fixed vibrato | Player-controlled |

### For Better Sound Quality

For professional-quality violin sound, connect the MIDI output to:
- **DAW Software**: Ableton, FL Studio, Logic Pro
- **VST Plugins**: SWAM Violin, Kontakt, Spitfire Audio
- **Hardware Synths**: Roland, Yamaha sound modules

---

## 📁 Project Structure

```
Violin-Auto-Playing/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   │
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── hand_detector.py       # MediaPipe hand detection wrapper
│   │   ├── gesture_recognizer.py  # Gesture interpretation logic
│   │   └── calibration.py         # Position calibration utilities
│   │
│   ├── music/
│   │   ├── __init__.py
│   │   ├── midi_controller.py     # MIDI output handling
│   │   ├── note_mapper.py         # Gesture to note mapping
│   │   └── violin_model.py        # Violin-specific music logic
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py              # Database models/schemas
│   │   ├── connection.py          # Database connection handler
│   │   └── logger.py              # Performance logging utilities
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       └── helpers.py             # Utility functions
│
├── tests/
│   ├── __init__.py
│   ├── test_hand_detector.py
│   ├── test_gesture_recognizer.py
│   ├── test_midi_controller.py
│   └── test_note_mapper.py
│
├── config/
│   ├── default_config.yaml        # Default configuration
│   └── calibration_profiles/      # Saved calibration data
│
├── data/
│   ├── performance_logs/          # SQLite database files
│   └── recordings/                # Optional MIDI recordings
│
└── docs/
    ├── architecture.md            # System architecture documentation
    ├── api_reference.md           # API documentation
    └── user_guide.md              # User manual
```

---

## 🛠️ Installation

### Prerequisites

- Python 3.9 or higher
- Webcam or external camera
- MIDI-compatible software (e.g., GarageBand, Ableton, FL Studio)
- Virtual MIDI port (e.g., loopMIDI on Windows, IAC Driver on macOS)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Violin-Auto-Playing.git
   cd Violin-Auto-Playing
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Set up virtual MIDI port**
   - **Linux**: Install `qjackctl` or use ALSA MIDI
   - **macOS**: Enable IAC Driver in Audio MIDI Setup
   - **Windows**: Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)

---

## 🚀 Usage

### Basic Usage

```bash
python src/main.py
```

### With Calibration

```bash
python src/main.py --calibrate
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--calibrate` | Run position calibration before starting |
| `--config <file>` | Use custom configuration file |
| `--debug` | Enable debug visualization |
| `--no-db` | Disable database logging |
| `--midi-port <name>` | Specify MIDI output port |
| `--audio` | Enable direct audio output (no external synth needed) |
| `--no-midi` | Disable MIDI output (visual only mode) |
| `--video <file>` | Use video file instead of camera |
| `--camera <index>` | Specify camera device index |

### Examples

```bash
# Basic usage with camera
python -m src.main

# Test with video file and audio output
python -m src.main --video recording.mp4 --audio --debug

# Debug mode with direct audio (no external MIDI)
python -m src.main --audio --no-midi --debug

# Connect to external synthesizer
python -m src.main --midi-port "FluidSynth"
```

---

## ⚙️ Configuration

Configuration is managed through YAML files in the `config/` directory.

### Key Configuration Options

```yaml
# config/default_config.yaml

camera:
  device_id: 0
  resolution: [1280, 720]
  fps: 30

detection:
  min_detection_confidence: 0.7
  min_tracking_confidence: 0.5
  max_num_hands: 2

thresholds:
  pinch_epsilon: 0.05          # Bow trigger threshold
  position_zones:
    first: [0.0, 0.33]
    second: [0.33, 0.66]
    third: [0.66, 1.0]

midi:
  port_name: "ViolinCV"
  velocity: 100
  channel: 0

database:
  enabled: true
  path: "data/performance_logs/sessions.db"
```

---

## 💾 Database Integration

The database is implemented in the **MIDI Output Integration** phase. Instead of just sending a MIDI signal, the application also logs the event to the database.

### Database Schema

```sql
-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    total_notes INTEGER DEFAULT 0,
    avg_accuracy REAL
);

-- Notes table
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    timestamp DATETIME NOT NULL,
    midi_note INTEGER NOT NULL,
    string_played VARCHAR(1),
    position INTEGER,
    finger_count INTEGER,
    duration_ms INTEGER,
    velocity INTEGER
);

-- Performance metrics table
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    metric_type VARCHAR(50),
    value REAL,
    recorded_at DATETIME
);
```

### Tracked Metrics

- **Notes per session**: Total notes played
- **Practice duration**: Time spent practicing
- **Note distribution**: Which notes are played most frequently
- **Position usage**: Distribution across violin positions
- **String preference**: Which strings are used most

---

## 📅 Development Roadmap

### Phase 1: Core Computer Vision ✅
- [x] Project structure setup
- [ ] MediaPipe hand detection integration
- [ ] Basic gesture recognition (finger counting)
- [ ] Pinch detection for bow trigger

### Phase 2: Gesture Refinement
- [ ] Position zone detection and calibration
- [ ] Finger orientation detection (pitch displacement)
- [ ] Dual-hand tracking synchronization
- [ ] Gesture smoothing and debouncing

### Phase 3: MIDI Integration
- [ ] MIDI output setup
- [ ] Note mapping implementation
- [ ] Velocity control (optional)
- [ ] Note-on/note-off timing

### Phase 4: MIDI Output & Database Integration
- [ ] SQLite database setup
- [ ] Session logging
- [ ] Performance metrics tracking
- [ ] Data visualization dashboard

### Phase 5: Polish & Extras
- [ ] Configuration GUI
- [ ] Calibration wizard
- [ ] Practice mode with visual feedback
- [ ] Recording and playback functionality

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_gesture_recognizer.py -v
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all public functions
- Include unit tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for hand tracking
- [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi) for MIDI output
- The open-source community for inspiration

---

## 📬 Contact

**Project Link**: [https://github.com/yourusername/Violin-Auto-Playing](https://github.com/yourusername/Violin-Auto-Playing)

---

*Made with ❤️ and 🎻*



