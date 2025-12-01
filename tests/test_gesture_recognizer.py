"""
Tests for the GestureRecognizer class.
"""

import pytest
from src.vision.gesture_recognizer import GestureRecognizer, GestureState
from src.vision.hand_detector import HandLandmarks
from src.utils.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def recognizer(config):
    """Create a GestureRecognizer instance."""
    return GestureRecognizer(config)


def create_mock_hand(
    handedness: str = "Right",
    thumb_tip: tuple = (0.5, 0.5, 0.0),
    index_tip: tuple = (0.5, 0.3, 0.0),
    extended_fingers: int = 2
) -> HandLandmarks:
    """
    Create a mock hand for testing.
    
    Args:
        handedness: "Left" or "Right"
        thumb_tip: Thumb tip position
        index_tip: Index tip position
        extended_fingers: Number of fingers to simulate as extended
        
    Returns:
        Mock HandLandmarks object
    """
    # Create 21 landmarks (standard MediaPipe hand)
    landmarks = [(0.5, 0.5, 0.0)] * 21
    
    # Set specific landmarks
    landmarks[4] = thumb_tip  # Thumb tip
    landmarks[8] = index_tip  # Index tip
    
    # Set finger positions based on extended_fingers
    # PIP joints (for extension detection)
    pip_y = 0.5
    
    for i, (tip_idx, pip_idx) in enumerate([(8, 6), (12, 10), (16, 14), (20, 18)]):
        if i < extended_fingers:
            # Extended: tip above PIP (lower Y)
            landmarks[tip_idx] = (0.5, pip_y - 0.1, 0.0)
            landmarks[pip_idx] = (0.5, pip_y, 0.0)
        else:
            # Curled: tip below PIP (higher Y)
            landmarks[tip_idx] = (0.5, pip_y + 0.1, 0.0)
            landmarks[pip_idx] = (0.5, pip_y, 0.0)
    
    return HandLandmarks(
        landmarks=landmarks,
        handedness=handedness,
        confidence=0.95
    )


class TestGestureRecognizer:
    """Tests for GestureRecognizer functionality."""
    
    def test_initial_state(self, recognizer):
        """Test initial gesture state."""
        state = recognizer.get_state()
        
        assert isinstance(state, GestureState)
        assert state.bow_active is False
        assert state.string_selected is None
        assert state.position == 1
        assert state.finger_count == 0
    
    def test_pinch_detection(self, recognizer):
        """Test bow trigger (pinch) detection."""
        # Create hand with pinch (thumb and index close together)
        pinched_hand = create_mock_hand(
            handedness="Right",
            thumb_tip=(0.5, 0.5, 0.0),
            index_tip=(0.52, 0.52, 0.0),  # Very close = pinch
            extended_fingers=2
        )
        
        gestures = recognizer.recognize([pinched_hand])
        assert gestures["bow_active"] is True
    
    def test_no_pinch(self, recognizer):
        """Test bow off when no pinch."""
        # Create hand without pinch (thumb and index far apart)
        open_hand = create_mock_hand(
            handedness="Right",
            thumb_tip=(0.3, 0.5, 0.0),
            index_tip=(0.7, 0.3, 0.0),  # Far apart = no pinch
            extended_fingers=2
        )
        
        gestures = recognizer.recognize([open_hand])
        assert gestures["bow_active"] is False
    
    def test_string_selection(self, recognizer):
        """Test string selection from extended fingers."""
        for num_fingers in range(1, 5):
            hand = create_mock_hand(
                handedness="Right",
                extended_fingers=num_fingers
            )
            
            gestures = recognizer.recognize([hand])
            assert gestures["string"] == num_fingers
    
    def test_position_zones(self, recognizer):
        """Test position detection from thumb Y coordinate."""
        # First position (low Y)
        hand_pos1 = create_mock_hand(
            handedness="Left",
            thumb_tip=(0.5, 0.2, 0.0)  # Low Y = first position
        )
        gestures = recognizer.recognize([hand_pos1])
        assert gestures["position"] == 1
        
        # Second position (mid Y)
        hand_pos2 = create_mock_hand(
            handedness="Left",
            thumb_tip=(0.5, 0.5, 0.0)  # Mid Y = second position
        )
        gestures = recognizer.recognize([hand_pos2])
        assert gestures["position"] == 2
        
        # Third position (high Y)
        hand_pos3 = create_mock_hand(
            handedness="Left",
            thumb_tip=(0.5, 0.8, 0.0)  # High Y = third position
        )
        gestures = recognizer.recognize([hand_pos3])
        assert gestures["position"] == 3
    
    def test_dual_hand_recognition(self, recognizer):
        """Test recognition with both hands."""
        right_hand = create_mock_hand(
            handedness="Right",
            thumb_tip=(0.5, 0.5, 0.0),
            index_tip=(0.52, 0.52, 0.0),  # Pinch
            extended_fingers=3  # D string
        )
        
        left_hand = create_mock_hand(
            handedness="Left",
            thumb_tip=(0.5, 0.5, 0.0)  # 2nd position
        )
        
        gestures = recognizer.recognize([right_hand, left_hand])
        
        assert gestures["bow_active"] is True
        assert gestures["string"] == 3  # D string
        assert gestures["position"] == 2  # 2nd position
    
    def test_no_hands(self, recognizer):
        """Test behavior with no hands detected."""
        gestures = recognizer.recognize([])
        
        assert gestures["bow_active"] is False
        assert gestures["string"] is None


class TestPinchDistance:
    """Tests for pinch distance calculation."""
    
    def test_zero_distance(self, recognizer):
        """Test distance when fingers overlap."""
        hand = create_mock_hand(
            thumb_tip=(0.5, 0.5, 0.0),
            index_tip=(0.5, 0.5, 0.0)
        )
        
        distance = recognizer._calculate_pinch_distance(hand)
        assert distance == 0.0
    
    def test_known_distance(self, recognizer):
        """Test distance calculation."""
        hand = create_mock_hand(
            thumb_tip=(0.0, 0.0, 0.0),
            index_tip=(0.3, 0.4, 0.0)
        )
        
        distance = recognizer._calculate_pinch_distance(hand)
        assert abs(distance - 0.5) < 0.01  # 3-4-5 triangle
