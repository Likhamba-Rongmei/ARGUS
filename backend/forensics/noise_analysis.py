"""
forensics/noise_analysis.py
Noise Inconsistency Detection for PNG and TIFF.

Real unedited images have consistent sensor noise patterns.
Edited regions (erased text, pasted content, cloned areas) break
this pattern — the noise signature at edit boundaries differs from
the surrounding image. Works regardless of editing software.
"""

import cv2
import numpy as np
from pathlib import Path

SUPPORTED_EXTS   = {".png", ".tiff", ".tif"}
NOISE_THRESHOLD  = 8.0  # Std dev of local noise variance above this = anomaly


def analyze_noise(file_path: str) -> dict:
    path = Path(file_path)

    if path.suffix.lower() not in SUPPORTED_EXTS:
        return {
            "result":      "SKIPPED",
            "notes":       f"Noise analysis not applicable for {path.suffix.upper()} files.",
            "noise_score": None,
            "flags":       [],
        }

    try:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError("Could not read image file.")

        noise_score, suspicious, region_count = _analyze_noise_inconsistency(img)

        if suspicious:
            return {
                "result":      "ANOMALY",
                "noise_score": round(noise_score, 4),
                "threshold":   NOISE_THRESHOLD,
                "flags":       ["noise_inconsistency_detected"],
                "notes": (
                    f"Noise inconsistency detected (score: {noise_score:.2f}). "
                    f"{region_count} suspicious region(s) found with abnormal noise patterns. "
                    f"Consistent with content erasure, text overlay, or region cloning."
                ),
            }
        else:
            return {
                "result":      "CLEAN",
                "noise_score": round(noise_score, 4),
                "threshold":   NOISE_THRESHOLD,
                "flags":       [],
                "notes":       "Noise pattern consistent across image. No editing artifacts detected.",
            }

    except Exception as e:
        return {
            "result":      "ERROR",
            "noise_score": None,
            "flags":       [],
            "notes":       f"Noise analysis failed: {str(e)}",
        }


def _analyze_noise_inconsistency(img: np.ndarray) -> tuple:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Extract noise by subtracting a Gaussian-blurred version
    blurred    = cv2.GaussianBlur(gray, (5, 5), 0)
    noise_map  = gray - blurred

    # Compute local variance in a sliding window
    block_size = 32
    h, w       = noise_map.shape
    local_vars = []

    for y in range(0, h - block_size, block_size // 2):
        for x in range(0, w - block_size, block_size // 2):
            block = noise_map[y:y+block_size, x:x+block_size]
            local_vars.append(float(np.var(block)))

    if not local_vars:
        return 0.0, False, 0

    local_vars  = np.array(local_vars)
    noise_score = float(np.std(local_vars))
    mean_var    = float(np.mean(local_vars))

    # Count regions that deviate significantly from the mean
    threshold_region = mean_var * 2.5
    suspicious_count = int(np.sum(local_vars > threshold_region))

    suspicious = noise_score > NOISE_THRESHOLD and suspicious_count >= 2

    return noise_score, suspicious, suspicious_count
