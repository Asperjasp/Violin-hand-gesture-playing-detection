"""
Main entry point for the Violin Auto-Playing application.

Ejecutar:
    python -m src.main --debug          # Con visualización
    python -m src.main --no-midi        # Sin MIDI (solo visual)
    python -m src.main --calibrate      # Calibrar posiciones
"""

import argparse  # User friendly CLI ( Command Line Interface )
import sys
import time
from pathlib import Path

import cv2

from src.utils.config import Config
from src.utils.helpers import FPSCounter
from src.vision.hand_detector import HandDetector
from src.vision.gesture_recognizer import GestureRecognizer
from src.vision.visualizer import ViolinVisualizer, HandVisualizerOverlay
from src.music.midi_controller import MIDIController
from src.music.note_mapper import NoteMapper
from src.music.audio_player import AudioPlayer
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
    
    parser.add_argument(
        "--no-midi",
        action="store_true",
        help="Disable MIDI output (visual only mode)"
    )
    
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Enable direct audio output (simple sine synth)"
    )
    
    parser.add_argument(
        "--realistic",
        action="store_true",
        help="Enable realistic violin sound via FluidSynth (recommended)"
    )
    
    parser.add_argument(
        "--no-visualizer",
        action="store_true",
        help="Disable violin visualizer overlay"
    )
    
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera device index (default: 0)"
    )
    
    parser.add_argument(
        "--video",
        type=str,
        default=None,
        help="Use video file instead of camera (for testing)"
    )
    
    return parser.parse_args()


class ViolinApp:
    """Main application class for Violin Auto-Playing."""
    
    def __init__(
        self,
        config: Config,
        debug: bool = False,
        use_db: bool = True,
        use_midi: bool = True,
        use_audio: bool = False,
        use_realistic: bool = False,
        use_visualizer: bool = True,
        camera_index: int = 0,
        video_source: str | None = None
    ):
        """
        Initialize the application.
        
        Args:
            config: Application configuration
            debug: Enable debug mode
            use_db: Enable database logging
            use_midi: Enable MIDI output
            use_audio: Enable direct audio output (pygame sine synth)
            use_realistic: Enable realistic audio via FluidSynth
            use_visualizer: Enable violin visualizer
            camera_index: Camera device index
            video_source: Path to video file (overrides camera)
        """
        self.config = config
        self.debug = debug
        self.running = False
        self.use_midi = use_midi
        self.use_audio = use_audio
        self.use_realistic = use_realistic
        self.use_visualizer = use_visualizer
        self.camera_index = camera_index
        self.video_source = video_source
        
        # Initialize core components
        self.hand_detector = HandDetector(config)
        self.gesture_recognizer = GestureRecognizer(config)
        self.note_mapper = NoteMapper(config)
        
        # MIDI controller (optional)
        if use_midi:
            try:
                self.midi_controller = MIDIController(config)
            except Exception as e:
                print(f"⚠️ MIDI disabled: {e}")
                self.midi_controller = None
                self.use_midi = False
        else:
            self.midi_controller = None
        
        # Audio player (optional - simple sine synth)
        if use_audio and not use_realistic:
            self.audio_player = AudioPlayer()
        else:
            self.audio_player = None
        
        # Realistic audio player (FluidSynth - sounds like real violin)
        if use_realistic:
            from src.music.fluidsynth_player import FluidSynthPlayer
            self.realistic_player = FluidSynthPlayer(instrument='violin', debug=debug)
        else:
            self.realistic_player = None
        
        # Visualizers
        if use_visualizer:
            self.violin_visualizer = ViolinVisualizer(
                width=300,
                height=400,
                position=(20, 20)
            )
            self.hand_overlay = HandVisualizerOverlay()
        else:
            self.violin_visualizer = None
            self.hand_overlay = None
        
        # Database logger (optional)
        self.logger = PerformanceLogger(config) if use_db else None
        
        # FPS counter
        self.fps_counter = FPSCounter()
        
        # State tracking
        self.current_note = None
        self.current_note_info = None
        self.is_playing = False
        self.last_gestures = {}
        
        # Debouncing - prevent rapid note changes
        self.last_note_change_time = 0
        self.note_debounce_ms = config.thresholds.note_debounce_ms
        self.pending_note = None
    def run(self) -> None:
        """Main application loop."""
        # Determine video source
        if self.video_source:
            source = self.video_source
            print(f"📹 Using video file: {source}")
        else:
            source = self.camera_index
            print(f"📷 Using camera index: {source}")
        
        cap = cv2.VideoCapture(source)
        
        # Only set camera properties if using camera (not video file)
        if not self.video_source:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera.resolution["width"])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera.resolution["height"])
            cap.set(cv2.CAP_PROP_FPS, self.config.camera.fps)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open video source: {source}")
            if not self.video_source:
                print("\n💡 Tips:")
                print("   - En WSL: La cámara de Windows no está disponible directamente")
                print("   - Prueba ejecutar en Windows: py -m src.main --debug")
                print("   - O usa un video: python -m src.main --video test.mp4")
                print("   - Prueba otra cámara: python -m src.main --camera 1")
            sys.exit(1)
        
        self.running = True
        print("Violin Auto-Playing started. Press 'q' to quit.")
        
        if self.logger:
            self.logger.start_session()
        
        print("\n🎻 Controles:")
        print("   q - Salir")
        print("   v - Toggle visualizador")
        print("   d - Toggle debug landmarks")
        print("   r - Reiniciar sesión\n")
        
        frame_count = 0
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                frame_count += 1
                if frame_count == 1:
                    print(f"📷 First frame read: {frame.shape}")
                elif frame_count % 100 == 0:
                    print(f"📷 Frame {frame_count}...")
                # Flip frame for mirror effect
                if self.config.camera.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                
                # Detect hands
                hands = self.hand_detector.detect(frame)
                
                # Process gestures
                if hands:
                    gestures = self.gesture_recognizer.recognize(hands)
                    self.last_gestures = gestures
                    self._process_gestures(gestures)
                else:
                    self.last_gestures = {}
                    self._stop_note()
                
                # === VISUALIZACIÓN ===
                
                # 1. Dibujar landmarks de manos (debug)
                if self.debug and hands:
                    frame = self.hand_detector.draw_landmarks(frame, hands)
                
                # 2. Dibujar overlay de información de manos
                if self.hand_overlay and hands:
                    frame = self.hand_overlay.render(frame, hands, self.last_gestures)
                
                # 3. Dibujar visualizador del violín
                if self.violin_visualizer:
                    self.violin_visualizer.update_state(
                        self.last_gestures,
                        self.current_note_info
                    )
                    frame = self.violin_visualizer.render(frame)
                
                # 4. Dibujar FPS y estado
                frame = self._draw_status_bar(frame)
                
                # Mostrar frame
                cv2.imshow(self.config.debug.window_name, frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == ord('v'):
                    # Toggle visualizer
                    if self.violin_visualizer:
                        self.use_visualizer = not self.use_visualizer
                        print(f"Visualizer: {'ON' if self.use_visualizer else 'OFF'}")
                elif key == ord('d'):
                    # Toggle debug
                    self.debug = not self.debug
                    print(f"Debug landmarks: {'ON' if self.debug else 'OFF'}")
        
        finally:
            self._cleanup(cap)
    
    def _process_gestures(self, gestures: dict) -> None:
        """Process recognized gestures and generate MIDI output."""
        import time as time_module
        
        # Extract gesture information
        bow_active = gestures.get("bow_active", False)
        string_selected = gestures.get("string", None)
        position = gestures.get("position", 1)
        finger_count = gestures.get("finger_count", 0)
        pitch_offset = gestures.get("pitch_offset", 0)
        
        current_time_ms = time_module.time() * 1000
        
        if bow_active and string_selected:
            # Calculate MIDI note
            note = self.note_mapper.get_note(
                string=string_selected,
                position=position,
                finger_count=finger_count,
                pitch_offset=pitch_offset
            )
            
            # Get note info for visualizer
            self.current_note_info = self.note_mapper.get_note_info(
                string=string_selected,
                position=position,
                finger_count=finger_count,
                pitch_offset=pitch_offset
            )
            
            # Debounce: only change note if enough time has passed
            if note != self.current_note:
                time_since_last_change = current_time_ms - self.last_note_change_time
                
                if time_since_last_change >= self.note_debounce_ms:
                    # Enough time passed, change note
                    self._stop_note()
                    self._play_note(note, gestures)
                    self.last_note_change_time = current_time_ms
                # else: ignore rapid changes (debounce)
        else:
            self._stop_note()
    
    def _play_note(self, note: int, gestures: dict) -> None:
        """Play a MIDI note."""
        if not self.is_playing or note != self.current_note:
            if self.use_midi and self.midi_controller:
                self.midi_controller.note_on(note)
            if self.use_audio and self.audio_player:
                self.audio_player.note_on(note)
            if self.use_realistic and self.realistic_player:
                self.realistic_player.note_on(note)
            self.current_note = note
            self.is_playing = True
            
            # Log to database
            if self.logger:
                self.logger.log_note(note, gestures)
    
    def _stop_note(self) -> None:
        """Stop the current note."""
        if self.is_playing and self.current_note is not None:
            if self.use_midi and self.midi_controller:
                self.midi_controller.note_off(self.current_note)
            if self.use_audio and self.audio_player:
                self.audio_player.note_off(self.current_note)
            if self.use_realistic and self.realistic_player:
                self.realistic_player.note_off(self.current_note)
            self.current_note = None
            self.current_note_info = None
            self.is_playing = False
    
    def _draw_status_bar(self, frame):
        """Draw status bar at the bottom of the frame."""
        h, w = frame.shape[:2]
        
        # FPS
        fps = self.fps_counter.tick()
        
        # Status bar background
        cv2.rectangle(frame, (0, h - 35), (w, h), (30, 30, 30), -1)
        
        # FPS
        cv2.putText(
            frame, f"FPS: {fps:.1f}",
            (10, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (0, 255, 0), 1
        )
        
        # Current note
        note_text = f"Note: {self.current_note_info.note_name if self.current_note_info else '---'}"
        cv2.putText(
            frame, note_text,
            (120, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (0, 255, 255) if self.is_playing else (128, 128, 128), 1
        )
        
        # MIDI status
        midi_text = "MIDI: ON" if self.use_midi else "MIDI: OFF"
        midi_color = (0, 255, 0) if self.use_midi else (0, 0, 255)
        cv2.putText(
            frame, midi_text,
            (280, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            midi_color, 1
        )
        
        # Controls hint
        cv2.putText(
            frame, "Q:Exit | V:Visualizer | D:Debug",
            (w - 280, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
            (150, 150, 150), 1
        )
        
        return frame
    
    def _draw_debug_info(self, frame, hands):
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
        
        if self.midi_controller:
            self.midi_controller.close()
        
        if self.audio_player:
            self.audio_player.close()
        
        if self.realistic_player:
            self.realistic_player.close()
        
        if self.logger:
            self.logger.end_session()
        
        print("\n✅ Application closed.")


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
    
    print("\n" + "🎻"*20)
    print("   VIOLIN AUTO-PLAYING")
    print("🎻"*20 + "\n")
    
    # Start application
    app = ViolinApp(
        config=config,
        debug=args.debug or config.debug.enabled,
        use_db=not args.no_db and config.database.enabled,
        use_midi=not args.no_midi,
        use_audio=args.audio,
        use_realistic=args.realistic,
        use_visualizer=not args.no_visualizer,
        camera_index=args.camera,
        video_source=args.video
    )
    
    app.run()


if __name__ == "__main__":
    main()
