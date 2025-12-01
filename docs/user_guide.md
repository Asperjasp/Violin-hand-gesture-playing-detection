# User Guide

## Getting Started

### Requirements

- **Hardware**: Webcam (720p or higher recommended)
- **Software**: 
  - Python 3.9+
  - Virtual MIDI port
  - MIDI-compatible software (GarageBand, Ableton, FL Studio, etc.)

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up a virtual MIDI port:
   - **Linux**: `sudo modprobe snd-virmidi`
   - **macOS**: Enable IAC Driver in Audio MIDI Setup
   - **Windows**: Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)

3. Run the application:
   ```bash
   python -m src.main --debug
   ```

## Hand Gestures

### Right Hand (Bow Control)

| Gesture | Action |
|---------|--------|
| 1 finger extended | Select E string |
| 2 fingers extended | Select A string |
| 3 fingers extended | Select D string |
| 4 fingers extended | Select G string |
| Pinch thumb + index | Start playing note |
| Release pinch | Stop playing note |

### Left Hand (Pitch Control)

| Gesture | Action |
|---------|--------|
| Hand position low | 1st position |
| Hand position middle | 2nd position |
| Hand position high | 3rd position |
| 0 fingers curled | Open string |
| 1 finger curled | 1st finger (+2 semitones) |
| 2 fingers curled | 2nd finger (+4 semitones) |
| 3 fingers curled | 3rd finger (+6 semitones) |
| 4 fingers curled | 4th finger (+8 semitones) |

## Calibration

Run calibration to adapt position zones to your playing style:

```bash
python -m src.main --calibrate
```

Follow the on-screen instructions to sample each position.

## Configuration

Edit `config/default_config.yaml` to customize:

- Camera settings
- Detection sensitivity
- Position zone thresholds
- MIDI settings
- Database options

## Troubleshooting

### Camera not detected
- Check that no other application is using the camera
- Try a different `device_id` in configuration

### MIDI not working
- Verify virtual MIDI port is active
- Check port name matches configuration
- Ensure DAW is listening on the correct port

### Hand detection unstable
- Ensure good lighting
- Keep hands in frame
- Adjust `min_detection_confidence` in config
