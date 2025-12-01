"""
Violin-specific music logic and theory.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum


class ViolinPosition(Enum):
    """Standard violin positions."""
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7


@dataclass
class ViolinNote:
    """Represents a note on the violin."""
    string: str  # G, D, A, E
    position: int
    finger: int  # 0 = open, 1-4 = fingers
    pitch_offset: int  # -1 = flat, 0 = natural, 1 = sharp
    
    def __str__(self) -> str:
        offset_str = ""
        if self.pitch_offset == -1:
            offset_str = "b"
        elif self.pitch_offset == 1:
            offset_str = "#"
        
        finger_str = "open" if self.finger == 0 else f"finger {self.finger}"
        return f"{self.string} string, {self.position}st pos, {finger_str}{offset_str}"


class ViolinModel:
    """
    Model of violin fingering and note relationships.
    
    Provides utilities for understanding violin-specific
    concepts like positions, fingering patterns, and scales.
    """
    
    # Standard tuning (MIDI notes)
    STRINGS = {
        'G': 55,  # G3
        'D': 62,  # D4
        'A': 69,  # A4
        'E': 76   # E5
    }
    
    # Standard fingering patterns (semitones from open string)
    # In first position with standard (major scale) fingering
    MAJOR_FINGERING = {
        0: 0,   # Open
        1: 2,   # Whole step
        2: 4,   # Whole step
        3: 5,   # Half step (high 3)
        4: 7    # Whole step
    }
    
    # Minor fingering (low 2nd finger)
    MINOR_FINGERING = {
        0: 0,
        1: 2,
        2: 3,   # Half step (low 2)
        3: 5,
        4: 7
    }
    
    def __init__(self):
        """Initialize the violin model."""
        self.current_position = ViolinPosition.FIRST
    
    def get_note_options(
        self,
        target_midi: int
    ) -> List[ViolinNote]:
        """
        Find all possible ways to play a given MIDI note.
        
        Args:
            target_midi: The MIDI note number to find
            
        Returns:
            List of ViolinNote options
        """
        options = []
        
        for string_name, base_note in self.STRINGS.items():
            # Check positions 1-3
            for position in range(1, 4):
                pos_shift = (position - 1) * 2  # Each position = 2 semitones
                
                for finger in range(5):
                    finger_shift = self.MAJOR_FINGERING.get(finger, 0)
                    
                    for offset in [-1, 0, 1]:
                        note = base_note + pos_shift + finger_shift + offset
                        
                        if note == target_midi:
                            options.append(ViolinNote(
                                string=string_name,
                                position=position,
                                finger=finger,
                                pitch_offset=offset
                            ))
        
        return options
    
    def get_easiest_fingering(
        self,
        target_midi: int,
        preferred_string: str = None,
        preferred_position: int = 1
    ) -> ViolinNote:
        """
        Get the most practical fingering for a note.
        
        Prioritizes:
        1. Preferred string if specified
        2. Lower positions
        3. Natural (non-modified) fingerings
        
        Args:
            target_midi: MIDI note to find
            preferred_string: Preferred string (G, D, A, E)
            preferred_position: Preferred position (1-7)
            
        Returns:
            Best ViolinNote option
        """
        options = self.get_note_options(target_midi)
        
        if not options:
            return None
        
        def score(note: ViolinNote) -> Tuple[int, int, int]:
            # Lower score = better
            string_score = 0 if note.string == preferred_string else 1
            position_score = abs(note.position - preferred_position)
            offset_score = abs(note.pitch_offset)
            return (string_score, position_score, offset_score)
        
        return min(options, key=score)
    
    def get_scale(
        self,
        root: str,
        scale_type: str = "major",
        octaves: int = 2
    ) -> List[int]:
        """
        Generate a scale starting from a root note.
        
        Args:
            root: Root note name (e.g., "G", "D", "A")
            scale_type: "major" or "minor"
            octaves: Number of octaves
            
        Returns:
            List of MIDI note numbers
        """
        # Find root MIDI note
        root_midi = None
        for string, note in self.STRINGS.items():
            if string == root.upper():
                root_midi = note
                break
        
        if root_midi is None:
            root_midi = 60  # Default to middle C
        
        # Scale intervals
        if scale_type == "major":
            intervals = [0, 2, 4, 5, 7, 9, 11, 12]
        elif scale_type == "minor":
            intervals = [0, 2, 3, 5, 7, 8, 10, 12]
        else:
            intervals = [0, 2, 4, 5, 7, 9, 11, 12]
        
        # Generate scale
        scale = []
        for octave in range(octaves):
            for interval in intervals[:-1]:  # Exclude octave to avoid duplicates
                scale.append(root_midi + interval + (octave * 12))
        
        # Add final note
        scale.append(root_midi + octaves * 12)
        
        return scale
    
    def suggest_position(self, notes: List[int]) -> int:
        """
        Suggest the best position for a sequence of notes.
        
        Args:
            notes: List of MIDI notes to play
            
        Returns:
            Recommended position (1-3)
        """
        if not notes:
            return 1
        
        avg_note = sum(notes) / len(notes)
        
        # Higher notes = higher position
        if avg_note < 65:
            return 1
        elif avg_note < 75:
            return 2
        else:
            return 3
    
    def get_string_range(self, string: str, position: int = 1) -> Tuple[int, int]:
        """
        Get the playable range on a string in a given position.
        
        Args:
            string: String name (G, D, A, E)
            position: Position number
            
        Returns:
            Tuple of (lowest_note, highest_note) MIDI numbers
        """
        base = self.STRINGS.get(string.upper(), 60)
        pos_shift = (position - 1) * 2
        
        lowest = base + pos_shift
        highest = base + pos_shift + 8  # 4th finger = 8 semitones
        
        return (lowest, highest)
