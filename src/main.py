"""
Main entry point for the Violin Auto-Playing application.
"""

import argparse
import sys
from pathlib import Path

import cv2

from src.utils.config import Config
from src.vision.hand_detector import HandDetector
from src.vision.gesture_recognizer import GestureRecognizer
from src.music.midi_controller import MIDIController
from src.music.note_mapper import NoteMapper
from src.database.logger import PerformanceLogger


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Violin Auto-Playing with Hand Gestures",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/default_config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run position calibration before starting"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug visualization"
    )
    
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Disable database logging"
    )
    
    parser.add_argument(
        "--midi-port",
        type=str,
        default=None,
        help="Specify MIDI output port name"
    )
    
    return parser.parse_args()


class ViolinApp:
    """Main application class for Violin Auto-Playing."""
    
    def __init__(self, config: Config, debug: bool = False, use_db: bool = True):
        """
        Initialize the application.
        
        Args:
            config: Application configuration
            debug: Enable debug mode
            use_db: Enable database logging
        """
        self.config = config
        self.debug = debug
        self.running = False
        
        # Initialize components
        self.hand_detector = HandDetector(config)
        self.gesture_recognizer = GestureRecognizer(config)
        self.note_mapper = NoteMapper(config)
        self.midi_controller = MIDIController(config)
        
        # Database logger (optional)
        self.logger = PerformanceLogger(config) if use_db else None
        
        # State tracking
        self.current_note = None
        self.is_playing = False
    
    def run(self) -> None:
        """Main application loop."""
        cap = cv2.VideoCapture(self.config.camera.device_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera.resolution["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera.resolution["height"])
        cap.set(cv2.CAP_PROP_FPS, self.config.camera.fps)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)
        
        self.running = True
        print("Violin Auto-Playing started. Press 'q' to quit.")
        
        if self.logger:
            self.logger.start_session()
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                # Flip frame for mirror effect
                if self.config.camera.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                
                # Detect hands
                hands = self.hand_detector.detect(frame)
                
                # Process gestures
                if hands:
                    gestures = self.gesture_recognizer.recognize(hands)
                    self._process_gestures(gestures)
                else:
                    self._stop_note()
                
                # Debug visualization
                if self.debug:
                    frame = self._draw_debug_info(frame, hands)
                    cv2.imshow(self.config.debug.window_name, frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
        
        finally:
            self._cleanup(cap)
    
    def _process_gestures(self, gestures: dict) -> None:
        """Process recognized gestures and generate MIDI output."""
        # Extract gesture information
        bow_active = gestures.get("bow_active", False)
        string_selected = gestures.get("string", None)
        position = gestures.get("position", 1)
        finger_count = gestures.get("finger_count", 0)
        pitch_offset = gestures.get("pitch_offset", 0)
        
        if bow_active and string_selected:
            # Calculate MIDI note
            note = self.note_mapper.get_note(
                string=string_selected,
                position=position,
                finger_count=finger_count,
                pitch_offset=pitch_offset
            )
            
            if note != self.current_note:
                # Stop previous note
                self._stop_note()
                # Play new note
                self._play_note(note, gestures)
        else:
            self._stop_note()
    
    def _play_note(self, note: int, gestures: dict) -> None:
        """Play a MIDI note."""
        if not self.is_playing or note != self.current_note:
            self.midi_controller.note_on(note)
            self.current_note = note
            self.is_playing = True
            
            # Log to database
            if self.logger:
                self.logger.log_note(note, gestures)
    
    def _stop_note(self) -> None:
        """Stop the current note."""
        if self.is_playing and self.current_note is not None:
            self.midi_controller.note_off(self.current_note)
            self.current_note = None
            self.is_playing = False
    
    def _draw_debug_info(self, frame, hands) -> any:
        """Draw debug information on the frame."""
        # Draw hand landmarks
        if hands:
            frame = self.hand_detector.draw_landmarks(frame, hands)
        
        # Draw FPS and other info
        if self.config.debug.show_fps:
            cv2.putText(
                frame, f"Note: {self.current_note}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )
        
        return frame
    
    def _cleanup(self, cap) -> None:
        """Clean up resources."""
        self._stop_note()
        cap.release()
        cv2.destroyAllWindows()
        self.midi_controller.close()
        
        if self.logger:
            self.logger.end_session()
        
        print("Application closed.")


def main():
    """Application entry point."""
    args = parse_arguments()
    
    # Load configuration
    config = Config(args.config)
    
    # Override with command line arguments
    if args.midi_port:
        config.midi.port_name = args.midi_port
    
    if args.debug:
        config.debug.enabled = True
    
    # Run calibration if requested
    if args.calibrate:
        from src.vision.calibration import run_calibration
        run_calibration(config)
    
    # Start application
    app = ViolinApp(
        config=config,
        debug=args.debug or config.debug.enabled,
        use_db=not args.no_db and config.database.enabled
    )
    
    app.run()


if __name__ == "__main__":
    main()
