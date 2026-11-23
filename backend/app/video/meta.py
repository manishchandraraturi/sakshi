from pathlib import Path
import re
import subprocess
from typing import Any, Dict
import cv2


def _extract_via_ffmpeg(path_str: str) -> Dict[str, Any] | None:
    """Extract metadata using imageio_ffmpeg binary which supports WebM/VP8/VP9 on Windows."""
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        res = subprocess.run(
            [exe, "-hide_banner", "-i", path_str],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
        )
        stderr = res.stderr

        # Parse Duration: 00:01:23.45
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
        duration = 0.0
        if dur_match:
            hours = float(dur_match.group(1))
            mins = float(dur_match.group(2))
            secs = float(dur_match.group(3))
            duration = hours * 3600 + mins * 60 + secs

        # Parse Video: ..., 1280x720 ..., 30 fps
        res_match = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", stderr)
        width, height = (0, 0)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))

        fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", stderr)
        fps = float(fps_match.group(1)) if fps_match else 30.0

        # If duration was not in header (common in live browser webm recordings), count frames and secs
        if duration <= 0:
            try:
                nframes, nsecs = imageio_ffmpeg.count_frames_and_secs(path_str)
                if nsecs and nsecs > 0:
                    duration = float(nsecs)
                if nframes and nframes > 0 and fps <= 0:
                    fps = nframes / duration if duration > 0 else 30.0
            except Exception:
                pass

        # If width or height are still missing, try read_frames generator meta
        if width <= 0 or height <= 0:
            try:
                gen = imageio_ffmpeg.read_frames(path_str)
                meta = next(gen)
                gen.close()
                w, h = meta.get("size", (0, 0))
                if w > 0 and h > 0:
                    width, height = w, h
                if duration <= 0 and meta.get("duration", 0) > 0:
                    duration = float(meta["duration"])
                if fps <= 0 and meta.get("fps", 0) > 0:
                    fps = float(meta["fps"])
            except Exception:
                pass

        if duration > 0 and width > 0 and height > 0:
            frame_count = int(duration * fps) if fps > 0 else int(duration * 30)
            return {
                "duration": round(duration, 2),
                "width": width,
                "height": height,
                "fps": round(fps, 2) if fps > 0 else 30.0,
                "frame_count": max(1, frame_count),
            }
    except Exception:
        pass
    return None


def extract_metadata(video_path: Path | str) -> Dict[str, Any]:
    """
    Extract technical metadata (duration, resolution, fps, frame count)
    from a video file using imageio_ffmpeg with fallback to OpenCV.
    Raises ValueError if video cannot be opened or has invalid stream metrics.
    """
    path_str = str(video_path)

    # 1. Try ffmpeg extraction (works for WebM, MP4, etc. on all OSes)
    meta = _extract_via_ffmpeg(path_str)
    if meta is not None:
        return meta

    # 2. Fallback to OpenCV
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
