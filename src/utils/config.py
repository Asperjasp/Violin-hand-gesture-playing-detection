"""
Configuration management.
"""
# Provides decorators
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import os
from dotenv import load_dotenv


@dataclass
class CameraConfig:
    """Camera configuration."""
    device_id: int = 0
    resolution: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    fps: int = 30
    flip_horizontal: bool = True


@dataclass
class DetectionConfig:
    """Hand detection configuration."""
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.5
    max_num_hands: int = 2
    model_complexity: int = 1


@dataclass
class ThresholdsConfig:
    """Gesture thresholds configuration."""
    pinch_epsilon: float = 0.05
    pinch_release_epsilon: float = 0.08
    position_zones: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "first": {"min": 0.0, "max": 0.33},
        "second": {"min": 0.33, "max": 0.66},
        "third": {"min": 0.66, "max": 1.0}
    })
    finger_extension_threshold: float = 0.6
    note_debounce_ms: int = 50
    position_debounce_ms: int = 100


@dataclass
class MIDIConfig:
    """MIDI configuration."""
    port_name: str = "Violin-Hand"
    channel: int = 0
    velocity: int = 100
    program: int = 40  # Violin in General MIDI


@dataclass
class ViolinConfig:
    """Violin-specific configuration."""
    strings: Dict[str, int] = field(default_factory=lambda: {
        "G": 55, "D": 62, "A": 69, "E": 76
    })
    positions: Dict[str, int] = field(default_factory=lambda: {
        "first": 0, "second": 2, "third": 4
    })
    fingers: Dict[int, int] = field(default_factory=lambda: {
        0: 0, 1: 2, 2: 4, 3: 6, 4: 8
    })


@dataclass
class DatabaseConfig:
    """Database configuration."""
    enabled: bool = True
    path: str = "data/performance_logs/sessions.db"
    log_interval_ms: int = 100


@dataclass
class DebugConfig:
    """Debug configuration."""
    enabled: bool = False
    show_landmarks: bool = True
    show_fps: bool = True
    show_gesture_info: bool = True
    window_name: str = "Violin Auto-Playing"


class Config:
    """
    Application configuration manager.
    
    Loads configuration from YAML files and environment variables,
    providing type-safe access to all settings.
    """
    
    def __init__(self, config_path: str = "config/default_config.yaml"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize with defaults
        self.camera = CameraConfig()
        self.detection = DetectionConfig()
        self.thresholds = ThresholdsConfig()
        self.midi = MIDIConfig()
        self.violin = ViolinConfig()
        self.database = DatabaseConfig()
        self.debug = DebugConfig()
        
        # Load from file
        self._load_from_file(config_path)
        
        # Override from environment
        self._load_from_env()
    
    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        path = Path(config_path)
        
        if not path.exists():
            print(f"Config file not found: {config_path}, using defaults")
            return
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            return
        
        # Camera
        if 'camera' in data:
            self._update_dataclass(self.camera, data['camera'])
        
        # Detection
        if 'detection' in data:
            self._update_dataclass(self.detection, data['detection'])
        
        # Thresholds
        if 'thresholds' in data:
            self._update_dataclass(self.thresholds, data['thresholds'])
        
        # MIDI
        if 'midi' in data:
            self._update_dataclass(self.midi, data['midi'])
        
        # Violin
        if 'violin' in data:
            self._update_dataclass(self.violin, data['violin'])
        
        # Database
        if 'database' in data:
            self._update_dataclass(self.database, data['database'])
        
        # Debug
        if 'debug' in data:
            self._update_dataclass(self.debug, data['debug'])
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Camera
        if os.getenv('CAMERA_DEVICE_ID'):
            self.camera.device_id = int(os.getenv('CAMERA_DEVICE_ID'))
        
        # MIDI
        if os.getenv('MIDI_PORT_NAME'):
            self.midi.port_name = os.getenv('MIDI_PORT_NAME')
        if os.getenv('MIDI_CHANNEL'):
            self.midi.channel = int(os.getenv('MIDI_CHANNEL'))
        if os.getenv('MIDI_VELOCITY'):
            self.midi.velocity = int(os.getenv('MIDI_VELOCITY'))
        
        # Database
        if os.getenv('DATABASE_PATH'):
            self.database.path = os.getenv('DATABASE_PATH')
        if os.getenv('DATABASE_ENABLED'):
            self.database.enabled = os.getenv('DATABASE_ENABLED').lower() == 'true'
        
        # Debug
        if os.getenv('DEBUG_MODE'):
            self.debug.enabled = os.getenv('DEBUG_MODE').lower() == 'true'
    
    def _update_dataclass(self, obj: Any, data: Dict) -> None:
        """Update dataclass fields from dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def save(self, path: str) -> None:
        """
        Save current configuration to file.
        
        Args:
            path: Output file path
        """
        data = {
            'camera': {
                'device_id': self.camera.device_id,
                'resolution': self.camera.resolution,
                'fps': self.camera.fps,
                'flip_horizontal': self.camera.flip_horizontal
            },
            'detection': {
                'min_detection_confidence': self.detection.min_detection_confidence,
                'min_tracking_confidence': self.detection.min_tracking_confidence,
                'max_num_hands': self.detection.max_num_hands,
                'model_complexity': self.detection.model_complexity
            },
            'thresholds': {
                'pinch_epsilon': self.thresholds.pinch_epsilon,
                'pinch_release_epsilon': self.thresholds.pinch_release_epsilon,
                'position_zones': self.thresholds.position_zones,
                'finger_extension_threshold': self.thresholds.finger_extension_threshold,
                'note_debounce_ms': self.thresholds.note_debounce_ms,
                'position_debounce_ms': self.thresholds.position_debounce_ms
            },
            'midi': {
                'port_name': self.midi.port_name,
                'channel': self.midi.channel,
                'velocity': self.midi.velocity,
                'program': self.midi.program
            },
            'violin': {
                'strings': self.violin.strings,
                'positions': self.violin.positions,
                'fingers': self.violin.fingers
            },
            'database': {
                'enabled': self.database.enabled,
                'path': self.database.path,
                'log_interval_ms': self.database.log_interval_ms
            },
            'debug': {
                'enabled': self.debug.enabled,
                'show_landmarks': self.debug.show_landmarks,
                'show_fps': self.debug.show_fps,
                'show_gesture_info': self.debug.show_gesture_info,
                'window_name': self.debug.window_name
            }
        }
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
