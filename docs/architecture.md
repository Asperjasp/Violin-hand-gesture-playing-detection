# System Architecture

## Overview

The Violin Auto-Playing application follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Application                          │
│                          (main.py)                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  Vision   │ │   Music   │ │ Database  │ │   Utils   │
│  Module   │ │   Module  │ │  Module   │ │  Module   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

## Data Flow

```
Camera Input
    │
    ▼
┌──────────────────┐
│  Hand Detector   │ ─── MediaPipe Hands
│  (hand_detector) │
└────────┬─────────┘
         │ HandLandmarks
         ▼
┌──────────────────┐
│ Gesture Recognizer│
│ (gesture_recognizer)│
└────────┬─────────┘
         │ GestureState
         ▼
┌──────────────────┐
│   Note Mapper    │
│  (note_mapper)   │
└────────┬─────────┘
         │ MIDI Note
         ▼
┌──────────────────┐     ┌──────────────────┐
│ MIDI Controller  │────▶│   DAW / Synth    │
│(midi_controller) │     │   (External)     │
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Performance      │
│ Logger (database)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  SQLite Database │
└──────────────────┘
```

## Module Descriptions

### Vision Module (`src/vision/`)

| Component | Responsibility |
|-----------|---------------|
| `hand_detector.py` | Wraps MediaPipe Hands for landmark detection |
| `gesture_recognizer.py` | Interprets landmarks as musical gestures |
| `calibration.py` | Position zone calibration utilities |

### Music Module (`src/music/`)

| Component | Responsibility |
|-----------|---------------|
| `midi_controller.py` | Sends MIDI messages to virtual port |
| `note_mapper.py` | Converts gestures to MIDI notes |
| `violin_model.py` | Violin-specific music theory logic |

### Database Module (`src/database/`)

| Component | Responsibility |
|-----------|---------------|
| `models.py` | SQLAlchemy ORM models |
| `connection.py` | Database connection management |
| `logger.py` | Performance logging utilities |

### Utils Module (`src/utils/`)

| Component | Responsibility |
|-----------|---------------|
| `config.py` | Configuration management |
| `helpers.py` | Utility functions (FPS, debounce, etc.) |

## Key Design Decisions

1. **Dependency Injection**: Components receive configuration via constructor
2. **Dataclasses**: Used for structured data (landmarks, gestures, notes)
3. **Context Managers**: Safe resource handling for database sessions
4. **Hysteresis**: Pinch detection uses different thresholds for on/off to prevent flickering
