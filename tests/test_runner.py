"""
Zecpath – Day 5 Automated Test Runner
--------------------------------------
Tests the resume extraction engine against all sample files.
Produces a structured log report: output/logs/test_results.json
                                  output/logs/test_report.txt
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Allow importing from engine/
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from extractor import extract_resume, clean_text

# ─────────────────────────── Setup ────────────────────────────────────────

LOG_DIR = Path("output/logs")
CLEAN_DIR = Path("output/cleaned")
SAMPLE_DIR = Path("samples")
LOG_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("zecpath.test_runner")

# ─────────────────────────── Test Cases ───────────────────────────────────

def check_section_detection(text: str, expected_sections: list) -> dict:
    """Verify that known section headings appear in the cleaned text."""
    text_upper = text.upper()
    found = [s for s in expected_sections if s.upper() in text_upper]
    missing = [s for s in expected_sections if s.upper() not in text_upper]
    return {"found": found, "missing": missing, "pass": len(missing) == 0}


def check_no_control_chars(text: str) -> dict:
    """Ensure no garbage control characters remain."""
    import re
    matches = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text)
    return {"pass": len(matches) == 0, "control_chars_found": len(matches)}


def check_no_excessive_blank_lines(text: str) -> dict:
    """Ensure no more than 1 consecutive blank line."""
    import re
    violations = re.findall(r"\n{3,}", text)
    return {"pass": len(violations) == 0, "violation_count": len(violations)}


def check_min_length(text: str, min_chars: int = 200) -> dict:
    """Ensure meaningful content was extracted."""
    return {"pass": len(text) >= min_chars, "length": len(text), "minimum": min_chars}


def check_no_raw_bullets(text: str) -> dict:
    """Ensure Unicode bullets were normalised to dashes."""
    import re
    raw_bullets = re.findall(r"[•●◦▪▫◆◇►▷]", text)
    return {"pass": len(raw_bullets) == 0, "raw_bullets_found": len(raw_bullets)}


# ─────────────────────────── Per-File Test Suite ──────────────────────────

RESUME_TESTS = {
    "resume_mern_arjun.docx": {
        "label": "MERN Stack Developer — Single-column DOCX",
        "expected_sections": ["SKILLS", "EXPERIENCE", "EDUCATION", "CERTIFICATIONS", "SUMMARY"],
        "min_chars": 400
    },
    "resume_uiux_priya.docx": {
        "label": "UI/UX Designer — Table-based DOCX",
        "expected_sections": ["SKILLS", "EXPERIENCE", "EDUCATION", "OBJECTIVE"],
        "min_chars": 300
    },
    "resume_sales_rajan.docx": {
        "label": "Sales Executive — Noisy/decorative DOCX",
        "expected_sections": ["EXPERIENCE", "EDUCATION", "SKILLS"],
        "min_chars": 300
    },
}

UNIT_TESTS = [
    {
        "id": "UT-01",
        "name": "Smart quote normalisation",
        "input": "He\u2019s a developer who \u201cexcels\u201d at Node.js\u2014React too.",
        "expected_substring": "He's",
        "not_expected": ["\u2019", "\u201c", "\u201d", "\u2014"],
    },
    {
        "id": "UT-02",
        "name": "Unicode bullet normalisation",
        "input": "\u2022 Led a team\n\u25cf Delivered on time\n\u27a2 Improved metrics",
        "expected_substring": "- Led a team",
        "not_expected": ["\u2022", "\u25cf", "\u27a2"],
    },
    {
        "id": "UT-03",
        "name": "Decorative divider removal",
        "input": "SKILLS\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\nPython, Java",
        "not_expected": ["\u2500\u2500\u2500"],
        "expected_substring": "Python",
    },
    {
        "id": "UT-04",
        "name": "Section heading uppercasing",
        "input": "experience\nSoftware Engineer at Zecpath",
        "expected_substring": "EXPERIENCE",
        "not_expected": [],
    },
    {
        "id": "UT-05",
        "name": "Excessive blank line collapse",
        "input": "Name\n\n\n\n\nSummary paragraph here.",
        "expected_substring": "Summary",
        "not_expected": ["\n\n\n"],
    },
    {
        "id": "UT-06",
        "name": "Control character removal",
        "input": "Experience\x00\x07\x1fSoftware Engineer",
        "expected_substring": "Experience",
        "not_expected": ["\x00", "\x07", "\x1f"],
    },
]


# ─────────────────────────── Runner ───────────────────────────────────────

def run_unit_tests() -> list:
    results = []
    log.info("\n══ Unit Tests ═══════════════════════════════════════════")

    for tc in UNIT_TESTS:
        cleaned = clean_text(tc["input"])
        passed = True
        notes = []

        if "expected_substring" in tc:
            if tc["expected_substring"] not in cleaned:
                passed = False
                notes.append(f"Expected '{tc['expected_substring']}' not found in output")

        for bad in tc.get("not_expected", []):
            if bad in cleaned:
                passed = False
                notes.append(f"Unwanted string '{repr(bad)}' still present")

        status = "PASS" if passed else "FAIL"
        log.info(f"  [{status}]  {tc['id']}  {tc['name']}")
        if notes:
            for n in notes:
                log.info(f"         ^ {n}")

        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "status": status,
            "notes": notes,
            "cleaned_output": cleaned[:200]
        })

    return results


def run_file_tests() -> list:
    results = []
    log.info("\n══ File Extraction Tests ════════════════════════════════")

    for filename, config in RESUME_TESTS.items():
        filepath = SAMPLE_DIR / filename
        log.info(f"\n  File: {filename}")
        log.info(f"  Label: {config['label']}")

        if not filepath.exists():
            log.warning(f"  [SKIP] File not found: {filepath}")
            results.append({"file": filename, "status": "SKIP", "reason": "File not found"})
            continue

        t0 = time.time()
        result = extract_resume(str(filepath))
        elapsed = round(time.time() - t0, 3)

        text = result.get("text", "")
        checks = {}

        checks["min_length"] = check_min_length(text, config.get("min_chars", 200))
        checks["no_control_chars"] = check_no_control_chars(text)
        checks["no_excessive_blanks"] = check_no_excessive_blank_lines(text)
        checks["no_raw_bullets"] = check_no_raw_bullets(text)
        checks["section_detection"] = check_section_detection(text, config["expected_sections"])

        all_pass = all(v["pass"] for v in checks.values())
        status = "PASS" if all_pass else "FAIL"

        for check_name, check_result in checks.items():
            icon = "✓" if check_result["pass"] else "✗"
            log.info(f"    {icon}  {check_name}: {check_result}")

        if result.get("warnings"):
            for w in result["warnings"]:
                log.info(f"    ⚠  {w}")

        # Save cleaned output
        out_path = CLEAN_DIR / f"{Path(filename).stem}_cleaned.txt"
        out_path.write_text(text, encoding="utf-8")
        log.info(f"    → Cleaned output saved: {out_path.name}  ({result['clean_length']} chars, {elapsed}s)")

        results.append({
            "file": filename,
            "label": config["label"],
            "status": status,
            "elapsed_seconds": elapsed,
            "raw_chars": result.get("raw_length", 0),
            "clean_chars": result.get("clean_length", 0),
            "pages": result.get("pages", "N/A"),
            "warnings": result.get("warnings", []),
            "checks": {k: v for k, v in checks.items()}
        })

    return results


def generate_report(unit_results: list, file_results: list) -> str:
    """Generate a human-readable test report."""
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    unit_pass = sum(1 for r in unit_results if r["status"] == "PASS")
    unit_total = len(unit_results)
    file_pass = sum(1 for r in file_results if r["status"] == "PASS")
    file_total = len([r for r in file_results if r["status"] != "SKIP"])

    lines = [
        "═" * 60,
        "  ZECPATH – Day 5 Test Report",
        "  Resume Text Extraction Engine",
        f"  Generated: {now}",
        "═" * 60,
        "",
        f"  Unit Tests      :  {unit_pass}/{unit_total} passed",
        f"  File Tests      :  {file_pass}/{file_total} passed",
        f"  Overall Status  :  {'ALL PASS' if unit_pass == unit_total and file_pass == file_total else 'FAILURES DETECTED'}",
        "",
        "─" * 60,
        "  UNIT TESTS",
        "─" * 60,
    ]

    for r in unit_results:
        lines.append(f"  [{r['status']}]  {r['id']}  {r['name']}")
        for n in r.get("notes", []):
            lines.append(f"         ^ {n}")

    lines += ["", "─" * 60, "  FILE EXTRACTION TESTS", "─" * 60]

    for r in file_results:
        lines.append(f"\n  [{r['status']}]  {r['file']}")
        lines.append(f"         {r.get('label', '')}")
        if r["status"] == "SKIP":
            lines.append(f"         Reason: {r.get('reason', '')}")
            continue
        lines.append(f"         Raw: {r['raw_chars']} chars  →  Clean: {r['clean_chars']} chars  ({r['elapsed_seconds']}s)")
        for check, val in r.get("checks", {}).items():
            icon = "✓" if val["pass"] else "✗"
            lines.append(f"         {icon}  {check}")
        for w in r.get("warnings", []):
            lines.append(f"         ⚠  {w}")

    lines += ["", "═" * 60, "  End of Report", "═" * 60]
    return "\n".join(lines)


def main():
    log.info("Zecpath Day 5 – Test Runner Starting")
    log.info(f"Timestamp: {datetime.now().isoformat()}")

    unit_results = run_unit_tests()
    file_results = run_file_tests()

    report_text = generate_report(unit_results, file_results)
    report_json = {
        "generated_at": datetime.now().isoformat(),
        "unit_tests": unit_results,
        "file_tests": file_results,
    }

    # Write outputs
    txt_path = LOG_DIR / "test_report.txt"
    json_path = LOG_DIR / "test_results.json"

    txt_path.write_text(report_text, encoding="utf-8")
    json_path.write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    log.info("\n" + report_text)
    log.info(f"\nReport saved: {txt_path}")
    log.info(f"JSON log saved: {json_path}")


if __name__ == "__main__":
    main()
