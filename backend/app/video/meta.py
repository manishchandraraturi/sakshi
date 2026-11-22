from pathlib import Path
from typing import Any, Dict
import cv2


def extract_metadata(video_path: Path | str) -> Dict[str, Any]:
    """
    Extract technical metadata (duration, resolution, fps, frame count)
    from a video file using OpenCV.
    Raises ValueError if video cannot be opened or has invalid stream metrics.
    """
    path_str = str(video_path)
    cap = cv2.VideoCapture(path_str)

    if not cap.isOpened():
        raise ValueError(f"Could not open video file at '{path_str}'")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0 or frame_count <= 0:
            raise ValueError(
                f"Invalid video stream metrics (fps={fps}, frame_count={frame_count})"
            )

        duration = frame_count / fps

        if duration <= 0 or width <= 0 or height <= 0:
            raise ValueError(
                f"Invalid video parameters (duration={duration}, width={width}, height={height})"
            )

        return {
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "fps": round(fps, 2),
            "frame_count": frame_count,
        }
    finally:
        cap.release()
