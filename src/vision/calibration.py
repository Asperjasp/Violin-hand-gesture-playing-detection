"""
Calibration utilities for position detection.
"""

import cv2
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

from src.utils.config import Config
from src.vision.hand_detector import HandDetector


class CalibrationWizard:
    """
    Interactive calibration for position zones.
    
    Guides the user through calibrating the three violin positions
    based on their natural hand positions.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the calibration wizard.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.hand_detector = HandDetector(config)
        self.calibration_data: Dict[str, Dict] = {}
        
        self.positions = ["first", "second", "third"]
        self.samples_per_position = 30
    
    def run(self) -> Dict:
        """
        Run the calibration process.
        
        Returns:
            Calibration data dictionary
        """
        cap = cv2.VideoCapture(self.config.camera.device_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera.resolution["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera.resolution["height"])
        
        print("\n=== Position Calibration Wizard ===\n")
        print("This will calibrate the three violin positions based on your hand.")
        print("Follow the on-screen instructions.\n")
        
        for position in self.positions:
            print(f"\nCalibrating {position} position...")
            print("Place your left hand in the position and press SPACE to sample.")
            print("Press 'q' to skip this position.\n")
            
            samples = []
            
            while len(samples) < self.samples_per_position:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if self.config.camera.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                
                hands = self.hand_detector.detect(frame)
                left_hand = self.hand_detector.get_hand_by_type(hands, "Left")
                
                # Draw UI
                frame = self._draw_calibration_ui(
                    frame, position, len(samples), left_hand
                )
                
                cv2.imshow("Calibration", frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' ') and left_hand:
                    # Sample the Y coordinate
                    y = left_hand.thumb_tip[1]
                    samples.append(y)
                    print(f"  Sample {len(samples)}/{self.samples_per_position}: Y = {y:.4f}")
                
                elif key == ord('q'):
                    print(f"  Skipped {position} position")
                    break
            
            if samples:
                self.calibration_data[position] = {
                    "min": min(samples),
                    "max": max(samples),
                    "mean": sum(samples) / len(samples),
                    "samples": len(samples)
                }
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Process and save calibration
        if self.calibration_data:
            zones = self._calculate_zones()
            self._save_calibration(zones)
            return zones
        
        return {}
    
    def _draw_calibration_ui(
        self,
        frame: np.ndarray,
        position: str,
        sample_count: int,
        left_hand
    ) -> np.ndarray:
        """Draw calibration UI overlay."""
        h, w, _ = frame.shape
        
        # Draw hand landmarks if detected
        if left_hand:
            frame = self.hand_detector.draw_landmarks(frame, [left_hand])
            
            # Draw thumb tip indicator
            thumb_y = left_hand.thumb_tip[1]
            y_px = int(thumb_y * h)
            cv2.line(frame, (0, y_px), (w, y_px), (0, 255, 255), 2)
            cv2.putText(
                frame, f"Y: {thumb_y:.4f}",
                (10, y_px - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
            )
        
        # Draw instructions
        cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.putText(
            frame, f"Calibrating: {position.upper()} position",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
        )
        cv2.putText(
            frame, f"Samples: {sample_count}/{self.samples_per_position} | SPACE to sample | Q to skip",
            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1
        )
        
        return frame
    
    def _calculate_zones(self) -> Dict:
        """Calculate position zones from calibration data."""
        zones = {}
        
        # Sort positions by mean Y value
        sorted_positions = sorted(
            self.calibration_data.items(),
            key=lambda x: x[1]["mean"]
        )
        
        for i, (position, data) in enumerate(sorted_positions):
            if i == 0:
                zones[position] = {"min": 0.0, "max": data["max"]}
            elif i == len(sorted_positions) - 1:
                prev_max = zones[sorted_positions[i-1][0]]["max"]
                zones[position] = {"min": prev_max, "max": 1.0}
            else:
                prev_max = zones[sorted_positions[i-1][0]]["max"]
                zones[position] = {"min": prev_max, "max": data["max"]}
        
        return zones
    
    def _save_calibration(self, zones: Dict) -> None:
        """Save calibration to file."""
        profile_dir = Path("config/calibration_profiles")
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        filepath = profile_dir / filename
        
        calibration = {
            "created": datetime.now().isoformat(),
            "position_zones": zones,
            "raw_data": self.calibration_data
        }
        
        with open(filepath, "w") as f:
            yaml.dump(calibration, f, default_flow_style=False)
        
        print(f"\nCalibration saved to: {filepath}")


def run_calibration(config: Config) -> Dict:
    """
    Run the calibration wizard.
    
    Args:
        config: Application configuration
        
    Returns:
        Calibration zones dictionary
    """
    wizard = CalibrationWizard(config)
    return wizard.run()
