"""
forensics/jpeg_ghost.py
━━━━━━━━━━━━━━━━━━━━━━
JPEG Double Compression Detection.

When any software (Photoshop, Snapseed, Canva, Preview, GIMP) edits and
re-saves a JPEG, it compresses it twice with different quantization tables.
This leaves a detectable periodic pattern in DCT coefficients that is
software-agnostic — it catches edits regardless of what tool was used.

Works on: JPG, JPEG
Skipped for: PNG, TIFF, PDF (single compression layer, not applicable)
"""

import cv2
import numpy as np
from pathlib import Path

# ─── CONFIG ────────────────────────────────────────────────────────────────────

QUALITY_LEVELS   = [51, 61, 71, 81, 91]   # Re-compression levels to test
GHOST_THRESHOLD  = 0.015                   # Mean ghost score above this = anomaly
SUPPORTED_EXTS   = {".jpg", ".jpeg"}


# ─── PUBLIC API ────────────────────────────────────────────────────────────────

def analyze_jpeg_ghost(file_path: str) -> dict:
    """
    Runs JPEG ghost analysis on the file.
    Returns result dict compatible with the existing forensics pipeline.
    """
    path = Path(file_path)

    # Skip non-JPEG files gracefully
    if path.suffix.lower() not in SUPPORTED_EXTS:
        return {
            "result":      "SKIPPED",
            "notes":       f"JPEG ghost analysis not applicable for {path.suffix.upper()} files.",
            "ghost_score": None,
            "flags":       [],
        }

    try:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError("Could not read image file.")

        ghost_score, suspicious = _compute_ghost_score(img, str(path))

        if suspicious:
            return {
                "result":      "ANOMALY",
                "ghost_score": round(ghost_score, 6),
                "threshold":   GHOST_THRESHOLD,
                "flags":       ["double_compression_detected"],
                "notes": (
                    f"Double compression detected (score: {ghost_score:.4f}). "
                    f"Image appears to have been edited and re-saved by external software. "
                    f"Consistent with Photoshop, Snapseed, Canva, or similar tools."
                ),
            }
        else:
            return {
                "result":      "CLEAN",
                "ghost_score": round(ghost_score, 6),
                "threshold":   GHOST_THRESHOLD,
                "flags":       [],
                "notes":       "No double compression artifacts detected. Image appears unmodified.",
            }

    except Exception as e:
        return {
            "result":      "ERROR",
            "ghost_score": None,
            "flags":       [],
            "notes":       f"JPEG ghost analysis failed: {str(e)}",
        }


# ─── INTERNALS ─────────────────────────────────────────────────────────────────

def _compute_ghost_score(img: np.ndarray, file_path: str) -> tuple[float, bool]:
    """
    Core ghost detection algorithm.

    For each quality level Q:
      1. Re-compress the image at quality Q → temp buffer
      2. Re-compress the re-compressed version again at Q → double buffer
      3. Compute pixel-wise difference between single and double compression
      4. A double-compressed original will show a dip in this difference
         at the quality level closest to the original compression quality

    The ghost_score is the variance of mean differences across quality levels.
    A high variance means the image responds differently to different quality
    levels — the signature of double compression.
    """
    import tempfile, os

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mean_diffs = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for q in QUALITY_LEVELS:
            single_path = os.path.join(tmpdir, f"single_{q}.jpg")
            double_path = os.path.join(tmpdir, f"double_{q}.jpg")

            # Single compression
            cv2.imwrite(single_path, img, [cv2.IMWRITE_JPEG_QUALITY, q])
            single = cv2.imread(single_path, cv2.IMREAD_GRAYSCALE).astype(np.float32)

            # Double compression
            cv2.imwrite(double_path, single.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, q])
            double = cv2.imread(double_path, cv2.IMREAD_GRAYSCALE).astype(np.float32)

            # Difference between original→single vs single→double
            diff = np.abs(gray - single) - np.abs(single - double)
            mean_diffs.append(float(np.mean(np.abs(diff))))

    # High variance across quality levels = double compression signature
    ghost_score = float(np.var(mean_diffs))
    suspicious  = ghost_score > GHOST_THRESHOLD

    return ghost_score, suspicious
