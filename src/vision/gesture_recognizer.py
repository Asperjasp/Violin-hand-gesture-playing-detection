"""
Gesture recognition from hand landmarks.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

from src.utils.config import Config
from src.vision.hand_detector import HandLandmarks


@dataclass
class GestureState:
    """Current gesture state for both hands."""
    # Right hand (bow control)
    bow_active: bool = False
    string_selected: Optional[int] = None  # 1-4 for E, A, D, G
    
    # Left hand (pitch control)
    position: int = 1  # 1, 2, or 3
    finger_count: int = 0  # 0-4
    pitch_offset: int = 0  # -1, 0, or 1


class GestureRecognizer:
    """
    Interprets hand landmarks as musical gestures.
    
    Right hand controls:
        - String selection (extended fingers)
        - Bow trigger (pinch gesture)
    
    Left hand controls:
        - Position (thumb Y coordinate)
        - Finger count (pressed fingers)
        - Pitch displacement (finger orientation)
    """
    
    # Finger tip and pip landmark indices
    FINGER_TIPS = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    FINGER_PIPS = [6, 10, 14, 18]  # PIP joints for comparison
    FINGER_MCPS = [5, 9, 13, 17]   # MCP joints
    
    def __init__(self, config: Config):
        """
        Initialize the gesture recognizer.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.state = GestureState()
        
        # Thresholds
        self.pinch_threshold = config.thresholds.pinch_epsilon
        self.pinch_release = config.thresholds.pinch_release_epsilon
        self.finger_threshold = config.thresholds.finger_extension_threshold
        
        # Position zones
        self.position_zones = config.thresholds.position_zones
    
    def recognize(self, hands: List[HandLandmarks]) -> Dict:
        """
        Recognize gestures from detected hands.
        
        Args:
            hands: List of detected hand landmarks
            
        Returns:
            Dictionary with gesture information
        """
        right_hand = None
        left_hand = None
        
        # Separate hands
        for hand in hands:
            if hand.handedness == "Right":
                right_hand = hand
            elif hand.handedness == "Left":
                left_hand = hand
        
        # Process right hand (bow control)
        if right_hand:
            self._process_right_hand(right_hand)
        else:
            self.state.bow_active = False
            self.state.string_selected = None
        
        # Process left hand (pitch control)
        if left_hand:
            self._process_left_hand(left_hand)
        
        return {
            "bow_active": self.state.bow_active,
            "string": self.state.string_selected,
            "position": self.state.position,
            "finger_count": self.state.finger_count,
            "pitch_offset": self.state.pitch_offset
        }
    
    def _process_right_hand(self, hand: HandLandmarks) -> None:
        """Process right hand for bow control."""
        # Check pinch (bow trigger)
        pinch_distance = self._calculate_pinch_distance(hand)
        
        if pinch_distance < self.pinch_threshold:
            self.state.bow_active = True
        elif pinch_distance > self.pinch_release:
            self.state.bow_active = False
        
        # Count extended fingers for string selection
        extended = self._count_extended_fingers(hand)
        if 1 <= extended <= 4:
            self.state.string_selected = extended
    
    def _process_left_hand(self, hand: HandLandmarks) -> None:
        """Process left hand for pitch control."""
        # Detect position from thumb Y coordinate
        thumb_y = hand.thumb_tip[1]  # Normalized Y
        self.state.position = self._get_position_from_y(thumb_y)
        
        # Count pressed fingers
        self.state.finger_count = self._count_pressed_fingers(hand)
        
        # Detect pitch displacement from finger orientation
        self.state.pitch_offset = self._get_pitch_offset(hand)
    
    def _calculate_pinch_distance(self, hand: HandLandmarks) -> float:
        """
        Calculate distance between thumb tip and index tip.
        
        Args:
            hand: Hand landmarks
            
        Returns:
            Euclidean distance (normalized)
        """
        thumb = hand.thumb_tip
        index = hand.index_tip
        
        distance = math.sqrt(
            (thumb[0] - index[0]) ** 2 +
            (thumb[1] - index[1]) ** 2 +
            (thumb[2] - index[2]) ** 2
        )
        
        return distance
    
    def _count_extended_fingers(self, hand: HandLandmarks) -> int:
        """
        Count number of extended fingers (excluding thumb).
        
        A finger is extended if its tip is above (lower Y) its PIP joint.
        
        Args:
            hand: Hand landmarks
            
        Returns:
            Number of extended fingers (0-4)
        """
        count = 0
        
        for tip_idx, pip_idx in zip(self.FINGER_TIPS, self.FINGER_PIPS):
            tip = hand.landmarks[tip_idx]
            pip = hand.landmarks[pip_idx]
            
            # Finger is extended if tip is above PIP (lower Y value)
            if tip[1] < pip[1]:
                count += 1
        
        return count
    
    def _count_pressed_fingers(self, hand: HandLandmarks) -> int:
        """
        Count number of pressed/curled fingers for left hand.
        
        For violin, pressed means the finger is curled down.
        
        Args:
            hand: Hand landmarks
            
        Returns:
            Number of pressed fingers (0-4)
        """
        count = 0
        
        for tip_idx, mcp_idx in zip(self.FINGER_TIPS, self.FINGER_MCPS):
            tip = hand.landmarks[tip_idx]
            mcp = hand.landmarks[mcp_idx]
            
            # Finger is pressed if tip is below MCP (higher Y value)
            if tip[1] > mcp[1]:
                count += 1
        
        return count
    
    def _get_position_from_y(self, y: float) -> int:
        """
        Determine violin position from normalized Y coordinate.
        
        Args:
            y: Normalized Y coordinate (0-1)
            
        Returns:
            Position number (1, 2, or 3)
        """
        zones = self.position_zones
        
        if y < zones["first"]["max"]:
            return 1
        elif y < zones["second"]["max"]:
            return 2
        else:
            return 3
    
    def _get_pitch_offset(self, hand: HandLandmarks) -> int:
        """
        Determine pitch offset from finger orientation.
        
        Uses the Z-axis (depth) difference between index tip and MCP
        to determine if fingers are tilted up (flat) or down (sharp).
        
        Args:
            hand: Hand landmarks
            
        Returns:
            -1 (flat), 0 (natural), or 1 (sharp)
        """
        index_tip = hand.landmarks[8]
        index_mcp = hand.landmarks[5]
        
        z_diff = index_tip[2] - index_mcp[2]
        
        # Threshold for detecting tilt
        tilt_threshold = 0.02
        
        if z_diff > tilt_threshold:
            return -1  # Flat
        elif z_diff < -tilt_threshold:
            return 1   # Sharp
        else:
            return 0   # Natural
    
    def get_state(self) -> GestureState:
        """Get the current gesture state."""
        return self.state
