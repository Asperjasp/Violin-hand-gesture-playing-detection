This guide explains how to get **realistic violin sound** from the hand gesture detection system.

## The Challenge

The built-in audio (`--audio` or `--realistic` flags) uses synthesized sounds which don't match the quality of real violin recordings. For professional-quality sound, you need to route the MIDI output to dedicated audio software.

## Architecture

```
┌──────────────────┐     MIDI      ┌──────────────────┐      Audio      ┌─────────┐
│  Python App      │ ───────────→  │  Virtual MIDI    │  ───────────→   │   DAW   │
│  (Hand Gesture   │               │  Port            │                 │  + VST  │
│   Detection)     │               │  (loopMIDI)      │                 │  Plugin │
└──────────────────┘               └──────────────────┘                 └─────────┘
                                                                              │
                                                                              ▼
                                                                        🔊 Speakers
```

---

## Option A: Windows Setup (Recommended)

### Step 1: Install loopMIDI

1. Download from: https://www.tobias-erichsen.de/software/loopmidi.html
2. Install and run
3. Click "+" to create a new port named **"ViolinCV"**

### Step 2: Install a DAW

Choose one:
- **Reaper** (free trial, very lightweight): https://www.reaper.fm/
- **LMMS** (free, open source): https://lmms.io/
- **Ableton Live Lite** (often free with hardware)
- **FL Studio** (free trial): https://www.image-line.com/

### Step 3: Get a Violin VST Plugin

**Free Options:**
- **Spitfire LABS** - https://labs.spitfireaudio.com/ (includes strings)
- **Versilian VSCO2** - http://vis.versilstudios.net/vsco-2.html
- **Sonatina Symphonic Orchestra** - https://github.com/peastman/sso

**Paid Options (best quality):**
- **SWAM Violin** (~$150) - Physical modeling, extremely realistic
- **Native Instruments Kontakt** - Professional orchestral libraries
- **Spitfire Chamber Strings** - Sampled recordings

### Step 4: Configure the DAW

1. Open your DAW
2. Create a new MIDI track
3. Set MIDI input to **"ViolinCV"** (the loopMIDI port)
4. Load your violin VST on that track
5. Arm the track for recording/monitoring

### Step 5: Run Python App on Windows

```powershell
# In Windows PowerShell (not WSL)
cd C:\path\to\Violin-Auto-Playing
python -m src.main --video your_video.mp4 --debug
```

The app will automatically send MIDI to available ports including loopMIDI.

---

## Option B: Better SoundFonts with FluidSynth (Linux/WSL)

If you want to stay in Linux, improve the FluidSynth sound quality:

### Download Better SoundFonts

```bash
# Create directory for soundfonts
mkdir -p ~/soundfonts

# Download Sonatina Symphonic Orchestra (high quality, free)
cd ~/soundfonts
wget https://github.com/peastman/sso/releases/download/v1.0/Sonatina_Symphonic_Orchestra.sf2.tar.gz
tar -xzf Sonatina_Symphonic_Orchestra.sf2.tar.gz

# Or download Arachno SoundFont
wget http://www.arachnosoft.com/main/download.php?id=arachno-soundfont -O arachno.sf2
```

### Use Custom SoundFont

Modify the FluidSynth player to use a better soundfont:

```python
# In src/music/fluidsynth_player.py, change:
soundfont_path = "/home/YOUR_USER/soundfonts/Sonatina_Symphonic_Orchestra.sf2"
```

Or set via environment variable:

```bash
export SOUNDFONT_PATH=~/soundfonts/Sonatina_Symphonic_Orchestra.sf2
python -m src.main --video video.mp4 --realistic --debug
```

---

## Option C: JACK Audio + Ardour (Linux Pro Setup)

For professional Linux audio:

```bash
# Install JACK and Ardour
sudo apt install jackd2 qjackctl ardour

# Start JACK
qjackctl &

# Run your app
python -m src.main --video video.mp4 --debug
```

Then use Ardour with Linux VST plugins like:
- **Sfizz** (SFZ sample player)
- **Calf Plugins** (effects)

---

## Quick Comparison

| Option | Quality | Complexity | Cost |
|--------|---------|------------|------|
| Built-in pygame | ⭐ | Easy | Free |
| FluidSynth + default SF | ⭐⭐ | Easy | Free |
| FluidSynth + good SF | ⭐⭐⭐ | Medium | Free |
| DAW + free VST | ⭐⭐⭐⭐ | Medium | Free |
| DAW + SWAM Violin | ⭐⭐⭐⭐⭐ | Medium | $150 |

---

## Recommended Path

1. **For testing**: Use `--realistic` flag (FluidSynth)
2. **For demos**: Install Reaper + Spitfire LABS (both free)
3. **For production**: SWAM Violin or Kontakt libraries

---

## Troubleshooting

### No MIDI output available
```bash
# Check available MIDI ports
python -c "import rtmidi; m = rtmidi.MidiOut(); print(m.get_ports())"
```

### FluidSynth no sound
```bash
# Test FluidSynth directly
fluidsynth -a pulseaudio /usr/share/sounds/sf2/FluidR3_GM.sf2
# Then type: noteon 0 69 100
```

### DAW not receiving MIDI
- Make sure loopMIDI is running
- Check DAW MIDI input settings
- Verify Python is sending to correct port
