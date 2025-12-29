#!/usr/bin/env python3
"""
Test script to verify computer vision components are working.
Run: python -m scripts.test_cv [video_file]
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import time


def test_video(video_path: str = "WIN_20251205_08_56_24_Pro.mp4"):
    """Test video playback with hand detection overlay."""
    
    print("=" * 50)
    print("🧪 VIOLIN CV TEST")
    print("=" * 50)
    
    # Test 1: Imports
    print("\n📦 Test 1: Importing components...")
    try:
        from src.vision.hand_detector import HandDetector
        from src.vision.gesture_recognizer import GestureRecognizer
        from src.music.note_mapper import NoteMapper
        from src.utils.config import Config
        print("   ✅ All imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Create components
    print("\n🔧 Test 2: Creating components...")
    try:
        config = Config()
        detector = HandDetector(config)
        recognizer = GestureRecognizer(config)
        mapper = NoteMapper(config)
        print("   ✅ All components created")
    except Exception as e:
        print(f"   ❌ Component creation failed: {e}")
        return False
    
    # Test 3: Open video
    print(f"\n🎬 Test 3: Opening video '{video_path}'...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"   ❌ Cannot open video: {video_path}")
        return False
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"   ✅ Video: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")
    
    # Test 4: Process frames with hand detection
    print("\n🖐️ Test 4: Processing frames with hand detection...")
    print("   (Press 'q' to quit, 'space' to pause)")
    
    frame_count = 0
    hands_detected_frames = 0
    start_time = time.time()
    paused = False
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("\n   📹 Video ended")
                break
            
            frame_count += 1
            
            # Detect hands
            hands = detector.detect(frame)
            
            if hands:
                hands_detected_frames += 1
                
                # Draw landmarks
                frame = detector.draw_landmarks(frame, hands)
                
                # Recognize gestures
                gestures = recognizer.recognize(hands)
                
                # Get note if bow is active
                if gestures.get('bow_active'):
                    string = gestures.get('string', 1)
                    position = gestures.get('position', 1)
                    fingers = gestures.get('finger_count', 0)
                    pitch = gestures.get('pitch_offset', 0)
                    
                    note = mapper.get_note(string, position, fingers, pitch)
                    note_name = mapper.get_note_name(note) if hasattr(mapper, 'get_note_name') else f"MIDI {note}"
                    
                    # Draw note on frame
                    cv2.putText(frame, f"NOTE: {note_name}", (50, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    cv2.putText(frame, f"String: {string}, Fingers: {fingers}", (50, 150),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            # Draw stats
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed if elapsed > 0 else 0
            
            cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {actual_fps:.1f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Hands: {'Yes' if hands else 'No'}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if hands else (0, 0, 255), 2)
        
        # Show frame
        cv2.imshow("CV Test - Press Q to quit", frame)
        
        # Handle keys
        key = cv2.waitKey(1 if not paused else 0) & 0xFF
        if key == ord('q'):
            print("\n   ⏹️ User quit")
            break
        elif key == ord(' '):
            paused = not paused
            print(f"   {'⏸️ Paused' if paused else '▶️ Resumed'}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Results
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    print(f"   Frames processed: {frame_count}")
    print(f"   Frames with hands: {hands_detected_frames} ({100*hands_detected_frames/max(1,frame_count):.1f}%)")
    print(f"   Time elapsed: {elapsed:.1f}s")
    print(f"   Average FPS: {frame_count/elapsed:.1f}")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "WIN_20251205_08_56_24_Pro.mp4"
    success = test_video(video)
    sys.exit(0 if success else 1)
