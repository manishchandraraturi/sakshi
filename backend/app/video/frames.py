from pathlib import Path
from typing import List, Optional
import cv2
from app.video.meta import convert_webm_to_mp4


def _save_resized_frame(frame, out_dir: Path, frame_idx: int, max_dimension: int) -> str:
    """Resize a BGR frame keeping aspect ratio within max_dimension and save as JPEG."""
    h, w = frame.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / float(max(h, w))
        new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    out_file = out_dir / f"frame_{frame_idx:02d}.jpg"
    cv2.imwrite(str(out_file), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return str(out_file).replace("\\", "/")


def _extract_from_cap(
    cap: cv2.VideoCapture,
    out_dir: Path,
    max_frames: int,
    max_dimension: int,
) -> List[str]:
    """Extract evenly spaced frames from an open cv2.VideoCapture, or return [] on failure."""
    if not cap.isOpened():
        return []

    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        return []

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    saved_paths: List[str] = []

    if total_frames > 0:
        num_to_sample = min(max_frames, total_frames)
        if num_to_sample == 1 or total_frames == 1:
            indices = [0]
        else:
            indices = sorted(
                {
                    int(round(i * (total_frames - 1) / (num_to_sample - 1)))
                    for i in range(num_to_sample)
                }
            )

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                saved_paths.append(
                    _save_resized_frame(frame, out_dir, len(saved_paths), max_dimension)
                )
        return saved_paths

    # Sequential fallback for streams where total frame count is unreported (e.g. live WebM)
    frames_cache = []
    while len(frames_cache) < 300:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        frames_cache.append(frame)

    if not frames_cache:
        return []

    step = max(1, len(frames_cache) // max_frames)
    for i in range(0, len(frames_cache), step):
        if len(saved_paths) >= max_frames:
            break
        saved_paths.append(
            _save_resized_frame(frames_cache[i], out_dir, len(saved_paths), max_dimension)
        )
    return saved_paths


def _try_extract_from_path(
    path_str: str,
    out_dir: Path,
    max_frames: int,
    max_dimension: int,
) -> List[str]:
    """Open path_str with cv2.VideoCapture safely and extract frames."""
    try:
        cap = cv2.VideoCapture(path_str)
        try:
            return _extract_from_cap(cap, out_dir, max_frames, max_dimension)
        finally:
            cap.release()
    except Exception:
        return []


def extract_frames(
    video_path: Path | str,
    output_dir: Path | str | None = None,
    max_frames: int = 12,
    max_dimension: int = 768,
    attempt_id: Optional[str] = None,
) -> List[str]:
    """
    Extract up to `max_frames` evenly spaced across the video duration.
    Resizes each frame so that max(width, height) <= `max_dimension`.
    Saves frames as JPEG to `output_dir` (or `data/frames/<attempt_id>`) and returns paths.
    Falls back to FFmpeg .mp4 transcoding when OpenCV cannot read the container directly.
    """
    path_str = str(video_path)
    if output_dir is None:
        data_frames = Path(__file__).resolve().parent.parent.parent / "data" / "frames"
        out_dir = data_frames / (attempt_id or "default")
    else:
        out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try OpenCV directly on the source video
    saved_paths = _try_extract_from_path(path_str, out_dir, max_frames, max_dimension)

    # 2. If OpenCV failed (common with browser-generated .webm), convert via FFmpeg to .mp4
    if not saved_paths:
        temp_mp4 = convert_webm_to_mp4(path_str)
        if temp_mp4 is not None:
            try:
                saved_paths = _try_extract_from_path(
                    str(temp_mp4), out_dir, max_frames, max_dimension
                )
            finally:
                if temp_mp4.exists():
                    try:
                        temp_mp4.unlink()
                    except Exception:
                        pass

    if not saved_paths:
        raise ValueError(f"Could not extract frames from video '{path_str}'")

    return saved_paths

