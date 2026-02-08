"""
Camera Stream - Kai's Eyes
============================

LEARNING POINT: Video Processing
-----------------------------------
A video is just a sequence of images (frames) shown rapidly.
Typically 30 FPS (frames per second). Each frame is a 2D grid of
pixels, where each pixel has Red, Green, Blue values (0-255).

A 1920x1080 frame = 1920 * 1080 * 3 bytes = ~6 MB per frame
At 30 FPS = ~180 MB/s of raw data!

This is why efficient processing matters. We:
  - Resize frames before processing (smaller = faster)
  - Skip frames when the system is busy
  - Only process what we need (e.g., grayscale for motion detection)

LEARNING POINT: OpenCV
-------------------------
OpenCV (Open Computer Vision) is the standard library for image/video
processing. Key operations:
  - cv2.VideoCapture(0)        — open default camera
  - cap.read()                 — grab one frame
  - cv2.cvtColor(frame, ...)   — convert colors (BGR→Gray, etc.)
  - cv2.resize(frame, size)    — resize for performance
  - cv2.imshow("Window", frame)— display in a window
"""

import asyncio
from typing import Any

from kai.core.engine import Module
from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


class CameraStream(Module):
    """
    Manages camera input and distributes frames to processing modules.

    LEARNING POINT: Producer Pattern
    -----------------------------------
    The camera is a "producer" — it generates frames continuously.
    Other modules (motion detector, gesture recognizer) are "consumers"
    that process these frames. The event bus connects them.

    This decoupling means:
    - Camera code doesn't know what will process its frames
    - You can add new processors without touching camera code
    - Processors can run at different speeds independently
    """

    DEFAULT_FPS = 15           # Process 15 frames per second
    DEFAULT_RESOLUTION = (640, 480)  # Width x Height

    def __init__(
        self,
        event_bus: EventBus,
        camera_id: int = 0,
        fps: int = DEFAULT_FPS,
    ):
        super().__init__("CameraStream", event_bus)
        self.camera_id = camera_id
        self.fps = fps
        self._capture = None
        self._capture_task: asyncio.Task | None = None
        self._frame_count = 0

    async def start(self) -> None:
        """
        Start the camera capture.

        LEARNING POINT: Resource Management
        --------------------------------------
        Hardware resources (camera, microphone) need careful handling:
        1. Open them when needed (start)
        2. Release them when done (stop)
        3. Handle errors (camera in use by another app)
        4. Only one module should own a hardware resource at a time
        """
        self._running = True
        self._frame_count = 0

        # Try to open the camera
        try:
            self._capture = self._open_camera()
            logger.info(f"Camera {self.camera_id} opened at {self.fps} FPS")
        except Exception as e:
            logger.warning(f"Camera not available: {e}. Running in simulation mode.")
            self._capture = None

        # Start frame capture loop
        self._capture_task = asyncio.create_task(self._capture_loop())

    async def stop(self) -> None:
        """Stop capture and release the camera."""
        self._running = False
        if self._capture_task:
            self._capture_task.cancel()
            try:
                await self._capture_task
            except asyncio.CancelledError:
                pass
        self._release_camera()
        logger.info(f"Camera stopped after {self._frame_count} frames.")

    def _open_camera(self) -> Any:
        """
        Open the camera device.

        Returns the capture object, or None if OpenCV is not installed.
        """
        try:
            import cv2
            cap = cv2.VideoCapture(self.camera_id)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open camera {self.camera_id}")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.DEFAULT_RESOLUTION[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.DEFAULT_RESOLUTION[1])
            return cap
        except ImportError:
            logger.debug("OpenCV not installed — using simulation mode")
            return None

    def _release_camera(self) -> None:
        """Release camera resources."""
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None

    async def _capture_loop(self) -> None:
        """
        Continuous frame capture loop.

        LEARNING POINT: Frame Rate Control
        -------------------------------------
        We calculate how long to sleep between frames to maintain
        the target FPS. If processing takes 20ms and we want 30 FPS
        (33ms per frame), we sleep for 13ms.

        frame_interval = 1 / fps = 1 / 30 = 0.033 seconds
        """
        frame_interval = 1.0 / self.fps

        while self._running:
            frame = await self._grab_frame()

            if frame is not None:
                self._frame_count += 1

                # Publish frame for other modules to process
                await self.emit("vision.frame", {
                    "frame": frame,
                    "frame_number": self._frame_count,
                    "resolution": self.DEFAULT_RESOLUTION,
                })

            await asyncio.sleep(frame_interval)

    async def _grab_frame(self) -> Any:
        """
        Grab a single frame from the camera.

        LEARNING POINT: Simulation Data
        ----------------------------------
        When the real camera isn't available, we generate simulated
        frame metadata. This lets the rest of the vision pipeline
        run and be tested without actual camera hardware.
        """
        if self._capture is not None:
            # Real camera
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self._capture.read)
            return frame if ret else None
        else:
            # Simulated frame — just metadata
            import random
            return {
                "simulated": True,
                "width": self.DEFAULT_RESOLUTION[0],
                "height": self.DEFAULT_RESOLUTION[1],
                "brightness": random.uniform(0.3, 0.9),
                "has_motion": random.random() < 0.2,  # 20% chance
            }
