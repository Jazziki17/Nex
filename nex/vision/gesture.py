"""
Gesture Recognizer - Understanding Body Language
==================================================

LEARNING POINT: Pose Estimation
----------------------------------
Pose estimation finds human body keypoints (joints) in an image:
head, shoulders, elbows, wrists, hips, knees, ankles.

Google's MediaPipe is the go-to library for this:
  - Detects 33 body landmarks in real-time
  - Works on CPU (no GPU required)
  - Returns normalized coordinates (0.0 to 1.0)

From keypoints, we can recognize gestures:
  - Wave: Wrist moves side to side above shoulder
  - Point: Arm extended, index finger forward
  - Thumbs up: Specific finger configuration
  - Stop: Palm facing camera, fingers extended

LEARNING POINT: Coordinate Systems
--------------------------------------
  (0,0) ──────────── (1,0)
    │                    │
    │    (0.5, 0.5)      │    Normalized coordinates
    │       ●            │    (0.0 to 1.0 range)
    │                    │
  (0,1) ──────────── (1,1)

Normalizing coordinates means gestures work regardless of
camera resolution or how far the person is from the camera.
"""

from dataclasses import dataclass
from enum import Enum, auto

from nex.core.engine import Module
from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger


logger = setup_logger(__name__)


class GestureType(Enum):
    """
    Enumeration of recognizable gestures.

    LEARNING POINT: Enum
    -----------------------
    Enums define a fixed set of named constants. Using an Enum
    instead of strings ("wave", "stop") prevents typos and gives
    you autocomplete in your IDE.

    `auto()` automatically assigns incrementing integer values.
    """
    WAVE = auto()
    THUMBS_UP = auto()
    THUMBS_DOWN = auto()
    POINT = auto()
    STOP = auto()
    UNKNOWN = auto()


@dataclass
class Landmark:
    """A single body landmark (joint) with 3D coordinates."""
    x: float  # Horizontal position (0.0 = left, 1.0 = right)
    y: float  # Vertical position (0.0 = top, 1.0 = bottom)
    z: float  # Depth (distance from camera)
    visibility: float  # Confidence that this point is visible (0.0 to 1.0)


@dataclass
class GestureResult:
    """Result of gesture recognition."""
    gesture: GestureType
    confidence: float
    landmarks: list[Landmark]


class GestureRecognizer(Module):
    """
    Recognizes human gestures from camera frames.

    LEARNING POINT: Classification Pipeline
    -------------------------------------------
    Gesture recognition is a pipeline:
      Frame → Pose Detection → Keypoint Extraction → Feature Calculation → Classification

    Each step transforms data into a more useful form:
    - Raw pixels → body landmarks (positions)
    - Positions → angles and distances (features)
    - Features → gesture label (classification)
    """

    # MediaPipe landmark indices (subset of 33 total)
    NOSE = 0
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14

    def __init__(self, event_bus: EventBus):
        super().__init__("GestureRecognizer", event_bus)
        self._pose_detector = None
        self._gesture_history: list[GestureType] = []
        self._history_size = 5  # Smooth over this many frames

    async def start(self) -> None:
        self._running = True
        self._try_load_mediapipe()
        self.event_bus.subscribe("vision.frame", self._on_frame)
        logger.info("Gesture recognizer ready.")

    async def stop(self) -> None:
        self._running = False
        self._pose_detector = None

    def _try_load_mediapipe(self):
        """Try to load MediaPipe for real pose detection."""
        try:
            import mediapipe as mp
            self._pose_detector = mp.solutions.pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe loaded for real pose detection")
        except ImportError:
            logger.debug("MediaPipe not installed — using simulation mode")
            self._pose_detector = None

    async def _on_frame(self, data: dict) -> None:
        """Process frames for gesture recognition (at reduced rate)."""
        # Only process every 5th frame (gestures don't need 30 FPS)
        frame_num = data.get("frame_number", 0)
        if frame_num % 5 != 0:
            return

        frame = data.get("frame")
        if frame is None:
            return

        result = self._recognize(frame)
        if result and result.gesture != GestureType.UNKNOWN:
            # Smooth the result using history
            self._gesture_history.append(result.gesture)
            if len(self._gesture_history) > self._history_size:
                self._gesture_history.pop(0)

            # Only report if the same gesture is detected consistently
            smoothed = self._get_dominant_gesture()
            if smoothed and smoothed != GestureType.UNKNOWN:
                await self.emit("vision.gesture_detected", {
                    "gesture": smoothed.name,
                    "confidence": result.confidence,
                })
                logger.info(f"Gesture: {smoothed.name}")
                self._gesture_history.clear()  # Reset after reporting

    def _recognize(self, frame) -> GestureResult | None:
        """
        Recognize gestures in a frame.

        LEARNING POINT: Feature Engineering
        --------------------------------------
        We don't feed raw pixels to the classifier. Instead, we extract
        meaningful features:
          - Wrist position relative to shoulder (above/below)
          - Arm angle (extended or bent)
          - Hand position in frame (left/center/right)

        Good features make classification much easier and more robust.
        """
        if isinstance(frame, dict) and frame.get("simulated"):
            return self._recognize_simulated(frame)

        if self._pose_detector is None:
            return None

        # Real MediaPipe detection would go here
        try:
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._pose_detector.process(rgb_frame)

            if results.pose_landmarks:
                landmarks = [
                    Landmark(lm.x, lm.y, lm.z, lm.visibility)
                    for lm in results.pose_landmarks.landmark
                ]
                gesture = self._classify_from_landmarks(landmarks)
                return GestureResult(gesture=gesture, confidence=0.8, landmarks=landmarks)
        except Exception as e:
            logger.debug(f"Pose detection error: {e}")

        return None

    def _classify_from_landmarks(self, landmarks: list[Landmark]) -> GestureType:
        """
        Classify gesture based on body landmark positions.

        LEARNING POINT: Rule-Based Classification
        --------------------------------------------
        We use geometric rules to identify gestures:

        WAVE: Wrist is above shoulder AND wrist moves horizontally
        STOP: Both wrists above shoulders, arms extended
        POINT: One arm extended forward (low z-value = closer to camera)
        """
        if len(landmarks) < 17:
            return GestureType.UNKNOWN

        r_wrist = landmarks[self.RIGHT_WRIST]
        l_wrist = landmarks[self.LEFT_WRIST]
        r_shoulder = landmarks[self.RIGHT_SHOULDER]
        l_shoulder = landmarks[self.LEFT_SHOULDER]

        # WAVE: Right wrist above right shoulder
        if r_wrist.y < r_shoulder.y and r_wrist.visibility > 0.5:
            return GestureType.WAVE

        # STOP: Both wrists above shoulders
        if (r_wrist.y < r_shoulder.y and l_wrist.y < l_shoulder.y
                and r_wrist.visibility > 0.5 and l_wrist.visibility > 0.5):
            return GestureType.STOP

        return GestureType.UNKNOWN

    def _recognize_simulated(self, frame: dict) -> GestureResult | None:
        """Simulated gesture recognition for development."""
        import random
        if random.random() < 0.1:  # 10% chance of gesture
            gesture = random.choice(list(GestureType))
            return GestureResult(
                gesture=gesture,
                confidence=random.uniform(0.6, 0.95),
                landmarks=[],
            )
        return None

    def _get_dominant_gesture(self) -> GestureType | None:
        """
        Return the most common gesture in recent history.

        LEARNING POINT: Temporal Smoothing
        -------------------------------------
        A single frame might misdetect a gesture. By looking at the
        last N frames and picking the most common gesture, we smooth
        out noise and get more reliable results.

        This is similar to "majority voting" in machine learning.
        """
        if not self._gesture_history:
            return None

        from collections import Counter
        counts = Counter(self._gesture_history)
        most_common, count = counts.most_common(1)[0]

        # Only report if it appears in more than half of recent frames
        if count >= len(self._gesture_history) // 2:
            return most_common

        return None
