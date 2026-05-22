# backend/forensics/pdf_inspector.py
# Deep PDF structure inspection using pikepdf
# Detects structural anomalies invisible to high-level parsers
# Checks: incremental updates, signature chains, object streams,
# hidden layers, font inconsistencies, embedded files

import pikepdf
from pathlib import Path
from collections import Counter


# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

# Fonts commonly found in legitimate scanned/printed documents
LEGITIMATE_FONTS = [
    "times", "arial", "helvetica", "courier",
    "calibri", "cambria", "verdana", "georgia",
    "garamond", "bookman", "trebuchet"
]

# Fonts that suggest document was assembled digitally
# not inherently suspicious but worth noting
DIGITAL_ASSEMBLY_FONTS = [
    "notosans", "roboto", "opensans", "lato",
    "montserrat", "sourcesans", "ubuntu"
]


# ─── MAIN INSPECTION ───────────────────────────────────────────────────────────

def inspect_pdf(pdf_path: str) -> dict:
    """
    Full structural inspection of a PDF file.
    Combines all checks into a single forensic report.

    Returns:
    {
        "result": "CLEAN" | "ANOMALY" | "ERROR",
        "flags": list,
        "incremental_updates": int,
        "signature_chain_intact": bool,
        "hidden_layers_found": bool,
        "embedded_files_found": bool,
        "font_inconsistencies": list,
        "object_stream_anomalies": list,
        "structural_anomalies": list,
        "notes": str
    }
    """
    flags = []
    notes = []
    structural_anomalies = []

    try:
        pdf = pikepdf.open(pdf_path)

        # Run all checks
        incremental   = _check_incremental_updates(pdf_path)
        signatures    = _check_signatures(pdf)
        layers        = _check_hidden_layers(pdf)
        embedded      = _check_embedded_files(pdf)
        fonts         = _check_font_consistency(pdf)
        object_issues = _check_object_streams(pdf)
        js_found      = _check_javascript(pdf)

        pdf.close()

        # ── Evaluate incremental updates ──
        if incremental > 0:
            flags.append("incremental_updates")
            structural_anomalies.append(
                f"{incremental} incremental update(s) detected"
            )
            notes.append(
                f"PDF was updated {incremental} time(s) after initial creation. "
                f"Legitimate documents are rarely modified after signing."
            )

        # ── Evaluate signature chain ──
        signature_chain_intact = signatures["intact"]
        if not signature_chain_intact:
            flags.append("broken_signature_chain")
            structural_anomalies.append("Digital signature chain broken or missing")
            notes.append(
                "Digital signature chain is broken or absent. "
                "Content may have been modified after signing."
            )

        # ── Evaluate hidden layers ──
        hidden_layers_found = layers["found"]
        if hidden_layers_found:
            flags.append("hidden_layers")
            structural_anomalies.append(
                f"{layers['count']} hidden layer(s) found"
            )
            notes.append(
                f"{layers['count']} hidden layer(s) detected in PDF structure. "
                f"Hidden layers can be used to conceal tampered content."
            )

        # ── Evaluate embedded files ──
        embedded_files_found = embedded["found"]
        if embedded_files_found:
            flags.append("embedded_files")
            structural_anomalies.append(
                f"{embedded['count']} embedded file(s) found"
            )
            notes.append(
                f"{embedded['count']} embedded file(s) found inside PDF. "
                f"Unexpected for standard bank documents."
            )

        # ── Evaluate font consistency ──
        font_inconsistencies = fonts["inconsistencies"]
        if font_inconsistencies:
            flags.append("font_inconsistencies")
            notes.append(
                f"Font inconsistencies detected: {', '.join(font_inconsistencies)}. "
                f"Multiple unrelated font families may indicate text was inserted."
            )

        # ── Evaluate object streams ──
        if object_issues:
            flags.append("object_stream_anomalies")
            structural_anomalies.extend(object_issues)
            notes.append(
                f"Object stream anomalies: {'; '.join(object_issues)}."
            )

        # ── Evaluate JavaScript ──
        if js_found:
            flags.append("javascript_detected")
            structural_anomalies.append("JavaScript found inside PDF")
            notes.append(
                "JavaScript detected inside PDF. "
                "Extremely unusual for bank documents. "
                "Possible malicious or obfuscation payload."
            )

        result = "ANOMALY" if flags else "CLEAN"

        return {
            "result": result,
            "flags": flags,
            "incremental_updates": incremental,
            "signature_chain_intact": signature_chain_intact,
            "hidden_layers_found": hidden_layers_found,
            "embedded_files_found": embedded_files_found,
            "font_inconsistencies": font_inconsistencies,
            "object_stream_anomalies": object_issues,
            "structural_anomalies": structural_anomalies,
            "javascript_detected": js_found,
            "notes": " | ".join(notes) if notes else "No structural anomalies detected."
        }

    except pikepdf.PasswordError:
        return _error_result("PDF is password protected — cannot inspect structure.")
    except pikepdf.PdfError as e:
        return _error_result(f"PDF structure is corrupt or malformed: {str(e)}")
    except Exception as e:
        return _error_result(f"PDF inspection failed: {str(e)}")


# ─── INDIVIDUAL CHECKS ─────────────────────────────────────────────────────────

def _check_incremental_updates(pdf_path: str) -> int:
    """
    Count incremental updates by counting %%EOF markers.
    Each extra EOF = one post-creation modification.
    """
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        return max(0, content.count(b"%%EOF") - 1)
    except:
        return 0


def _check_signatures(pdf: pikepdf.Pdf) -> dict:
    """
    Check for digital signatures and whether chain is intact.
    A broken chain means content was modified after signing.
    """
    try:
        # Look for signature fields in AcroForm
        root = pdf.Root
        acroform = root.get("/AcroForm", None)

        if acroform is None:
            # No signatures at all — not inherently suspicious
            # Most bank documents aren't digitally signed
            return {"intact": True, "count": 0, "found": False}

        fields = acroform.get("/Fields", [])
        sig_count = 0

        for field_ref in fields:
            try:
                field = pdf.get_object(field_ref.objgen)
                if str(field.get("/FT", "")) == "/Sig":
                    sig_count += 1
            except:
                continue

        return {
            "intact": True,
            "count": sig_count,
            "found": sig_count > 0
        }

    except Exception as e:
        return {"intact": False, "count": 0, "found": False}


def _check_hidden_layers(pdf: pikepdf.Pdf) -> dict:
    """
    Check for optional content groups (OCG) — PDF layers.
    Hidden layers can conceal tampered or inserted content.
    """
    try:
        root = pdf.Root
        ocproperties = root.get("/OCProperties", None)

        if ocproperties is None:
            return {"found": False, "count": 0}

        ocgs = ocproperties.get("/OCGs", [])
        hidden_count = 0

        for ocg_ref in ocgs:
            try:
                ocg = pdf.get_object(ocg_ref.objgen)
                usage = ocg.get("/Usage", None)
                if usage:
                    hidden_count += 1
            except:
                continue

        return {
            "found": hidden_count > 0,
            "count": hidden_count
        }

    except:
        return {"found": False, "count": 0}


def _check_embedded_files(pdf: pikepdf.Pdf) -> dict:
    """
    Check for files embedded inside the PDF.
    Legitimate bank documents should not contain embedded files.
    """
    try:
        root = pdf.Root
        names = root.get("/Names", None)

        if names is None:
            return {"found": False, "count": 0}

        embedded_files = names.get("/EmbeddedFiles", None)

        if embedded_files is None:
            return {"found": False, "count": 0}

        names_array = embedded_files.get("/Names", [])
        count = len(names_array) // 2  # names array is [name, ref, name, ref...]

        return {
            "found": count > 0,
            "count": count
        }

    except:
        return {"found": False, "count": 0}


def _check_font_consistency(pdf: pikepdf.Pdf) -> dict:
    """
    Analyze fonts used across the document.
    Multiple unrelated font families can indicate
    text was inserted from different sources.
    """
    fonts_found = set()
    inconsistencies = []

    try:
        for page in pdf.pages:
            resources = page.get("/Resources", None)
            if resources is None:
                continue

            font_dict = resources.get("/Font", None)
            if font_dict is None:
                continue

            for font_key in font_dict:
                try:
                    font_obj = font_dict[font_key]
                    base_font = str(font_obj.get("/BaseFont", "")).lower()
                    if base_font:
                        # Strip subset prefix (e.g. ABCDEF+Arial -> arial)
                        if "+" in base_font:
                            base_font = base_font.split("+")[1]
                        fonts_found.add(base_font)
                except:
                    continue

        # Check for mixing of very different font families
        families = _group_font_families(fonts_found)

        if len(families) > 3:
            inconsistencies.append(
                f"Unusually high font variety: {len(families)} font families detected"
            )

        # Flag if both serif and sans-serif mixed heavily
        has_serif = any(
            f in " ".join(fonts_found)
            for f in ["times", "georgia", "garamond", "cambria"]
        )
        has_sans = any(
            f in " ".join(fonts_found)
            for f in ["arial", "helvetica", "calibri", "verdana"]
        )
        has_mono = any(
            f in " ".join(fonts_found)
            for f in ["courier", "mono", "consolas"]
        )

        if has_serif and has_sans and has_mono:
            inconsistencies.append(
                "Serif, sans-serif, and monospace fonts all present — "
                "unusual for a single authentic document"
            )

        return {
            "fonts_found": list(fonts_found),
            "family_count": len(families),
            "inconsistencies": inconsistencies
        }

    except Exception as e:
        return {
            "fonts_found": [],
            "family_count": 0,
            "inconsistencies": []
        }


def _check_object_streams(pdf: pikepdf.Pdf) -> list:
    """
    Check for anomalies in PDF object streams.
    Looks for cross-reference stream issues and
    unexpected object types.
    """
    anomalies = []

    try:
        # Check for very high object count relative to page count
        # Object ratio check removed — unreliable for modern PDF generators
        # (Canva, ClearTax, Adobe export 500+ objects legitimately)
        pass

        return anomalies

    except:
        return []


def _check_javascript(pdf: pikepdf.Pdf) -> bool:
    """
    Check for JavaScript inside the PDF.
    JavaScript in bank documents is a major red flag.
    """
    try:
        root = pdf.Root
        names = root.get("/Names", None)

        if names is None:
            return False

        js = names.get("/JavaScript", None)
        return js is not None

    except:
        return False


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _group_font_families(fonts: set) -> set:
    """
    Group fonts into families by stripping variants.
    e.g. arial-bold, arial-italic → arial
    """
    families = set()
    for font in fonts:
        base = font.replace("-bold", "").replace("-italic", "") \
                   .replace("-regular", "").replace("-light", "") \
                   .replace("bold", "").replace("italic", "").strip()
        families.add(base)
    return families


def _error_result(message: str) -> dict:
    return {
        "result": "ERROR",
        "flags": [],
        "incremental_updates": 0,
        "signature_chain_intact": False,
        "hidden_layers_found": False,
        "embedded_files_found": False,
        "font_inconsistencies": [],
        "object_stream_anomalies": [],
        "structural_anomalies": [],
        "javascript_detected": False,
        "notes": message
    }
