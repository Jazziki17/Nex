"""
Motion Detector - Sensing Movement
=====================================

LEARNING POINT: Motion Detection Algorithms
----------------------------------------------
Motion detection compares consecutive frames to find differences.
If pixels change significantly between frames, something moved.

ALGORITHM: Background Subtraction
------------------------------------
1. Maintain a "background model" (what the scene looks like when nothing moves)
2. Compare each new frame to the background
3. Pixels that differ significantly = foreground (motion)
4. Apply threshold to remove noise
5. Find contours (outlines) of moving regions
6. Filter by size to ignore tiny changes (dust, light flicker)

        Frame N          Frame N+1         Difference
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │           │    │     ○     │    │     ●     │  ← Motion detected
    │   ____    │    │   ____    │    │           │
    │  |    |   │    │  |    |   │    │           │
    └───────────┘    └───────────┘    └───────────┘

LEARNING POINT: Contour Analysis
-----------------------------------
A contour is the boundary of a shape in an image. After detecting
motion pixels, we find their contours to determine:
  - WHERE motion is (x, y coordinates)
  - HOW BIG the motion is (area in pixels)
  - WHAT SHAPE it is (could help identify people vs objects)
"""

import asyncio
from dataclasses import dataclass

from nex.core.engine import Module
from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class MotionEvent:
    """Represents a detected motion event."""
    x: int              # Horizontal position (pixels from left)
    y: int              # Vertical position (pixels from top)
    width: int          # Width of motion region
    height: int         # Height of motion region
    area: int           # Total area in pixels
    intensity: float    # How much change (0.0 to 1.0)


class MotionDetector(Module):
    """
    Detects motion by comparing consecutive camera frames.

    LEARNING POINT: Stateful Processing
    --------------------------------------
    This module is "stateful" — it remembers the previous frame
    to compare against the current one. This is why it has instance
    variables (self._previous_frame) instead of being a pure function.

    Stateful modules need careful lifecycle management:
    - Initialize state in start()
    - Clean up state in stop()
    - Handle the first frame (no previous frame to compare)
    """

    MIN_CONTOUR_AREA = 500   # Ignore motion smaller than this (pixels)
    MOTION_THRESHOLD = 25    # Pixel difference to count as motion (0-255)

    def __init__(self, event_bus: EventBus):
        super().__init__("MotionDetector", event_bus)
        self._previous_frame = None
        self._motion_cooldown = 0  # Prevents flooding events

    async def start(self) -> None:
        self._running = True
        self._previous_frame = None
        self.event_bus.subscribe("vision.frame", self._on_frame)
        logger.info("Motion detector ready.")

    async def stop(self) -> None:
        self._running = False
        self._previous_frame = None

    async def _on_frame(self, data: dict) -> None:
        """
        Process each frame to detect motion.

        LEARNING POINT: Frame Differencing
        ------------------------------------
        The simplest motion detection: subtract frame B from frame A.
        Large differences = motion. We convert to grayscale first
        because color doesn't matter for detecting movement.
        """
        frame = data.get("frame")
        if frame is None:
            return

        # Handle cooldown — don't report motion every single frame
        if self._motion_cooldown > 0:
            self._motion_cooldown -= 1
            self._previous_frame = frame
            return

        motions = self._detect_motion(frame)

        if motions:
            self._motion_cooldown = 10  # Wait 10 frames before next report

            await self.emit("vision.motion_detected", {
                "regions": [
                    {
                        "x": m.x, "y": m.y,
                        "width": m.width, "height": m.height,
                        "area": m.area, "intensity": m.intensity,
                    }
                    for m in motions
                ],
                "count": len(motions),
            })
            logger.debug(f"Motion detected: {len(motions)} region(s)")

        self._previous_frame = frame

    def _detect_motion(self, current_frame) -> list[MotionEvent]:
        """
        Compare current frame with previous to find motion regions.

        This handles both real OpenCV frames and simulated data.
        """
        if self._previous_frame is None:
            return []

        # Check if we're in simulation mode
        if isinstance(current_frame, dict) and current_frame.get("simulated"):
            return self._detect_motion_simulated(current_frame)

        # Real OpenCV-based detection
        return self._detect_motion_opencv(current_frame)

    def _detect_motion_opencv(self, current_frame) -> list[MotionEvent]:
        """
        Real motion detection using OpenCV.

        ALGORITHM STEPS:
        1. Convert both frames to grayscale
        2. Apply Gaussian blur to reduce noise
        3. Compute absolute difference between frames
        4. Apply threshold to get binary image (motion / no motion)
        5. Find contours of motion regions
        6. Filter small contours
        """
        try:
            import cv2
        except ImportError:
            return []

        # Step 1: Convert to grayscale
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_previous = cv2.cvtColor(self._previous_frame, cv2.COLOR_BGR2GRAY)

        # Step 2: Blur to reduce noise (5x5 kernel)
        gray_current = cv2.GaussianBlur(gray_current, (5, 5), 0)
        gray_previous = cv2.GaussianBlur(gray_previous, (5, 5), 0)

        # Step 3: Absolute difference
        diff = cv2.absdiff(gray_previous, gray_current)

        # Step 4: Binary threshold
        _, thresh = cv2.threshold(diff, self.MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)

        # Step 5: Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 6: Filter and convert to MotionEvents
        motions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.MIN_CONTOUR_AREA:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            intensity = area / (current_frame.shape[0] * current_frame.shape[1])

            motions.append(MotionEvent(
                x=x, y=y, width=w, height=h,
                area=int(area), intensity=min(intensity, 1.0),
            ))

        return motions

    def _detect_motion_simulated(self, frame: dict) -> list[MotionEvent]:
        """Simulated motion detection for development without a camera."""
        import random

        if frame.get("has_motion", False):
            return [MotionEvent(
                x=random.randint(0, 500),
                y=random.randint(0, 400),
                width=random.randint(50, 200),
                height=random.randint(50, 200),
                area=random.randint(2500, 40000),
                intensity=random.uniform(0.1, 0.8),
            )]

        return []
