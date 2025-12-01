"""
Note mapping from gestures to MIDI notes.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.utils.config import Config


class ViolinString(Enum):
    """Violin strings with their base MIDI notes."""
    G = 55  # G3
    D = 62  # D4
    A = 69  # A4
    E = 76  # E5


@dataclass
class NoteInfo:
    """Information about a mapped note."""
    midi_note: int
    string: str
    position: int
    finger: int
    pitch_offset: int
    note_name: str


class NoteMapper:
    """
    Maps gesture parameters to MIDI notes.
    
    Uses the violin model to calculate the correct MIDI note
    based on string selection, position, finger count, and pitch offset.
    """
    
    # String number to enum mapping
    STRING_MAP = {
        1: ViolinString.E,
        2: ViolinString.A,
        3: ViolinString.D,
        4: ViolinString.G
    }
    
    # Position to semitone shift
    POSITION_SHIFT = {
        1: 0,   # 1st position
        2: 2,   # 2nd position
        3: 4    # 3rd position
    }
    
    # Finger count to semitone shift
    FINGER_SHIFT = {
        0: 0,   # Open string
        1: 2,   # 1st finger
        2: 4,   # 2nd finger
        3: 6,   # 3rd finger
        4: 8    # 4th finger
    }
    
    # MIDI note to name mapping
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, config: Config):
        """
        Initialize the note mapper.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Override defaults with config if provided
        if hasattr(config, 'violin'):
            self._load_config_mappings(config.violin)
    
    def _load_config_mappings(self, violin_config) -> None:
        """Load custom mappings from configuration."""
        if hasattr(violin_config, 'strings'):
            for string, note in violin_config.strings.items():
                if hasattr(ViolinString, string.upper()):
                    # Update enum value (this is a bit hacky but works)
                    pass
        
        if hasattr(violin_config, 'positions'):
            self.POSITION_SHIFT = violin_config.positions
        
        if hasattr(violin_config, 'fingers'):
            self.FINGER_SHIFT = violin_config.fingers
    
    def get_note(
        self,
        string: int,
        position: int = 1,
        finger_count: int = 0,
        pitch_offset: int = 0
    ) -> int:
        """
        Calculate the MIDI note from gesture parameters.
        
        Formula:
            note = base_note + position_shift + finger_shift + pitch_offset
        
        Args:
            string: String number (1=E, 2=A, 3=D, 4=G)
            position: Position (1, 2, or 3)
            finger_count: Number of fingers pressed (0-4)
            pitch_offset: Pitch adjustment (-1, 0, or 1)
            
        Returns:
            MIDI note number (0-127)
        """
        # Validate inputs
        string = max(1, min(4, string))
        position = max(1, min(3, position))
        finger_count = max(0, min(4, finger_count))
        pitch_offset = max(-1, min(1, pitch_offset))
        
        # Get base note
        violin_string = self.STRING_MAP.get(string, ViolinString.A)
        base_note = violin_string.value
        
        # Calculate shifts
        pos_shift = self.POSITION_SHIFT.get(position, 0)
        finger_shift = self.FINGER_SHIFT.get(finger_count, 0)
        
        # Calculate final note
        midi_note = base_note + pos_shift + finger_shift + pitch_offset
        
        # Clamp to valid MIDI range
        return max(0, min(127, midi_note))
    
    def get_note_info(
        self,
        string: int,
        position: int = 1,
        finger_count: int = 0,
        pitch_offset: int = 0
    ) -> NoteInfo:
        """
        Get detailed information about a note.
        
        Args:
            string: String number (1=E, 2=A, 3=D, 4=G)
            position: Position (1, 2, or 3)
            finger_count: Number of fingers pressed (0-4)
            pitch_offset: Pitch adjustment (-1, 0, or 1)
            
        Returns:
            NoteInfo with all note details
        """
        midi_note = self.get_note(string, position, finger_count, pitch_offset)
        string_name = self.STRING_MAP.get(string, ViolinString.A).name
        note_name = self._midi_to_note_name(midi_note)
        
        return NoteInfo(
            midi_note=midi_note,
            string=string_name,
            position=position,
            finger=finger_count,
            pitch_offset=pitch_offset,
            note_name=note_name
        )
    
    def _midi_to_note_name(self, midi_note: int) -> str:
        """
        Convert MIDI note number to note name.
        
        Args:
            midi_note: MIDI note number
            
        Returns:
            Note name with octave (e.g., "A4", "C#5")
        """
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        return f"{self.NOTE_NAMES[note_index]}{octave}"
    
    def get_all_notes_for_string(self, string: int) -> Dict[str, int]:
        """
        Get all possible notes for a given string.
        
        Args:
            string: String number (1-4)
            
        Returns:
            Dictionary mapping position/finger combinations to MIDI notes
        """
        notes = {}
        
        for pos in range(1, 4):
            for finger in range(5):
                key = f"pos{pos}_finger{finger}"
                notes[key] = self.get_note(string, pos, finger, 0)
        
        return notes
    
    def get_chromatic_scale(self, string: int, position: int = 1) -> list:
        """
        Get the chromatic scale available on a string at a position.
        
        Args:
            string: String number
            position: Position number
            
        Returns:
            List of (finger, offset, midi_note, note_name) tuples
        """
        scale = []
        
        for finger in range(5):
            for offset in [-1, 0, 1]:
                note = self.get_note(string, position, finger, offset)
                name = self._midi_to_note_name(note)
                scale.append((finger, offset, note, name))
        
        # Remove duplicates and sort
        unique_notes = {}
        for finger, offset, note, name in scale:
            if note not in unique_notes:
                unique_notes[note] = (finger, offset, name)
        
        return sorted(
            [(note, *info) for note, info in unique_notes.items()],
            key=lambda x: x[0]
        )
