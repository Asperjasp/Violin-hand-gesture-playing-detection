"""
Simple audio player for testing without external MIDI setup.
Uses pygame to generate and play tones directly.
"""

import threading
import numpy as np
from typing import Optional, Dict

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioPlayer:
    """
    Generates and plays audio tones for MIDI notes.
    
    This is a fallback for when no MIDI synthesizer is available.
    Uses simple sine wave synthesis with pygame.
    """
    
    # Standard A4 = 440 Hz
    A4_FREQ = 440.0
    A4_MIDI = 69
    
    def __init__(self, sample_rate: int = 44100, volume: float = 0.4):
        """
        Initialize the audio player.
        
        Args:
            sample_rate: Audio sample rate in Hz
            volume: Master volume (0.0 - 1.0)
        """
        self.sample_rate = sample_rate
        self.volume = volume
        self.active_notes: Dict[int, pygame.mixer.Channel] = {}
        self.cached_sounds: Dict[int, pygame.mixer.Sound] = {}
        self._lock = threading.Lock()
        
        if not PYGAME_AVAILABLE:
            print("⚠️  pygame not available - audio disabled")
            self.enabled = False
            return
        
        try:
            # Better audio settings: stereo, larger buffer for smooth sound
            pygame.mixer.pre_init(sample_rate, -16, 2, 2048)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self.enabled = True
            print("🔊 Audio player initialized (pygame)")
            
            # Pre-generate common violin notes (G3 to E6)
            self._precache_notes()
        except Exception as e:
            print(f"⚠️  Audio init failed: {e}")
            self.enabled = False
    
    def _precache_notes(self):
        """Pre-generate sounds for common violin range."""
        # Violin range: G3 (55) to E6 (88)
        for midi_note in range(55, 89):
            self.cached_sounds[midi_note] = self._generate_violin_tone(midi_note)
        print(f"   Cached {len(self.cached_sounds)} notes")
    
    def midi_to_freq(self, midi_note: int) -> float:
        """Convert MIDI note number to frequency in Hz."""
        return self.A4_FREQ * (2.0 ** ((midi_note - self.A4_MIDI) / 12.0))
    
    def _generate_violin_tone(self, midi_note: int, duration: float = 3.0) -> pygame.mixer.Sound:
        """
        Generate a violin-like tone.
        
        Args:
            midi_note: MIDI note number
            duration: Duration in seconds
            
        Returns:
            pygame Sound object
        """
        freq = self.midi_to_freq(midi_note)
        n_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float64)
        
        # Violin-like sound with harmonics
        wave = np.zeros(n_samples, dtype=np.float64)
        
        # Violin harmonic series (relative amplitudes based on real violin spectra)
        harmonics = [
            (1, 1.0),      # Fundamental
            (2, 0.6),      # 2nd harmonic
            (3, 0.4),      # 3rd harmonic  
            (4, 0.25),     # 4th harmonic
            (5, 0.15),     # 5th harmonic
            (6, 0.1),      # 6th harmonic
            (7, 0.08),     # 7th harmonic
            (8, 0.05),     # 8th harmonic
        ]
        
        for harmonic_num, amp in harmonics:
            harmonic_freq = freq * harmonic_num
            if harmonic_freq < self.sample_rate / 2:  # Nyquist limit
                # Add slight vibrato for more realistic sound
                vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 5.5 * t)  # 5.5 Hz vibrato
                wave += amp * np.sin(2 * np.pi * harmonic_freq * vibrato * t)
        
        # Apply ADSR envelope for bowed string
        attack_time = 0.08
        decay_time = 0.1
        sustain_level = 0.8
        release_time = 0.15
        
        attack_samples = int(attack_time * self.sample_rate)
        decay_samples = int(decay_time * self.sample_rate)
        release_samples = int(release_time * self.sample_rate)
        sustain_samples = n_samples - attack_samples - decay_samples - release_samples
        
        envelope = np.concatenate([
            np.linspace(0, 1, attack_samples),                    # Attack
            np.linspace(1, sustain_level, decay_samples),         # Decay
            np.ones(max(0, sustain_samples)) * sustain_level,     # Sustain
            np.linspace(sustain_level, 0, release_samples)        # Release
        ])
        
        # Ensure envelope matches wave length
        if len(envelope) > n_samples:
            envelope = envelope[:n_samples]
        elif len(envelope) < n_samples:
            envelope = np.pad(envelope, (0, n_samples - len(envelope)), constant_values=0)
        
        wave *= envelope
        
        # Normalize
        max_val = np.max(np.abs(wave))
        if max_val > 0:
            wave = wave / max_val * self.volume
        
        # Convert to stereo 16-bit
        wave_int = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave_int, wave_int))
        
        return pygame.mixer.Sound(stereo)
    
    def note_on(self, note: int, velocity: Optional[int] = None) -> None:
        """
        Start playing a note.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (unused, for API compatibility)
        """
        if not self.enabled or note < 0 or note > 127:
            return
        
        with self._lock:
            # Stop previous instance of this note
            if note in self.active_notes:
                self.active_notes[note].fadeout(50)
            
            # Get cached sound or generate new one
            if note in self.cached_sounds:
                sound = self.cached_sounds[note]
            else:
                sound = self._generate_violin_tone(note)
                self.cached_sounds[note] = sound
            
            # Find free channel and play
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(sound, loops=-1)  # Loop until stopped
                self.active_notes[note] = channel
    
    def note_off(self, note: int) -> None:
        """
        Stop playing a note.
        
        Args:
            note: MIDI note number (0-127)
        """
        if not self.enabled:
            return
        
        with self._lock:
            if note in self.active_notes:
                # Fade out for smoother stop (100ms)
                self.active_notes[note].fadeout(100)
                del self.active_notes[note]
    
    def all_notes_off(self) -> None:
        """Stop all active notes."""
        if not self.enabled:
            return
        
        with self._lock:
            for channel in self.active_notes.values():
                channel.fadeout(100)
            self.active_notes.clear()
    
    def close(self) -> None:
        """Clean up audio resources."""
        self.all_notes_off()
        if self.enabled:
            pygame.mixer.quit()
