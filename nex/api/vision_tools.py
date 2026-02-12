"""
Vision Tools — On-demand camera capture + YOLO object detection/classification/segmentation.

Key design: NO persistent camera stream. Each request opens the camera, grabs one frame,
and releases immediately. This avoids the TTS feedback loops caused by continuous-stream
vision modules (nex/vision/camera.py etc).

Models are lazy-loaded on first use (~6MB download each).
"""

import asyncio
import os
from pathlib import Path

from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

# Lazy-loaded model cache
_detect_model = None
_cls_model = None
_seg_model = None


def _get_detect_model():
    global _detect_model
    if _detect_model is None:
        from ultralytics import YOLO
        logger.info("Loading YOLOv8n detection model (first use)...")
        _detect_model = YOLO("yolov8n.pt")
        logger.info("Detection model ready.")
    return _detect_model


def _get_cls_model():
    global _cls_model
    if _cls_model is None:
        from ultralytics import YOLO
        logger.info("Loading YOLOv8n classification model (first use)...")
        _cls_model = YOLO("yolov8n-cls.pt")
        logger.info("Classification model ready.")
    return _cls_model


def _get_seg_model():
    global _seg_model
    if _seg_model is None:
        from ultralytics import YOLO
        logger.info("Loading YOLOv8n segmentation model (first use)...")
        _seg_model = YOLO("yolov8n-seg.pt")
        logger.info("Segmentation model ready.")
    return _seg_model


def _capture_frame():
    """Open camera, grab one frame, release immediately. Returns numpy array or None."""
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    # Let camera auto-expose for a moment
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return frame


def _load_image(path: str):
    """Load an image from a file path. Returns numpy array or None."""
    import cv2
    expanded = os.path.expanduser(path)
    p = Path(expanded)
    if not p.exists():
        return None
    frame = cv2.imread(str(p))
    return frame


def _get_frame(source: str):
    """Get a frame from camera or file path."""
    if source == "camera":
        return _capture_frame()
    return _load_image(source)


async def detect_objects(source: str = "camera") -> str:
    """Run YOLO detection. Returns formatted text of detected objects with confidence."""
    try:
        frame = await asyncio.to_thread(_get_frame, source)
        if frame is None:
            return f"Error: Could not {'access camera' if source == 'camera' else f'load image: {source}'}."

        model = await asyncio.to_thread(_get_detect_model)
        results = await asyncio.to_thread(model.predict, frame, verbose=False)

        if not results or len(results[0].boxes) == 0:
            return "No objects detected."

        detections = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = results[0].names[cls_id]
            detections.append((name, conf))

        # Sort by confidence, deduplicate by counting
        from collections import Counter
        counts = Counter(name for name, _ in detections)
        best_conf = {}
        for name, conf in detections:
            if name not in best_conf or conf > best_conf[name]:
                best_conf[name] = conf

        lines = []
        for name, count in counts.most_common():
            conf = best_conf[name]
            qty = f" x{count}" if count > 1 else ""
            lines.append(f"- {name}{qty} ({conf:.0%} confidence)")

        src = "camera" if source == "camera" else Path(source).name
        return f"Objects detected ({src}):\n" + "\n".join(lines)

    except ImportError:
        return "Error: Vision dependencies not installed. Run: pip install ultralytics opencv-python"
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        return f"Error during detection: {e}"


async def classify_image(source: str = "camera") -> str:
    """Run YOLO classification. Returns top-5 classes with confidence."""
    try:
        frame = await asyncio.to_thread(_get_frame, source)
        if frame is None:
            return f"Error: Could not {'access camera' if source == 'camera' else f'load image: {source}'}."

        model = await asyncio.to_thread(_get_cls_model)
        results = await asyncio.to_thread(model.predict, frame, verbose=False)

        if not results or results[0].probs is None:
            return "Could not classify the image."

        probs = results[0].probs
        top5_indices = probs.top5
        top5_confs = probs.top5conf.tolist()
        names = results[0].names

        lines = []
        for idx, conf in zip(top5_indices, top5_confs):
            lines.append(f"- {names[idx]} ({conf:.0%})")

        src = "camera" if source == "camera" else Path(source).name
        return f"Image classification ({src}):\n" + "\n".join(lines)

    except ImportError:
        return "Error: Vision dependencies not installed. Run: pip install ultralytics opencv-python"
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        return f"Error during classification: {e}"


async def segment_scene(source: str = "camera") -> str:
    """Run YOLO segmentation. Returns segment descriptions with confidence."""
    try:
        frame = await asyncio.to_thread(_get_frame, source)
        if frame is None:
            return f"Error: Could not {'access camera' if source == 'camera' else f'load image: {source}'}."

        model = await asyncio.to_thread(_get_seg_model)
        results = await asyncio.to_thread(model.predict, frame, verbose=False)

        if not results or len(results[0].boxes) == 0:
            return "No distinct segments detected."

        segments = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = results[0].names[cls_id]
            segments.append((name, conf))

        from collections import Counter
        counts = Counter(name for name, _ in segments)
        best_conf = {}
        for name, conf in segments:
            if name not in best_conf or conf > best_conf[name]:
                best_conf[name] = conf

        lines = []
        for name, count in counts.most_common():
            conf = best_conf[name]
            qty = f" x{count}" if count > 1 else ""
            lines.append(f"- {name}{qty} ({conf:.0%} confidence)")

        src = "camera" if source == "camera" else Path(source).name
        return f"Scene segmentation ({src}):\n" + "\n".join(lines)

    except ImportError:
        return "Error: Vision dependencies not installed. Run: pip install ultralytics opencv-python"
    except Exception as e:
        logger.error(f"Segmentation error: {e}", exc_info=True)
        return f"Error during segmentation: {e}"
