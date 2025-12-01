"""
Hand detection using MediaPipe.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import cv2
import mediapipe as mp

from src.utils.config import Config


@dataclass
class HandLandmarks:
    """Container for hand landmark data."""
    landmarks: List[Tuple[float, float, float]]  # (x, y, z) normalized coordinates
    handedness: str  # "Left" or "Right"
    confidence: float
    
    def get_landmark(self, index: int) -> Tuple[float, float, float]:
        """Get a specific landmark by index."""
        return self.landmarks[index]
    
    @property
    def wrist(self) -> Tuple[float, float, float]:
        return self.landmarks[0]
    
    @property
    def thumb_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[4]
    
    @property
    def index_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[8]
    
    @property
    def middle_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[12]
    
    @property
    def ring_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[16]
    
    @property
    def pinky_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[20]


class HandDetector:
    """
    MediaPipe-based hand detector.
    
    Detects and tracks hands in video frames, providing
    normalized landmark coordinates for gesture recognition.
    """
    
    # MediaPipe landmark indices
    LANDMARK_NAMES = {
        0: "WRIST",
        1: "THUMB_CMC", 2: "THUMB_MCP", 3: "THUMB_IP", 4: "THUMB_TIP",
        5: "INDEX_MCP", 6: "INDEX_PIP", 7: "INDEX_DIP", 8: "INDEX_TIP",
        9: "MIDDLE_MCP", 10: "MIDDLE_PIP", 11: "MIDDLE_DIP", 12: "MIDDLE_TIP",
        13: "RING_MCP", 14: "RING_PIP", 15: "RING_DIP", 16: "RING_TIP",
        17: "PINKY_MCP", 18: "PINKY_PIP", 19: "PINKY_DIP", 20: "PINKY_TIP"
    }
    
    def __init__(self, config: Config):
        """
        Initialize the hand detector.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.detection.max_num_hands,
            min_detection_confidence=config.detection.min_detection_confidence,
            min_tracking_confidence=config.detection.min_tracking_confidence,
            model_complexity=config.detection.model_complexity
        )
    
    def detect(self, frame: np.ndarray) -> List[HandLandmarks]:
        """
        Detect hands in a frame.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            List of HandLandmarks for each detected hand
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.hands.process(rgb_frame)
        
        detected_hands = []
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness_info in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                # Extract landmarks as list of tuples
                landmarks = [
                    (lm.x, lm.y, lm.z)
                    for lm in hand_landmarks.landmark
                ]
                
                # Get handedness
                handedness = handedness_info.classification[0].label
                confidence = handedness_info.classification[0].score
                
                detected_hands.append(HandLandmarks(
                    landmarks=landmarks,
                    handedness=handedness,
                    confidence=confidence
                ))
        
        return detected_hands
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        hands: List[HandLandmarks]
    ) -> np.ndarray:
        """
        Draw hand landmarks on a frame.
        
        Args:
            frame: BGR image
            hands: List of detected hands
            
        Returns:
            Frame with landmarks drawn
        """
        h, w, _ = frame.shape
        
        for hand in hands:
            # Draw connections
            for connection in self.mp_hands.HAND_CONNECTIONS:
                start_idx, end_idx = connection
                start = hand.landmarks[start_idx]
                end = hand.landmarks[end_idx]
                
                start_point = (int(start[0] * w), int(start[1] * h))
                end_point = (int(end[0] * w), int(end[1] * h))
                
                color = (0, 255, 0) if hand.handedness == "Right" else (255, 0, 0)
                cv2.line(frame, start_point, end_point, color, 2)
            
            # Draw landmarks
            for i, lm in enumerate(hand.landmarks):
                x, y = int(lm[0] * w), int(lm[1] * h)
                cv2.circle(frame, (x, y), 5, (255, 255, 255), -1)
                cv2.circle(frame, (x, y), 3, (0, 0, 0), -1)
            
            # Draw handedness label
            wrist = hand.landmarks[0]
            label_pos = (int(wrist[0] * w) - 30, int(wrist[1] * h) - 20)
            cv2.putText(
                frame, hand.handedness,
                label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0) if hand.handedness == "Right" else (255, 0, 0),
                2
            )
        
        return frame
    
    def get_hand_by_type(
        self,
        hands: List[HandLandmarks],
        hand_type: str
    ) -> Optional[HandLandmarks]:
        """
        Get a specific hand by type.
        
        Args:
            hands: List of detected hands
            hand_type: "Left" or "Right"
            
        Returns:
            HandLandmarks if found, None otherwise
        """
        for hand in hands:
            if hand.handedness == hand_type:
                return hand
        return None
    
    def close(self) -> None:
        """Release resources."""
        self.hands.close()
