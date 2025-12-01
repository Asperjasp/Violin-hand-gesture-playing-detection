"""
Utility helper functions.
"""

import time
from typing import Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass
import math


@dataclass
class FPSCounter:
    """Frames per second counter."""
    
    def __init__(self, window_size: int = 30):
        """
        Initialize FPS counter.
        
        Args:
            window_size: Number of frames to average
        """
        self.window_size = window_size
        self.timestamps: list = []
    
    def tick(self) -> float:
        """
        Record a frame and return current FPS.
        
        Returns:
            Current FPS estimate
        """
        now = time.time()
        self.timestamps.append(now)
        
        # Keep only recent timestamps
        if len(self.timestamps) > self.window_size:
            self.timestamps.pop(0)
        
        # Calculate FPS
        if len(self.timestamps) < 2:
            return 0.0
        
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed <= 0:
            return 0.0
        
        return (len(self.timestamps) - 1) / elapsed


class Debouncer:
    """Debounce rapid value changes."""
    
    def __init__(self, delay_ms: int = 50):
        """
        Initialize debouncer.
        
        Args:
            delay_ms: Minimum time between value changes
        """
        self.delay_ms = delay_ms
        self.last_value: Any = None
        self.last_time: float = 0
        self.stable_value: Any = None
    
    def update(self, value: Any) -> Any:
        """
        Update with new value and return stable value.
        
        Args:
            value: New value
            
        Returns:
            Stable (debounced) value
        """
        now = time.time() * 1000
        
        if value != self.last_value:
            self.last_value = value
            self.last_time = now
        
        if now - self.last_time >= self.delay_ms:
            self.stable_value = self.last_value
        
        return self.stable_value


class Smoother:
    """Smooth noisy values using exponential moving average."""
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize smoother.
        
        Args:
            alpha: Smoothing factor (0-1, higher = less smoothing)
        """
        self.alpha = alpha
        self.value: Optional[float] = None
    
    def update(self, value: float) -> float:
        """
        Update with new value and return smoothed value.
        
        Args:
            value: New value
            
        Returns:
            Smoothed value
        """
        if self.value is None:
            self.value = value
        else:
            self.value = self.alpha * value + (1 - self.alpha) * self.value
        
        return self.value
    
    def reset(self) -> None:
        """Reset the smoother."""
        self.value = None


def euclidean_distance(p1: tuple, p2: tuple) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        p1: First point (x, y) or (x, y, z)
        p2: Second point (x, y) or (x, y, z)
        
    Returns:
        Distance between points
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def normalize_coordinates(
    x: float,
    y: float,
    width: int,
    height: int
) -> tuple:
    """
    Normalize pixel coordinates to 0-1 range.
    
    Args:
        x: X coordinate in pixels
        y: Y coordinate in pixels
        width: Frame width
        height: Frame height
        
    Returns:
        Tuple of (norm_x, norm_y)
    """
    return (x / width, y / height)


def denormalize_coordinates(
    norm_x: float,
    norm_y: float,
    width: int,
    height: int
) -> tuple:
    """
    Convert normalized coordinates to pixels.
    
    Args:
        norm_x: Normalized X (0-1)
        norm_y: Normalized Y (0-1)
        width: Frame width
        height: Frame height
        
    Returns:
        Tuple of (x, y) in pixels
    """
    return (int(norm_x * width), int(norm_y * height))


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value to range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def map_range(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float
) -> float:
    """
    Map value from one range to another.
    
    Args:
        value: Input value
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
        
    Returns:
        Mapped value
    """
    # Clamp input
    value = clamp(value, in_min, in_max)
    
    # Map
    return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min)


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that prints execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        print(f"{func.__name__}: {elapsed:.2f}ms")
        return result
    
    return wrapper
