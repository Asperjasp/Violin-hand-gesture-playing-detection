"""
FluidSynth-based audio player for realistic instrument sounds.
Uses the FluidSynth library to play SoundFont instruments.
"""

import subprocess
import socket
import time
import threading
from typing import Optional, Dict, Set
import os


class FluidSynthPlayer:
    """
    Plays notes using FluidSynth for realistic instrument sounds.
    
    FluidSynth is a software synthesizer that uses SoundFont (.sf2) files
    to produce high-quality instrument sounds, including violin.
    
    This class starts FluidSynth as a background process and communicates
    with it via its shell interface.
    """
    
    # General MIDI program numbers
    INSTRUMENTS = {
        'violin': 40,
        'viola': 41,
        'cello': 42,
        'contrabass': 43,
        'acoustic_grand_piano': 0,
        'strings_ensemble': 48,
    }
    
    def __init__(
        self,
        soundfont_path: str = "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        instrument: str = 'violin',
        audio_driver: str = 'pulseaudio',
        gain: float = 1.0,
        debug: bool = False
    ):
        """
        Initialize FluidSynth player.
        
        Args:
            soundfont_path: Path to SoundFont file
            instrument: Instrument name (violin, viola, cello, etc.)
            audio_driver: Audio driver (pulseaudio, alsa, jack)
            gain: Master volume (0.0 - 5.0)
            debug: Print debug messages when notes play
        """
        self.soundfont_path = soundfont_path
        self.instrument = instrument
        self.audio_driver = audio_driver
        self.gain = gain
        self.debug = debug
        self.process: Optional[subprocess.Popen] = None
        self.active_notes: Set[int] = set()
        self._lock = threading.Lock()
        self.enabled = False
        self.channel = 0
        
        # Check if soundfont exists
        if not os.path.exists(soundfont_path):
            # Try alternative paths
            alt_paths = [
                "/usr/share/sounds/sf2/FluidR3_GM.sf2",
                "/usr/share/soundfonts/FluidR3_GM.sf2",
                "/usr/share/sounds/sf2/default-GM.sf2",
                "~/.local/share/sounds/sf2/FluidR3_GM.sf2",
            ]
            for path in alt_paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    self.soundfont_path = expanded
                    break
            else:
                print(f"⚠️  SoundFont not found. Install with: sudo apt install fluid-soundfont-gm")
                return
        
        self._start_fluidsynth()
    
    def _start_fluidsynth(self) -> None:
        """Start FluidSynth process."""
        try:
            # Start FluidSynth in server mode with shell interface
            cmd = [
                'fluidsynth',
                '-a', self.audio_driver,
                '-g', str(self.gain),
                '-o', 'synth.chorus.active=1',
                '-o', 'synth.reverb.active=1',
                '-o', 'synth.reverb.room-size=0.6',
                '-o', 'synth.reverb.damp=0.5',
                '-o', 'synth.reverb.level=0.7',
                '-q',  # Quiet mode
                '-i',  # No interactive shell prompt
                self.soundfont_path
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for FluidSynth to initialize
            time.sleep(1.0)
            
            # Check if process is running
            if self.process.poll() is None:
                self.enabled = True
                print(f"🎻 FluidSynth initialized with {os.path.basename(self.soundfont_path)}")
                
                # Set instrument to violin (program 40)
                self._send_command(f"prog {self.channel} {self.INSTRUMENTS.get(self.instrument, 40)}")
                print(f"   Instrument: {self.instrument} (GM #{self.INSTRUMENTS.get(self.instrument, 40)})")
            else:
                stderr = self.process.stderr.read() if self.process.stderr else "Unknown error"
                print(f"⚠️  FluidSynth failed to start: {stderr}")
                self.enabled = False
                
        except FileNotFoundError:
            print("⚠️  FluidSynth not installed. Install with: sudo apt install fluidsynth")
            self.enabled = False
        except Exception as e:
            print(f"⚠️  FluidSynth error: {e}")
            self.enabled = False
    
    def _send_command(self, command: str) -> None:
        """Send a command to FluidSynth."""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                self.enabled = False
    
    def note_on(self, note: int, velocity: int = 100) -> None:
        """
        Start playing a note.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity/volume (0-127)
        """
        if not self.enabled or note < 0 or note > 127:
            return
        
        with self._lock:
            self._send_command(f"noteon {self.channel} {note} {velocity}")
            self.active_notes.add(note)
            if self.debug:
                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                name = note_names[note % 12] + str(note // 12 - 1)
                print(f"🎵 FluidSynth: {name} (MIDI {note})")
    
    def note_off(self, note: int) -> None:
        """
        Stop playing a note.
        
        Args:
            note: MIDI note number (0-127)
        """
        if not self.enabled:
            return
        
        with self._lock:
            self._send_command(f"noteoff {self.channel} {note}")
            self.active_notes.discard(note)
    
    def all_notes_off(self) -> None:
        """Stop all currently playing notes."""
        if not self.enabled:
            return
        
        with self._lock:
            for note in list(self.active_notes):
                self._send_command(f"noteoff {self.channel} {note}")
            self.active_notes.clear()
    
    def set_instrument(self, instrument: str) -> None:
        """
        Change the instrument.
        
        Args:
            instrument: Instrument name (violin, viola, cello, etc.)
        """
        if instrument in self.INSTRUMENTS:
            self.instrument = instrument
            program = self.INSTRUMENTS[instrument]
            self._send_command(f"prog {self.channel} {program}")
            print(f"🎵 Instrument changed to: {instrument}")
    
    def set_reverb(self, room_size: float = 0.6, damp: float = 0.5, level: float = 0.7) -> None:
        """Adjust reverb settings for richer sound."""
        self._send_command(f"reverb {room_size} {damp} 0.5 {level}")
    
    def close(self) -> None:
        """Clean up and close FluidSynth."""
        self.all_notes_off()
        
        if self.process:
            try:
                self._send_command("quit")
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            self.process = None
        
        self.enabled = False


# Alias for backwards compatibility
class RealisticAudioPlayer(FluidSynthPlayer):
    """Alias for FluidSynthPlayer - provides realistic instrument sounds."""
    pass
