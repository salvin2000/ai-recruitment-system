"""
Day 10 – Experience Parsing & Relevance Engine
Zecpath AI Recruitment Platform v4 — final
"""

import re
import json
from pathlib import Path
from datetime import datetime, date
from dateutil import relativedelta
from difflib import SequenceMatcher
from parsers.skill_extractor import SkillExtractionEngine


MONTH_MAP = {
    "jan": 1, "january": 1,    "feb": 2, "february": 2,
    "mar": 3, "march": 3,      "apr": 4, "april": 4,
    "may": 5,                   "jun": 6, "june": 6,
    "jul": 7, "july": 7,       "aug": 8, "august": 8,
    "sep": 9, "september": 9,  "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}

EXPERIENCE_HEADINGS = [
    "work experience", "professional experience", "employment history",
    "career history", "experience", "work history", "job experience",
    "internship experience", "industry experience", "relevant experience",
]

STOP_HEADINGS = [
    "education", "educational background", "academic background",
    "qualifications", "certifications", "certificates",
    "certifications & training", "certification",
    "projects", "academic projects", "key projects", "personal projects",
    "achievements", "awards", "accomplishments", "recognition",
    "achievements & awards", "skills", "technical skills",
    "core competencies", "key skills", "languages", "languages known",
    "hobbies", "interests", "hobbies & interests", "references",
    "summary", "objective", "professional summary", "publications",
]

ROLE_KEYWORDS = {
    "software_engineer":  ["software engineer", "software developer", "sde", "swe",
                           "backend developer", "frontend developer", "full stack",
                           "fullstack developer", "web developer", "application developer"],
    "data_scientist":     ["data scientist", "ml engineer", "machine learning engineer",
                           "ai engineer", "deep learning engineer", "research scientist"],
    "data_analyst":       ["data analyst", "business analyst", "analytics engineer",
                           "reporting analyst", "bi analyst", "data engineer"],
    "devops_engineer":    ["devops engineer", "sre", "cloud engineer",
                           "infrastructure engineer", "platform engineer"],
    "product_manager":    ["product manager", "product owner", "pm", "product lead"],
    "ui_ux_designer":     ["ui designer", "ux designer", "ui/ux designer"],
    "management_trainee": ["management trainee", "graduate trainee",
                           "executive trainee", "trainee"],
    "hr_manager":         ["hr manager", "human resources", "hr executive",
                           "talent acquisition", "recruiter"],
    "finance_analyst":    ["finance analyst", "financial analyst", "accounts executive",
                           "chartered accountant", "audit associate"],
}

DATE_PAT = re.compile(
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}'
    r'|\d{4}', re.IGNORECASE
)
DATE_RANGE_PAT = re.compile(
    r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+\d{4}'
    r'|\d{1,2}[/\-]\d{4}|\d{4})'
    r'\s*(?:to|–|-|—|till|until)\s*'
    r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+\d{4}'
    r'|\d{1,2}[/\-]\d{4}|\d{4}|present|current|now|till date|today)',
    re.IGNORECASE
)
TITLE_COMPANY_PAT = re.compile(r'^[A-Za-z].*[-–|].*[A-Za-z]')


class ExperienceParser:
    def __init__(self):
        self.skill_engine = SkillExtractionEngine()
        self.today        = date.today()

    # ── Section Extraction ────────────────────────────────────────────────────

    def extract_experience_section(self, full_text: str) -> str:
        lines, exp_lines, in_exp = full_text.split('\n'), [], False
        for line in lines:
            lower = line.strip().lower().rstrip(':')
            if lower in EXPERIENCE_HEADINGS:
                in_exp = True
                continue
            if lower in STOP_HEADINGS and in_exp:
                break
            if in_exp:
                exp_lines.append(line)
        return '\n'.join(exp_lines).strip()

    # ── Date Parsing ──────────────────────────────────────────────────────────

    def parse_date(self, s: str):
        if not s:
            return None
        s = s.strip().lower()
        if s in ["present", "current", "now", "till date", "today"]:
            return self.today
        for name, num in MONTH_MAP.items():
            m = re.search(rf'\b{name}\b[\s,]+(\d{{4}})', s)
            if m:
                return date(int(m.group(1)), num, 1)
        m = re.search(r'(\d{1,2})[/\-](\d{4})', s)
        if m:
            mo, yr = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                return date(yr, mo, 1)
        m = re.search(r'\b(\d{4})\b', s)
        if m:
            yr = int(m.group(1))
            if 1990 <= yr <= self.today.year + 1:
                return date(yr, 1, 1)
        return None

    def parse_duration(self, start_str, end_str):
        start = self.parse_date(start_str)
        end   = self.parse_date(end_str)
        if not start:
            return None, None, 0
        if not end:
            end = self.today
        d = relativedelta.relativedelta(end, start)
        return start, end, max(d.years * 12 + d.months, 0)

    def extract_date_range(self, text: str):
        m = DATE_RANGE_PAT.search(text)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        m = re.search(r'\b(\d{4})\s*[-–]\s*(\d{4}|present|current)\b',
                      text, re.IGNORECASE)
        if m:
            return m.group(1), m.group(2)
        return None, None

    # ── Title & Company Extraction ────────────────────────────────────────────

    def extract_title_and_company(self, block: str):
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            return "Unknown Role", "Unknown Company"

        # First line should be "Title - Company, City"
        first = lines[0]
        # Remove any trailing date info
        first = re.sub(
            r'\s*\|?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
            r'[\s,]+\d{4}.*$', '', first, flags=re.IGNORECASE
        ).strip()
        first = re.sub(r'\s*\|?\s*\d{4}\s*[-–].*$', '', first).strip()

        m = re.match(r'^(.+?)\s*[-–]\s*(.+)$', first)
        if m:
            title   = m.group(1).strip()
            company = m.group(2).strip()
            # Remove city suffix e.g. ", Bangalore" or ", Mumbai"
            company = re.sub(r',\s*[A-Z][a-z][\w\s]*$', '', company).strip()
            return title, company

        # "Title at Company" format
        m2 = re.match(r'^(.+?)\s+at\s+(.+)$', first, re.IGNORECASE)
        if m2:
            return m2.group(1).strip(), m2.group(2).strip()

        return first, "Unknown Company"

    # ── Block Splitting ───────────────────────────────────────────────────────

    def split_experience_blocks(self, exp_text: str) -> list:
        """
        Split by job title lines (Title - Company format).
        Bullet points and date lines stay attached to their block.
        """
        lines, blocks, current = exp_text.split('\n'), [], []

        for line in lines:
            stripped = line.strip()
            is_title = (
                TITLE_COMPANY_PAT.match(stripped) and
                not stripped.startswith('-') and
                not stripped.startswith('•') and
                not DATE_RANGE_PAT.search(stripped) and
                not re.match(r'^\d{4}', stripped) and
                len(stripped) > 5
            )
            if is_title and current:
                blocks.append('\n'.join(current).strip())
                current = [line]
            else:
                current.append(line)

        if current:
            blocks.append('\n'.join(current).strip())

        return [b for b in blocks if len(b.strip()) > 10]

    # ── Gap & Overlap Detection ───────────────────────────────────────────────

    def detect_gaps(self, roles: list) -> list:
        gaps  = []
        dated = sorted(
            [r for r in roles if r.get("_start") and r.get("_end")],
            key=lambda x: x["_start"]
        )
        for i in range(len(dated) - 1):
            end, start = dated[i]["_end"], dated[i+1]["_start"]
            if start > end:
                d = relativedelta.relativedelta(start, end)
                mo = d.years * 12 + d.months
                if mo >= 2:
                    gaps.append({
                        "after_role":  dated[i]["job_title"],
                        "before_role": dated[i+1]["job_title"],
                        "gap_start":   str(end),
                        "gap_end":     str(start),
                        "gap_months":  mo,
                        "severity": "high" if mo>=12 else "medium" if mo>=6 else "low",
                    })
        return gaps

    def detect_overlaps(self, roles: list) -> list:
        overlaps = []
        dated = sorted(
            [r for r in roles if r.get("_start") and r.get("_end")],
            key=lambda x: x["_start"]
        )
        for i in range(len(dated)):
            for j in range(i+1, len(dated)):
                r1, r2 = dated[i], dated[j]
                os_ = max(r1["_start"], r2["_start"])
                oe_ = min(r1["_end"],   r2["_end"])
                if os_ < oe_:
                    d  = relativedelta.relativedelta(oe_, os_)
                    mo = d.years * 12 + d.months
                    if mo >= 1:
                        overlaps.append({
                            "role_1": r1["job_title"], "role_2": r2["job_title"],
                            "overlap_start": str(os_), "overlap_end": str(oe_),
                            "overlap_months": mo,
                        })
        return overlaps

    # ── Relevance Scoring ─────────────────────────────────────────────────────

    def compute_role_similarity(self, title: str, target: str) -> float:
        jl, tl = title.lower(), target.lower()
        ss = SequenceMatcher(None, jl, tl).ratio()
        ks = 0.0
        for _, kws in ROLE_KEYWORDS.items():
            tm = any(k in jl for k in kws)
            rm = any(k in tl for k in kws)
            if tm and rm:
                ks = 1.0; break
            elif tm or rm:
                ks = max(ks, 0.5)
        return round(max(ss, ks), 2)

    def score_relevance(self, roles: list, jreq: dict) -> dict:
        target     = jreq.get("role_name", "")
        req_skills = [s.lower() for s in jreq.get("required_skills", [])]
        min_exp    = jreq.get("min_experience_years", 0)
        max_exp    = jreq.get("max_experience_years", 99)

        sims       = [self.compute_role_similarity(r.get("job_title",""), target)
                      for r in roles]
        role_sim   = round(max(sims) if sims else 0.0, 2)

        all_sk     = []
        for r in roles:
            all_sk.extend(r.get("skills_mentioned", []))
        all_sk     = [s.lower() for s in all_sk]
        matched    = sum(1 for s in req_skills if s in all_sk)
        skills_m   = round(matched / len(req_skills), 2) if req_skills else 0.5

        tot_mo     = sum(r.get("duration_months", 0) for r in roles)
        tot_yr     = round(tot_mo / 12, 1)
        exp_sc     = (1.0 if tot_yr >= min_exp and tot_yr <= max_exp else
                      0.8 if tot_yr > max_exp else
                      round(tot_yr / max(min_exp, 1), 2))

        score = round((role_sim * 0.40) + (skills_m * 0.40) + (exp_sc * 0.20), 2)
        return {
            "relevance_score":      score,
            "role_similarity":      role_sim,
            "skills_match":         skills_m,
            "experience_score":     exp_sc,
            "total_years":          tot_yr,
            "meets_min_experience": tot_yr >= min_exp,
            "grade": ("A" if score>=0.80 else "B" if score>=0.65 else
                      "C" if score>=0.50 else "D"),
        }

    # ── Main Parse ────────────────────────────────────────────────────────────

    def parse(self, full_text: str, job_requirements: dict = None) -> dict:
        exp_text = self.extract_experience_section(full_text)
        blocks   = self.split_experience_blocks(exp_text) if exp_text else []
        roles    = []

        for block in blocks:
            start_str, end_str           = self.extract_date_range(block)
            start_date, end_date, dur_mo = self.parse_duration(start_str, end_str)
            if not start_str:
                continue

            title, company = self.extract_title_and_company(block)
            sr             = self.skill_engine.extract(block)
            skills         = (sr["skill_summary"]["technical"] +
                              sr["skill_summary"]["business"])

            roles.append({
                "job_title":        title,
                "company":          company,
                "start_date":       str(start_date) if start_date else None,
                "end_date":         str(end_date)   if end_date   else None,
                "start_raw":        start_str,
                "end_raw":          end_str,
                "duration_months":  dur_mo,
                "duration_display": self._format_duration(dur_mo),
                "is_current":       bool(end_str and end_str.lower() in
                                    ["present","current","now","till date","today"]),
                "skills_mentioned": skills,
                "_start":           start_date,
                "_end":             end_date,
            })

        gaps     = self.detect_gaps(roles)
        overlaps = self.detect_overlaps(roles)
        tot_mo   = sum(r["duration_months"] for r in roles)
        tot_yr   = round(tot_mo / 12, 1)
        rel      = self.score_relevance(roles, job_requirements) \
                   if job_requirements else None

        for r in roles:
            r.pop("_start", None); r.pop("_end", None)

        current = next((r["job_title"] for r in roles if r["is_current"]), None)

        return {
            "metadata": {
                "parsed_at":      datetime.now().isoformat(),
                "parser_version": "4.0",
                "total_roles":    len(roles),
                "total_months":   tot_mo,
                "total_years":    tot_yr,
                "total_display":  self._format_duration(tot_mo),
                "has_gaps":       len(gaps) > 0,
                "has_overlaps":   len(overlaps) > 0,
                "current_role":   current,
            },
            "roles": roles, "gaps": gaps, "overlaps": overlaps, "relevance": rel,
        }

    def parse_file(self, file_path: str, job_requirements: dict = None) -> dict:
        text   = Path(file_path).read_text(encoding="utf-8")
        result = self.parse(text, job_requirements)
        result["metadata"]["source_file"] = Path(file_path).name
        return result

    def save_output(self, result: dict, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"✅ Saved → {output_path}")

    def _format_duration(self, months: int) -> str:
        if months == 0:
            return "Unknown"
        y, m = months // 12, months % 12
        if y > 0 and m > 0:
            return f"{y} yr {m} mo"
        return f"{y} yr" if y > 0 else f"{m} mo"
