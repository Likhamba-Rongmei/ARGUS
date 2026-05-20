# backend/forensics/ela.py
# Error Level Analysis — detects re-saved or composited image regions
# Core forensic check in Pipeline 1
# Works on both images and PDF pages converted to images

import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import os
from pathlib import Path


# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

ELA_QUALITY = 90          # JPEG re-save quality for ELA
ELA_SCALE = 15            # Amplification scale for difference visibility
ANOMALY_THRESHOLD = 5.0  # Mean ELA intensity above this = anomaly flagged


# ─── CORE ELA ALGORITHM ────────────────────────────────────────────────────────

def run_ela_on_image(image_path: str) -> dict:
    """
    Run Error Level Analysis on a single image file.

    How ELA works:
    1. Re-save the image at a known JPEG quality level
    2. Compute pixel-level difference between original and re-saved
    3. Amplify the difference for visibility
    4. High-difference regions = areas that were previously saved
       at a different quality = evidence of tampering or compositing

    Returns anomaly score + heatmap path.
    """
    try:
        original = Image.open(image_path).convert("RGB")

        # Step 1 — Re-save at known quality
        temp_path = f"/tmp/argus_ela_resaved.jpg"
        original.save(temp_path, "JPEG", quality=ELA_QUALITY)

        # Step 2 — Reload re-saved version
        resaved = Image.open(temp_path).convert("RGB")

        # Step 3 — Compute absolute difference
        original_arr = np.array(original, dtype=np.float32)
        resaved_arr  = np.array(resaved,  dtype=np.float32)
        diff         = np.abs(original_arr - resaved_arr)

        # Step 4 — Amplify for visibility
        amplified = np.clip(diff * ELA_SCALE, 0, 255).astype(np.uint8)

        # Step 5 — Compute anomaly score (mean intensity of amplified diff)
        anomaly_score = float(np.mean(amplified))

        # Step 6 — Save heatmap
        heatmap_path = _save_heatmap(amplified, image_path)

        # Step 7 — Identify flagged regions
        flagged_regions = _find_flagged_regions(amplified)

        # Cleanup
        os.remove(temp_path)

        is_anomaly = anomaly_score > ANOMALY_THRESHOLD

        return {
            "result": "ANOMALY" if is_anomaly else "CLEAN",
            "anomaly_score": round(anomaly_score, 4),
            "threshold": ANOMALY_THRESHOLD,
            "flagged_regions": flagged_regions,
            "heatmap_path": heatmap_path,
            "notes": _generate_notes(anomaly_score, flagged_regions)
        }

    except Exception as e:
        return {
            "result": "ERROR",
            "anomaly_score": 0.0,
            "threshold": ANOMALY_THRESHOLD,
            "flagged_regions": [],
            "heatmap_path": None,
            "notes": f"ELA failed: {str(e)}"
        }


# ─── PDF SUPPORT ───────────────────────────────────────────────────────────────

def run_ela_on_pdf(pdf_path: str) -> dict:
    """
    Run ELA on a PDF by converting each page to image first.
    Merges results across all pages.
    Most relevant for scanned document PDFs.
    """
    try:
        doc = fitz.open(pdf_path)
        page_results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better ELA resolution
            pix = page.get_pixmap(matrix=mat)
            temp_img_path = f"/tmp/argus_ela_page_{page_num}.png"
            pix.save(temp_img_path)

            result = run_ela_on_image(temp_img_path)
            result["page"] = page_num + 1
            page_results.append(result)

            os.remove(temp_img_path)

        doc.close()

        return _merge_page_results(page_results)

    except Exception as e:
        return {
            "result": "ERROR",
            "anomaly_score": 0.0,
            "flagged_regions": [],
            "heatmap_path": None,
            "notes": f"PDF ELA failed: {str(e)}",
            "page_results": []
        }


# ─── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def run_ela(file_path: str) -> dict:
    """
    Universal ELA entry point.
    Detects file type and routes correctly.

    Returns:
    {
        "result": "CLEAN" | "ANOMALY" | "ERROR",
        "anomaly_score": float,
        "threshold": float,
        "flagged_regions": list,
        "heatmap_path": str or None,
        "notes": str
    }
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return run_ela_on_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]:
        return run_ela_on_image(file_path)
    else:
        return {
            "result": "ERROR",
            "anomaly_score": 0.0,
            "flagged_regions": [],
            "heatmap_path": None,
            "notes": f"Unsupported file type for ELA: {ext}"
        }


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _save_heatmap(amplified: np.ndarray, original_path: str) -> str:
    """
    Save the ELA heatmap as a colored image for dashboard display.
    Applies a heat colormap so anomalous regions appear red/yellow.
    """
    # Convert to grayscale for colormap application
    gray = cv2.cvtColor(amplified, cv2.COLOR_RGB2GRAY)

    # Apply heat colormap — red = high anomaly, blue = clean
    heatmap = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    # Save next to original with _ela suffix
    base = Path(original_path).stem
    heatmap_path = f"/tmp/argus_{base}_ela_heatmap.png"
    cv2.imwrite(heatmap_path, heatmap)

    return heatmap_path


def _find_flagged_regions(amplified: np.ndarray) -> list:
    """
    Identify specific image regions with high ELA values.
    Returns bounding boxes of suspicious areas.
    """
    gray = cv2.cvtColor(amplified, cv2.COLOR_RGB2GRAY)

    # Threshold — only keep high-intensity pixels
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

    # Find contours of flagged regions
    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # ignore tiny noise regions
            x, y, w, h = cv2.boundingRect(contour)
            regions.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "area": int(area)
            })

    # Sort by area descending — largest suspicious region first
    regions.sort(key=lambda r: r["area"], reverse=True)

    return regions[:5]  # return top 5 flagged regions max


def _generate_notes(anomaly_score: float, flagged_regions: list) -> str:
    """
    Generate human-readable forensic notes for the dashboard.
    """
    if anomaly_score <= ANOMALY_THRESHOLD:
        return "No re-save artifacts detected. Document appears unmodified."

    region_count = len(flagged_regions)
    if region_count == 0:
        return f"Elevated ELA score ({anomaly_score:.2f}) detected but no specific regions isolated."
    elif region_count == 1:
        return (
            f"ELA anomaly detected (score: {anomaly_score:.2f}). "
            f"1 suspicious region found — possible localized tampering or compositing."
        )
    else:
        return (
            f"ELA anomaly detected (score: {anomaly_score:.2f}). "
            f"{region_count} suspicious regions found — strong indicator of image manipulation."
        )


def _merge_page_results(page_results: list) -> dict:
    """
    Merge ELA results across multiple PDF pages.
    Uses the worst-case page as the overall verdict.
    """
    if not page_results:
        return {
            "result": "ERROR",
            "anomaly_score": 0.0,
            "flagged_regions": [],
            "heatmap_path": None,
            "notes": "No pages processed",
            "page_results": []
        }

    # Overall result is ANOMALY if any page is anomalous
    any_anomaly = any(r["result"] == "ANOMALY" for r in page_results)
    max_score   = max(r["anomaly_score"] for r in page_results)
    worst_page  = max(page_results, key=lambda r: r["anomaly_score"])

    return {
        "result": "ANOMALY" if any_anomaly else "CLEAN",
        "anomaly_score": round(max_score, 4),
        "threshold": ANOMALY_THRESHOLD,
        "flagged_regions": worst_page.get("flagged_regions", []),
        "heatmap_path": worst_page.get("heatmap_path"),
        "notes": worst_page.get("notes", ""),
        "page_results": page_results
    }
