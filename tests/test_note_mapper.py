"""
Tests for the NoteMapper class.
"""

import pytest
from src.music.note_mapper import NoteMapper, ViolinString, NoteInfo
from src.utils.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def mapper(config):
    """Create a NoteMapper instance."""
    return NoteMapper(config)


class TestNoteMapper:
    """Tests for NoteMapper functionality."""
    
    def test_open_strings(self, mapper):
        """Test open string MIDI values."""
        # G string open
        assert mapper.get_note(string=4, position=1, finger_count=0) == 55
        
        # D string open
        assert mapper.get_note(string=3, position=1, finger_count=0) == 62
        
        # A string open
        assert mapper.get_note(string=2, position=1, finger_count=0) == 69
        
        # E string open
        assert mapper.get_note(string=1, position=1, finger_count=0) == 76
    
    def test_finger_positions(self, mapper):
        """Test finger position calculations on A string."""
        # A string (base = 69)
        # 1st finger = +2 semitones = B (71)
        assert mapper.get_note(string=2, position=1, finger_count=1) == 71
        
        # 2nd finger = +4 semitones = C# (73)
        assert mapper.get_note(string=2, position=1, finger_count=2) == 73
        
        # 3rd finger = +6 semitones = D (75)
        assert mapper.get_note(string=2, position=1, finger_count=3) == 75
        
        # 4th finger = +8 semitones = E (77)
        assert mapper.get_note(string=2, position=1, finger_count=4) == 77
    
    def test_position_shifts(self, mapper):
        """Test position shift calculations."""
        # A string, 1st position, open = 69
        assert mapper.get_note(string=2, position=1, finger_count=0) == 69
        
        # A string, 2nd position, open = 71 (+2)
        assert mapper.get_note(string=2, position=2, finger_count=0) == 71
        
        # A string, 3rd position, open = 73 (+4)
        assert mapper.get_note(string=2, position=3, finger_count=0) == 73
    
    def test_pitch_offset(self, mapper):
        """Test pitch offset (flat/sharp)."""
        base = mapper.get_note(string=2, position=1, finger_count=1)  # B
        
        # Flat
        flat = mapper.get_note(string=2, position=1, finger_count=1, pitch_offset=-1)
        assert flat == base - 1
        
        # Sharp
        sharp = mapper.get_note(string=2, position=1, finger_count=1, pitch_offset=1)
        assert sharp == base + 1
    
    def test_combined_calculation(self, mapper):
        """Test full note calculation."""
        # E string (76), 2nd position (+2), 3rd finger (+6), natural (0)
        # = 76 + 2 + 6 + 0 = 84
        note = mapper.get_note(string=1, position=2, finger_count=3, pitch_offset=0)
        assert note == 84
    
    def test_get_note_info(self, mapper):
        """Test getting detailed note info."""
        info = mapper.get_note_info(string=2, position=1, finger_count=0)
        
        assert isinstance(info, NoteInfo)
        assert info.midi_note == 69
        assert info.string == "A"
        assert info.position == 1
        assert info.finger == 0
        assert info.note_name == "A4"
    
    def test_input_clamping(self, mapper):
        """Test that invalid inputs are clamped."""
        # String out of range
        assert mapper.get_note(string=0) == mapper.get_note(string=1)
        assert mapper.get_note(string=10) == mapper.get_note(string=4)
        
        # Position out of range
        assert mapper.get_note(string=2, position=0) == mapper.get_note(string=2, position=1)
        assert mapper.get_note(string=2, position=5) == mapper.get_note(string=2, position=3)
        
        # Finger out of range
        assert mapper.get_note(string=2, finger_count=-1) == mapper.get_note(string=2, finger_count=0)
        assert mapper.get_note(string=2, finger_count=10) == mapper.get_note(string=2, finger_count=4)
    
    def test_midi_range(self, mapper):
        """Test that output is always valid MIDI."""
        # Even with extreme values, output should be 0-127
        note = mapper.get_note(string=1, position=3, finger_count=4, pitch_offset=1)
        assert 0 <= note <= 127
    
    def test_midi_to_note_name(self, mapper):
        """Test MIDI to note name conversion."""
        assert mapper._midi_to_note_name(69) == "A4"
        assert mapper._midi_to_note_name(60) == "C4"
        assert mapper._midi_to_note_name(72) == "C5"
        assert mapper._midi_to_note_name(73) == "C#5"


class TestViolinString:
    """Tests for ViolinString enum."""
    
    def test_string_values(self):
        """Test that string MIDI values are correct."""
        assert ViolinString.G.value == 55
        assert ViolinString.D.value == 62
        assert ViolinString.A.value == 69
        assert ViolinString.E.value == 76
