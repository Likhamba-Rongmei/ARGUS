"""
timestamp.py — Temporal consistency forensics.

Checks:
  1. File system timestamps (created, modified) vs claimed document date
  2. PDF metadata timestamps (CreationDate, ModDate) vs claimed date
  3. Internal consistency: modified < created is physically impossible
  4. Future-dated documents
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pikepdf


def _parse_pdf_date(raw: str) -> Optional[datetime]:
    """Parse PDF date string: D:YYYYMMDDHHmmSSOHH'mm' → datetime (UTC)."""
    if not raw:
        return None
    raw = raw.strip().lstrip("D:").replace("'", "")
    # Normalise timezone offset
    for fmt in (
        "%Y%m%d%H%M%S%z",
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y%m%d",
    ):
        try:
            # Handle +0000 / -0530 style offsets embedded in the string
            candidate = raw[:len(fmt.replace("%z","").replace("%","XX"))]
            dt = datetime.strptime(raw[:19], "%Y%m%d%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _extract_year_from_text(text: str) -> Optional[int]:
    """Pull the first 4-digit year that looks like a calendar year from text."""
    matches = re.findall(r"\b(19[0-9]{2}|20[0-2][0-9])\b", text)
    return int(matches[0]) if matches else None


def check_timestamps(
    file_path: str,
    claimed_date_text: Optional[str] = None,
) -> dict:
    """
    Run all timestamp checks on a file.

    Parameters
    ----------
    file_path       : absolute path to the uploaded file
    claimed_date_text : raw text extracted from the document (used to find
                       the year the document claims to be from)

    Returns
    -------
    {
      "anomalies": [...],   # list of anomaly strings
      "details": {...},     # raw timestamp values for the evidence graph
      "score": float        # 0.0 = clean, 1.0 = maximum suspicion
    }
    """
    anomalies = []
    details = {}
    now = datetime.now(tz=timezone.utc)
    path = Path(file_path)

    # ── 1. File system timestamps ────────────────────────────────────────────
    try:
        stat = path.stat()
        fs_created  = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        fs_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        details["fs_created"]  = fs_created.isoformat()
        details["fs_modified"] = fs_modified.isoformat()

        if fs_modified < fs_created:
            anomalies.append(
                "IMPOSSIBLE: file modified timestamp precedes created timestamp"
            )

        if fs_created > now:
            anomalies.append(
                f"FUTURE-DATED: file created in the future ({fs_created.date()})"
            )

    except OSError as exc:
        details["fs_error"] = str(exc)

    # ── 2. PDF metadata timestamps ───────────────────────────────────────────
    if path.suffix.lower() == ".pdf":
        try:
            with pikepdf.open(str(path)) as pdf:
                meta = pdf.docinfo
                raw_creation = str(meta.get("/CreationDate", ""))
                raw_moddate  = str(meta.get("/ModDate", ""))

            details["pdf_creation_date_raw"] = raw_creation
            details["pdf_mod_date_raw"]       = raw_moddate

            pdf_created  = _parse_pdf_date(raw_creation)
            pdf_modified = _parse_pdf_date(raw_moddate)

            if pdf_created:
                details["pdf_created_parsed"] = pdf_created.isoformat()
                if pdf_created > now:
                    anomalies.append(
                        f"FUTURE-DATED: PDF CreationDate is {pdf_created.date()}"
                    )

            if pdf_modified:
                details["pdf_modified_parsed"] = pdf_modified.isoformat()
                if pdf_modified > now:
                    anomalies.append(
                        f"FUTURE-DATED: PDF ModDate is {pdf_modified.date()}"
                    )

            if pdf_created and pdf_modified and pdf_modified < pdf_created:
                anomalies.append(
                    "IMPOSSIBLE: PDF ModDate precedes CreationDate"
                )

        except Exception as exc:
            details["pdf_timestamp_error"] = str(exc)

    # ── 3. Claimed year vs file system ───────────────────────────────────────
    if claimed_date_text:
        claimed_year = _extract_year_from_text(claimed_date_text)
        details["claimed_year"] = claimed_year

        if claimed_year and "fs_created" in details:
            fs_year = datetime.fromisoformat(details["fs_created"]).year
            if claimed_year > fs_year:
                anomalies.append(
                    f"ANACHRONISM: document claims year {claimed_year} "
                    f"but file was created in {fs_year}"
                )
            if fs_year - claimed_year > 5:
                anomalies.append(
                    f"STALE UPLOAD: document dated {claimed_year} "
                    f"uploaded {fs_year - claimed_year} years later — verify authenticity"
                )

    # ── 4. Score ─────────────────────────────────────────────────────────────
    impossible_count = sum(1 for a in anomalies if "IMPOSSIBLE" in a or "FUTURE" in a)
    score = min(1.0, impossible_count * 0.5 + len(anomalies) * 0.2)

    return {
        "anomalies": anomalies,
        "details":   details,
        "score":     round(score, 3),
    }
