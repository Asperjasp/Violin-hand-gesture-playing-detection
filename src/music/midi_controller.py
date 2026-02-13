"""
MIDI controller for sending note messages.
"""

from typing import Optional
import rtmidi
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF, PROGRAM_CHANGE

from src.utils.config import Config

class MIDIController:
    """
    Handles MIDI output for the application.
    
    Sends note on/off messages to a virtual MIDI port
    that can be connected to any DAW or synthesizer.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the MIDI controller.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.channel = config.midi.channel
        self.velocity = config.midi.velocity
        self.port_name = config.midi.port_name
        
        # Initialize MIDI output Object
        self.midi_out = rtmidi.MidiOut()
        self._setup_port()
        
        # Set instrument (violin = 40 in General MIDI)
        self._set_program(config.midi.program)
        
        # Track active notes
        self.active_notes: set = set()
    
    def _setup_port(self) -> None:
        """Set up the MIDI output port."""
        available_ports = self.midi_out.get_ports()
        
        # Try to find the specified port
        port_index = None
        for i, port in enumerate(available_ports):
            if self.port_name in port:
                port_index = i
                break
        
        if port_index is not None:
            self.midi_out.open_port(port_index)
            print(f"MIDI: Connected to port '{available_ports[port_index]}'")
        else:
            # Create a virtual port
            self.midi_out.open_virtual_port(self.port_name)
            print(f"MIDI: Created virtual port '{self.port_name}'")
    
    def _set_program(self, program: int) -> None:
        """
        Set the MIDI program (instrument).
        
        Args:
            program: MIDI program number (0-127)
        """
        message = [PROGRAM_CHANGE | self.channel, program]
        self.midi_out.send_message(message)
    
    def note_on(self, note: int, velocity: Optional[int] = None) -> None:
        """
        Send a Note On message.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127), uses default if not specified
        """
        if note < 0 or note > 127:
            return
        
        vel = velocity if velocity is not None else self.velocity
        message = [NOTE_ON | self.channel, note, vel]
        self.midi_out.send_message(message)
        self.active_notes.add(note)
    
    def note_off(self, note: int) -> None:
        """
        Send a Note Off message.
        
        Args:
            note: MIDI note number (0-127)
        """
        if note < 0 or note > 127:
            return
        
        message = [NOTE_OFF | self.channel, note, 0]
        self.midi_out.send_message(message)
        self.active_notes.discard(note)
    
    def all_notes_off(self) -> None:
        """Turn off all active notes."""
        for note in list(self.active_notes):
            self.note_off(note)
        self.active_notes.clear()
    
    def set_velocity(self, velocity: int) -> None:
        """
        Set the default velocity for subsequent notes.
        
        Args:
            velocity: Note velocity (0-127)
        """
        self.velocity = max(0, min(127, velocity))
    
    def get_available_ports(self) -> list:
        """Get list of available MIDI output ports."""
        return self.midi_out.get_ports()
    
    def close(self) -> None:
        """Close the MIDI port and release resources."""
        self.all_notes_off()
        self.midi_out.close_port()
        del self.midi_out
