"""
ocr.py
Document and Product Label OCR & Compliance Parser for ComplyBot.
Extracts text from uploaded product photos, packaging labels, and certificates,
then checks compliance markers (ISI Mark, CM/L number, CRS R-Number, HUID, IS standards).
"""

import os
import re
from typing import Dict, Any, List
from PIL import Image

try:
    import pytesseract
    # Check if standard Windows tesseract path exists if not in PATH
    default_win_tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_win_tess) and not pytesseract.pytesseract.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = default_win_tess
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from image using Tesseract OCR with resilient fallback
    if the external tesseract binary is not installed on the host.
    """
    if not os.path.exists(image_path):
        return ""

    if TESSERACT_AVAILABLE:
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ("L", "RGB"):
                    img = img.convert("RGB")
                text = pytesseract.image_to_string(img)
                return text.strip()
        except Exception:
            # If tesseract binary not found in system PATH, continue to fallback
            pass

    # Fallback: file name heuristics or notification
    base_name = os.path.basename(image_path)
    return f"[Uploaded image: {base_name}]"


def analyze_compliance_text(text: str, filename: str = "") -> Dict[str, Any]:
    """
    Analyzes OCR text or extracted label text against BIS marking rules.
    Identifies:
      - ISI Mark and CM/L license number
      - CRS R-Number
      - Hallmarking HUID and purity
      - Standard numbers (IS XXXX)
    """
    text_clean = text.strip()
    upper = text_clean.upper()

    # 1. Detect Standard Numbers (e.g. IS 16102, IS 9873, IS:374, IS-14543)
    standard_matches = re.findall(r"\bIS\s*[:\-]?\s*(\d{3,5}(?:\s*\([^\)]+\))?)", upper)
    standards_found = [f"IS {s.strip()}" for s in set(standard_matches)]

    # 2. Detect ISI License Number (CM/L - XXXXXXX)
    cml_matches = re.findall(r"(?:CM\s*/\s*L\s*[:\-]?\s*|CML\s*[:\-]?\s*)(\d{7,8})", upper)
    isi_mark_present = "ISI" in upper or len(cml_matches) > 0

    # 3. Detect CRS Registration (R-XXXXXXXX)
    crs_matches = re.findall(r"\b(?:R\s*[:\-]?\s*)(\d{7,8})\b", upper)
    crs_mark_present = "CRS" in upper or "SELF-DECLARATION" in upper or len(crs_matches) > 0

    # 4. Detect Hallmarking Purity & HUID
    huid_candidates = re.findall(r"\b([A-Z0-9]{6})\b", upper)
    # Filter common false positives
    filtered_huids = [h for h in huid_candidates if re.search(r"[A-Z]", h) and re.search(r"\d", h)]
    purity_gold = re.findall(r"\b(24K|22K|20K|18K|14K|999|916|833|750|585)\b", upper)
    purity_silver = re.findall(r"\b(970|925|835|800)\b", upper)
    hallmark_present = "HUID" in upper or "HALLMARK" in upper or len(purity_gold) > 0 or len(purity_silver) > 0

    # Verdict synthesis
    detected_scheme = "General Product / Unspecified"
    findings = []
    missing_items = []
    compliance_score = 0

    if isi_mark_present or any(s in ["IS 374", "IS 9873", "IS 14543"] for s in standards_found):
        detected_scheme = "ISI Mark (Product Certification Scheme I)"
        if isi_mark_present:
            findings.append("✅ ISI Mark / Monogram reference identified.")
            compliance_score += 40
        else:
            missing_items.append("⚠️ Missing official ISI Mark monogram.")

        if cml_matches:
            findings.append(f"✅ Valid License Number format detected: CM/L-{cml_matches[0]}")
            compliance_score += 40
        else:
            missing_items.append("⚠️ Missing mandatory 7-digit CM/L license number beneath the ISI mark.")

        if standards_found:
            findings.append(f"✅ Applicable Standard declared: {', '.join(standards_found)}")
            compliance_score += 20
        else:
            missing_items.append("⚠️ Standard number (e.g. IS 9873 or IS 374) should be clearly marked.")

    elif crs_mark_present or any("16102" in s or "13252" in s for s in standards_found):
        detected_scheme = "Compulsory Registration Scheme (CRS Scheme II)"
        if crs_matches:
            findings.append(f"✅ Valid CRS Registration Number detected: R-{crs_matches[0]}")
            compliance_score += 50
        else:
            missing_items.append("⚠️ Missing mandatory 8-digit CRS Registration Number (R-XXXXXXXX).")

        if "SELF-DECLARATION" in upper or "CONFORMING TO" in upper:
            findings.append("✅ Standard CRS self-declaration statement found.")
            compliance_score += 30
        else:
            missing_items.append("⚠️ Packaging should include: 'Self-Declaration - Conforming to IS XXXXX'.")

        if standards_found:
            findings.append(f"✅ Product Standard declared: {', '.join(standards_found)}")
            compliance_score += 20

    elif hallmark_present:
        detected_scheme = "BIS Hallmarking Scheme"
        if purity_gold or purity_silver:
            p = (purity_gold or purity_silver)[0]
            findings.append(f"✅ Precious metal purity mark identified: {p}")
            compliance_score += 50
        else:
            missing_items.append("⚠️ Missing purity grade / fineness number.")

        if filtered_huids:
            findings.append(f"✅ Hallmark Unique Identification (HUID) code detected: {filtered_huids[0]}")
            compliance_score += 50
        else:
            missing_items.append("⚠️ Missing 6-character laser-engraved HUID code.")

    else:
        findings.append("ℹ️ General packaging or document detected.")
        if standards_found:
            findings.append(f"✅ Referenced Standard: {', '.join(standards_found)}")
            compliance_score = 60
        else:
            missing_items.append("No official BIS mark (ISI, CRS R-Number, or Hallmarking HUID) detected in the provided text.")
            compliance_score = 20

    is_compliant = compliance_score >= 80

    return {
        "detected_scheme": detected_scheme,
        "standards_found": standards_found,
        "isi_mark": bool(isi_mark_present),
        "cml_number": cml_matches[0] if cml_matches else None,
        "crs_number": crs_matches[0] if crs_matches else None,
        "huid": filtered_huids[0] if filtered_huids else None,
        "compliance_score": compliance_score,
        "is_compliant": is_compliant,
        "findings": findings,
        "missing_items": missing_items,
        "raw_text_snippet": text_clean[:300] + ("..." if len(text_clean) > 300 else ""),
    }
