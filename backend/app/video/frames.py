from pathlib import Path
from typing import List
import cv2


def extract_frames(
    video_path: Path | str,
    output_dir: Path | str,
    max_frames: int = 12,
    max_dimension: int = 768,
) -> List[str]:
    """
    Extract up to `max_frames` evenly spaced across the video duration.
    Resizes each frame so that max(width, height) <= `max_dimension`.
    Saves frames as JPEG to `output_dir` and returns their file paths.
    """
    path_str = str(video_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(path_str)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file '{path_str}' for frame extraction")

    saved_paths: List[str] = []

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError("Video contains zero extractable frames")

        # Determine evenly spaced frame indices
        num_frames_to_sample = min(max_frames, total_frames)
        if num_frames_to_sample == 1 or total_frames == 1:
            frame_indices = [0]
        else:
            frame_indices = [
                int(round(i * (total_frames - 1) / (num_frames_to_sample - 1)))
                for i in range(num_frames_to_sample)
            ]

        # Deduplicate while preserving order
        unique_indices = sorted(list(set(frame_indices)))

        for i, idx in enumerate(unique_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            h, w = frame.shape[:2]
            if max(h, w) > max_dimension:
                scale = max_dimension / float(max(h, w))
                new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            frame_filename = f"frame_{i:02d}.jpg"
            out_file = out_dir / frame_filename
            cv2.imwrite(str(out_file), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            saved_paths.append(str(out_file).replace("\\", "/"))

        if not saved_paths:
            raise ValueError("Failed to extract any readable frames from video")

        return saved_paths

    finally:
        cap.release()
