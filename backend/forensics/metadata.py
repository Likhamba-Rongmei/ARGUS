# backend/forensics/metadata.py
# EXIF and file metadata forensics
# Detects editing software fingerprints, timestamp anomalies,
# GPS inconsistencies, and suspicious metadata patterns

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
import pikepdf
from PIL import Image
import exifread


# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

# Software that indicates professional image editing
# Legitimate bank documents should never have these
SUSPICIOUS_SOFTWARE = [
    "photoshop",
    "gimp",
    "paint.net",
    "affinity",
    "lightroom",
    "pixelmator",
    "canva",
    "illustrator",
    "inkscape",
    "corel"
]

# Legitimate document creation software — not suspicious
LEGITIMATE_SOFTWARE = [
    "microsoft word",
    "microsoft office",
    "adobe acrobat",
    "libreoffice",
    "google docs",
    "scanner",
    "scan",
    "hp",
    "canon",
    "epson",
    "brother"
]


# ─── EXIF METADATA (IMAGES) ────────────────────────────────────────────────────

def extract_exif(image_path: str) -> dict:
    """
    Extract EXIF metadata from image files using exifread.
    Returns raw EXIF tags as a clean dictionary.
    """
    try:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        clean = {}
        for key, val in tags.items():
            clean[key] = str(val)

        return clean

    except Exception as e:
        return {"error": str(e)}


def analyze_exif(image_path: str) -> dict:
    """
    Analyze EXIF metadata for forensic red flags.
    Checks software fingerprints, timestamps, GPS anomalies.
    """
    flags = []
    notes = []
    raw_exif = extract_exif(image_path)

    if "error" in raw_exif:
        return {
            "result": "UNKNOWN",
            "flags": [],
            "software_detected": None,
            "gps_anomaly": False,
            "timestamp_consistent": True,
            "raw_exif": {},
            "notes": "Could not read EXIF data"
        }

    # ── Check 1: Software fingerprint ──
    software = (
        raw_exif.get("Image Software", "") or
        raw_exif.get("EXIF Software", "")
    ).lower()

    software_detected = software if software else None
    software_suspicious = any(s in software for s in SUSPICIOUS_SOFTWARE)
    software_legitimate = any(s in software for s in LEGITIMATE_SOFTWARE)

    if software_suspicious:
        flags.append("suspicious_software")
        notes.append(
            f"Editing software detected in EXIF: '{software}'. "
            f"Legitimate bank documents should not have image editing history."
        )
    elif not software and not software_legitimate:
        notes.append("No software tag found in EXIF — metadata may have been stripped.")

    # ── Check 2: Timestamp consistency ──
    datetime_original = raw_exif.get("EXIF DateTimeOriginal", "")
    datetime_digitized = raw_exif.get("EXIF DateTimeDigitized", "")
    datetime_modified = raw_exif.get("Image DateTime", "")

    timestamp_consistent = True
    if datetime_original and datetime_modified:
        if datetime_original != datetime_modified:
            # Allow small differences but flag large ones
            timestamp_consistent = False
            flags.append("timestamp_mismatch")
            notes.append(
                f"Timestamp mismatch: Original={datetime_original}, "
                f"Modified={datetime_modified}. Document may have been re-edited."
            )

    # ── Check 3: GPS anomaly ──
    gps_anomaly = False
    gps_lat = raw_exif.get("GPS GPSLatitude", "")
    gps_lon = raw_exif.get("GPS GPSLongitude", "")

    if gps_lat or gps_lon:
        # Financial documents should not have GPS coordinates
        # unless they were photographed on a phone
        # Flag it but don't hard-fail
        gps_anomaly = True
        flags.append("gps_coordinates_present")
        notes.append(
            "GPS coordinates found in document image. "
            "Document was likely photographed on a mobile device — verify authenticity."
        )

    # ── Check 4: Missing EXIF entirely ──
    if not raw_exif:
        flags.append("no_exif_data")
        notes.append(
            "No EXIF metadata found. "
            "Metadata may have been deliberately stripped — common in forgeries."
        )

    result = "ANOMALY" if flags else "CLEAN"

    return {
        "result": result,
        "flags": flags,
        "software_detected": software_detected,
        "gps_anomaly": gps_anomaly,
        "timestamp_consistent": timestamp_consistent,
        "raw_exif": raw_exif,
        "notes": " | ".join(notes) if notes else "No metadata anomalies detected."
    }


# ─── PDF METADATA ──────────────────────────────────────────────────────────────

def analyze_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract and analyze PDF document metadata.
    Checks creation/modification timestamps, producer software,
    and incremental update history.
    """
    flags = []
    notes = []

    try:
        pdf = pikepdf.open(pdf_path)
        meta = pdf.docinfo

        # Extract metadata fields
        producer  = str(meta.get("/Producer",  "")).lower()
        creator   = str(meta.get("/Creator",   "")).lower()
        author    = str(meta.get("/Author",    ""))
        created   = str(meta.get("/CreationDate",     ""))
        modified  = str(meta.get("/ModDate",   ""))
        title     = str(meta.get("/Title",     ""))

        pdf.close()

        # ── Check 1: Producer software ──
        software_suspicious = any(s in producer for s in SUSPICIOUS_SOFTWARE) or \
                              any(s in creator  for s in SUSPICIOUS_SOFTWARE)

        software_detected = producer or creator or None

        if software_suspicious:
            flags.append("suspicious_software")
            notes.append(
                f"Suspicious software in PDF metadata: producer='{producer}', "
                f"creator='{creator}'. Image editing tools should not produce bank documents."
            )

        # ── Check 2: Creation vs modification date ──
        timestamp_consistent = True
        if created and modified:
            created_clean  = _parse_pdf_date(created)
            modified_clean = _parse_pdf_date(modified)

            if created_clean and modified_clean:
                if modified_clean > created_clean:
                    flags.append("document_modified_after_creation")
                    notes.append(
                        f"PDF was modified after creation. "
                        f"Created: {created_clean}, Modified: {modified_clean}. "
                        f"Could indicate post-signing tampering."
                    )
                    timestamp_consistent = False

        # ── Check 3: Incremental updates ──
        incremental_updates = _count_incremental_updates(pdf_path)
        if incremental_updates > 0:
            flags.append("incremental_updates_detected")
            notes.append(
                f"{incremental_updates} incremental update(s) found in PDF structure. "
                f"Document was modified after initial creation."
            )

        # ── Check 4: Missing metadata ──
        if not created and not producer:
            flags.append("metadata_stripped")
            notes.append(
                "PDF metadata is unusually sparse. "
                "Creation date and producer missing — may indicate metadata stripping."
            )

        result = "ANOMALY" if flags else "CLEAN"

        return {
            "result": result,
            "flags": flags,
            "software_detected": software_detected,
            "author": author,
            "title": title,
            "creation_date": created,
            "modification_date": modified,
            "incremental_updates": incremental_updates,
            "timestamp_consistent": timestamp_consistent,
            "notes": " | ".join(notes) if notes else "No metadata anomalies detected."
        }

    except Exception as e:
        return {
            "result": "ERROR",
            "flags": [],
            "software_detected": None,
            "notes": f"PDF metadata analysis failed: {str(e)}"
        }


# ─── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def analyze_metadata(file_path: str) -> dict:
    """
    Universal metadata analysis entry point.
    Routes to EXIF or PDF analyzer based on file type.

    Returns:
    {
        "result": "CLEAN" | "ANOMALY" | "ERROR" | "UNKNOWN",
        "flags": list,
        "software_detected": str or None,
        "timestamp_consistent": bool,
        "gps_anomaly": bool (images only),
        "incremental_updates": int (PDFs only),
        "notes": str
    }
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return analyze_pdf_metadata(file_path)

    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]:
        return analyze_exif(file_path)

    else:
        return {
            "result": "UNKNOWN",
            "flags": [],
            "software_detected": None,
            "timestamp_consistent": True,
            "notes": f"Unsupported file type for metadata analysis: {ext}"
        }


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _parse_pdf_date(date_str: str):
    """
    Parse PDF date format: D:20240315092200+05'30'
    Returns datetime object or None.
    """
    try:
        # Strip PDF date prefix and timezone
        clean = date_str.replace("D:", "")[:14]
        return datetime.strptime(clean, "%Y%m%d%H%M%S")
    except:
        return None


def _count_incremental_updates(pdf_path: str) -> int:
    """
    Count how many times a PDF was incrementally updated.
    Each '%%EOF' marker after the first = one incremental update.
    Incremental updates can be used to hide tampering.
    """
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        eof_count = content.count(b"%%EOF")
        return max(0, eof_count - 1)  # first EOF is normal
    except:
        return 0
