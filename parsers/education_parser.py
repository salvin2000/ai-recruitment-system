"""
Day 11 – Education & Certification Parsing
Zecpath AI Recruitment Platform v2
"""

import re
import json
from pathlib import Path
from datetime import datetime, date
from difflib import SequenceMatcher

from parsers.skill_extractor import SkillExtractionEngine


# ── Degree Normalization Map ──────────────────────────────────────────────────

DEGREE_NORMALIZATION = {
    "b.tech":   ["btech", "b tech", "bachelor of technology",
                 "be", "b.e", "bachelor of engineering"],
    "b.sc":     ["bsc", "b sc", "bachelor of science", "bs", "b.s"],
    "b.com":    ["bcom", "b com", "bachelor of commerce"],
    "b.a":      ["ba", "b a", "bachelor of arts"],
    "b.b.a":    ["bba", "b b a", "bachelor of business administration"],
    "b.ca":     ["bca", "b c a", "bachelor of computer applications"],
    "b.arch":   ["barch", "b arch", "bachelor of architecture"],
    "b.pharm":  ["bpharm", "b pharm", "bachelor of pharmacy"],
    "m.tech":   ["mtech", "m tech", "master of technology",
                 "me", "m.e", "master of engineering"],
    "m.sc":     ["msc", "m sc", "master of science", "ms", "m.s"],
    "m.com":    ["mcom", "m com", "master of commerce"],
    "m.a":      ["ma", "m a", "master of arts"],
    "m.b.a":    ["mba", "m b a", "master of business administration",
                 "pgdm", "post graduate diploma in management"],
    "m.ca":     ["mca", "m c a", "master of computer applications"],
    "ph.d":     ["phd", "ph d", "doctor of philosophy",
                 "doctorate", "doctoral degree"],
    "diploma":  ["polytechnic", "poly", "technical diploma",
                 "pg diploma", "post graduate diploma"],
    "12th":     ["hsc", "higher secondary", "intermediate",
                 "plus two", "+2", "class 12", "grade 12"],
    "10th":     ["ssc", "secondary school", "matriculation",
                 "class 10", "grade 10"],
}

DEGREE_HIERARCHY = {
    "ph.d":   7,
    "m.tech": 6, "m.sc": 6, "m.b.a": 6, "m.com": 6,
    "m.a":    6, "m.ca": 6,
    "b.tech": 5, "b.sc": 5, "b.com": 5, "b.a": 5,
    "b.b.a":  5, "b.ca": 5, "b.arch": 5, "b.pharm": 5,
    "diploma":4, "12th": 3, "10th": 2,
}

FIELD_KEYWORDS = {
    "computer_science": ["computer science", "cs", "cse", "computing",
                         "software engineering", "information technology",
                         "it", "information science", "computer engineering"],
    "data_science":     ["data science", "data analytics", "statistics",
                         "applied mathematics", "machine learning"],
    "electronics":      ["electronics", "electrical", "ece", "eee"],
    "mechanical":       ["mechanical", "mechanical engineering"],
    "civil":            ["civil", "civil engineering"],
    "business":         ["business", "commerce", "management", "finance",
                         "accounting", "economics", "marketing", "mba"],
    "arts_humanities":  ["arts", "humanities", "english", "history",
                         "psychology", "sociology"],
    "medical":          ["medicine", "medical", "pharmacy", "nursing",
                         "biotechnology", "biochemistry"],
    "design":           ["design", "architecture", "visual arts"],
    "law":              ["law", "legal", "llb", "llm"],
}

CERTIFICATION_CATEGORIES = {
    "cloud": {
        "keywords":  ["aws", "azure", "gcp", "google cloud", "cloud",
                      "solutions architect", "cloud practitioner",
                      "devops engineer", "sysops"],
        "providers": ["amazon", "microsoft", "google"],
    },
    "data_science_ml": {
        "keywords":  ["machine learning", "deep learning", "tensorflow",
                      "pytorch", "data science", "nlp", "ai",
                      "neural network", "data analytics professional"],
        "providers": ["coursera", "deeplearning.ai", "fast.ai"],
    },
    "programming": {
        "keywords":  ["python", "java", "javascript", "react", "angular",
                      "node", "django", "flask", "web development",
                      "mobile development", "android", "ios", "nptel"],
        "providers": ["udemy", "coursera", "pluralsight", "codecademy",
                      "nptel"],
    },
    "data_analytics": {
        "keywords":  ["power bi", "tableau", "excel", "sql", "data analysis",
                      "business intelligence", "analytics", "google analytics"],
        "providers": ["microsoft", "tableau", "google"],
    },
    "project_management": {
        "keywords":  ["pmp", "prince2", "agile", "scrum", "kanban",
                      "project management", "six sigma", "lean"],
        "providers": ["pmi", "axelos", "scrum alliance"],
    },
    "cybersecurity": {
        "keywords":  ["security", "cybersecurity", "ethical hacking",
                      "cissp", "ceh", "comptia", "network security"],
        "providers": ["isc2", "ec-council", "comptia"],
    },
    "database": {
        "keywords":  ["mysql", "postgresql", "mongodb", "oracle",
                      "database", "sql server", "dba"],
        "providers": ["oracle", "microsoft", "mongodb"],
    },
    "devops": {
        "keywords":  ["docker", "kubernetes", "jenkins", "ci/cd",
                      "devops", "terraform", "ansible", "linux"],
        "providers": ["linux foundation", "docker", "cncf"],
    },
    "general": {
        "keywords":  [],
        "providers": [],
    },
}

# Education headings — all known variations
EDUCATION_HEADINGS = [
    "education", "educational background", "academic background",
    "academic qualifications", "qualifications", "educational qualifications",
    "academic details", "scholastic details", "education details",
]

# Certification headings — all known variations
CERTIFICATION_HEADINGS = [
    "certifications", "certificates", "professional certifications",
    "certifications and training", "certifications & training",
    "courses", "online courses", "training", "professional development",
    "certifications & awards",
]

# Headings that end education/certification sections
STOP_HEADINGS = [
    "experience", "work experience", "professional experience",
    "employment history", "career history",
    "projects", "academic projects", "key projects",
    "skills", "technical skills", "core competencies",
    "languages", "languages known",
    "hobbies", "interests", "hobbies & interests",
    "references", "summary", "objective", "professional summary",
    "achievements", "awards", "achievements & awards",
    "publications", "volunteering",
]

# Lines that signal actual degree entries
DEGREE_SIGNAL_PATTERN = re.compile(
    r'\b(?:bachelor|master|b\.?tech|m\.?tech|b\.?sc|m\.?sc|'
    r'mba|bca|mca|b\.?com|m\.?com|b\.?a\b|m\.?a\b|'
    r'ph\.?d|phd|diploma|hsc|ssc|'
    r'bachelor of|master of|doctor of)\b',
    re.IGNORECASE
)

# Lines that signal certification entries
CERT_SIGNAL_LINES = re.compile(
    r'\b(?:certified|certificate|certification|course|specialization|'
    r'bootcamp|training|associate|professional|developer|analyst|'
    r'prize|award|nptel|coursera|udemy|google|microsoft|aws|azure)\b',
    re.IGNORECASE
)

# Lines to skip in certification section (not real certs)
SKIP_CERT_LINES = re.compile(
    r'\b(?:hobbies|interests|open source|competitive|member|club|'
    r'hackathon prize|second prize|first prize|languages known|'
    r'english|hindi|native|fluent|professional)\b',
    re.IGNORECASE
)


class EducationParser:
    """
    Parses education and certification sections from resume text.
    Extracts degree type, field of study, institution, graduation year,
    and certifications with relevance categories.
    """

    def __init__(self):
        self.today = date.today()
        self.skill_engine = SkillExtractionEngine()

    # ── Section Extraction ────────────────────────────────────────────────────

    def extract_education_section(self, full_text: str) -> str:
        """Extract only the education section from full resume."""
        lines = full_text.split('\n')
        edu_lines = []
        in_edu = False

        for line in lines:
            lower = line.strip().lower().rstrip(':')
            if lower in EDUCATION_HEADINGS:
                in_edu = True
                continue
            if lower in STOP_HEADINGS and in_edu:
                break
            if in_edu:
                edu_lines.append(line)

        return '\n'.join(edu_lines).strip()

    def extract_certification_section(self, full_text: str) -> str:
        """Extract only the certifications section from full resume."""
        lines = full_text.split('\n')
        cert_lines = []
        in_cert = False

        for line in lines:
            lower = line.strip().lower().rstrip(':')
            if lower in CERTIFICATION_HEADINGS:
                in_cert = True
                continue
            if lower in STOP_HEADINGS and in_cert:
                break
            if in_cert:
                cert_lines.append(line)

        return '\n'.join(cert_lines).strip()

    # ── Degree Normalization ──────────────────────────────────────────────────

    def normalize_degree(self, raw_degree: str) -> str:
        """Normalize a raw degree string to its canonical form."""
        import re as _re
        raw_lower = raw_degree.lower().strip()
        # Check longer/higher degrees first to avoid b.a matching inside m.b.a
        for canonical in sorted(DEGREE_NORMALIZATION.keys(),
                                 key=lambda x: len(x), reverse=True):
            synonyms = DEGREE_NORMALIZATION[canonical]
            if raw_lower == canonical:
                return canonical
            for syn in synonyms:
                # Use exact match or word boundary to avoid partial matches
                if raw_lower == syn:
                    return canonical
                if _re.search(r'\b' + _re.escape(syn) + r'\b', raw_lower):
                    return canonical
        return raw_degree.strip()

    def extract_degree(self, text: str) -> str:
        """Extract and normalize degree type from education block."""
        text_lower = text.lower()
        for canonical in sorted(
            DEGREE_HIERARCHY.keys(),
            key=lambda x: DEGREE_HIERARCHY[x],
            reverse=True
        ):
            synonyms = DEGREE_NORMALIZATION.get(canonical, [])
            all_forms = [canonical] + synonyms
            for form in all_forms:
                if re.search(r'\b' + re.escape(form) + r'\b', text_lower):
                    return canonical
        return "Not specified"

    # ── Field of Study ────────────────────────────────────────────────────────

    def extract_field_of_study(self, text: str) -> str:
        """Extract and normalize field of study."""
        text_lower = text.lower()
        for field, keywords in FIELD_KEYWORDS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    return field.replace('_', ' ').title()
        return "Not specified"

    # ── Institution ───────────────────────────────────────────────────────────

    def extract_institution(self, text: str) -> str:
        """Extract institution name from education block."""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        institution_pat = re.compile(
            r'(?:university|college|institute|school|academy|'
            r'polytechnic|iit|nit|iim|bits)',
            re.IGNORECASE
        )
        for line in lines:
            if institution_pat.search(line):
                # Remove trailing date and pipe
                clean = re.sub(r'\s*\|?\s*\d{4}.*$', '', line).strip()
                clean = re.sub(r',\s*[A-Z][a-z]+\s*$', '', clean).strip()
                if len(clean) >= 4:
                    return clean
        return "Not specified"

    # ── Graduation Year ───────────────────────────────────────────────────────

    def extract_graduation_year(self, text: str) -> str:
        """Extract graduation year from education block."""
        range_match = re.search(r'\b(\d{4})\s*[-–to]+\s*(\d{4})\b', text)
        if range_match:
            return range_match.group(2)
        years = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
        if years:
            return max(years)
        return "Not specified"

    # ── Education Block Splitting ─────────────────────────────────────────────

    def split_education_blocks(self, edu_text: str) -> list:
        """
        Split education section into individual qualification blocks.
        Only include blocks that contain a real degree signal.
        """
        if not edu_text:
            return []

        lines  = edu_text.split('\n')
        blocks = []
        current = []

        for line in lines:
            stripped = line.strip()

            # Empty line = possible block boundary
            if not stripped:
                if current:
                    block_text = '\n'.join(current).strip()
                    # Only keep blocks with a real degree signal
                    if DEGREE_SIGNAL_PATTERN.search(block_text):
                        blocks.append(block_text)
                    current = []
            else:
                # New degree line while already collecting = new block
                if (DEGREE_SIGNAL_PATTERN.search(stripped) and
                        current and
                        DEGREE_SIGNAL_PATTERN.search('\n'.join(current))):
                    block_text = '\n'.join(current).strip()
                    if DEGREE_SIGNAL_PATTERN.search(block_text):
                        blocks.append(block_text)
                    current = [line]
                else:
                    current.append(line)

        # Last block
        if current:
            block_text = '\n'.join(current).strip()
            if DEGREE_SIGNAL_PATTERN.search(block_text):
                blocks.append(block_text)

        return blocks

    # ── Certification Extraction ──────────────────────────────────────────────

    def categorize_certification(self, cert_text: str) -> str:
        """Tag a certification with its relevance category."""
        cert_lower = cert_text.lower()
        for category, data in CERTIFICATION_CATEGORIES.items():
            if category == "general":
                continue
            for kw in data["keywords"]:
                if kw in cert_lower:
                    return category.replace('_', ' ').title()
            for provider in data["providers"]:
                if provider in cert_lower:
                    return category.replace('_', ' ').title()
        return "General"

    def extract_certifications(self, cert_text: str) -> list:
        """
        Extract individual certifications from certification section.
        Filters out non-certification lines like hobbies and achievements.
        """
        if not cert_text:
            return []

        certifications = []
        lines = [l.strip() for l in cert_text.split('\n') if l.strip()]

        for line in lines:
            # Remove bullet points
            line = re.sub(r'^[\-\•\*\+▪►]\s*', '', line).strip()
            if len(line) < 5:
                continue

            # Skip lines that are clearly not certifications
            if SKIP_CERT_LINES.search(line):
                continue

            # Only include lines that look like real certifications
            if not CERT_SIGNAL_LINES.search(line):
                continue

            # Extract year
            year_match = re.search(r'\(?(20\d{2}|19\d{2})\)?', line)
            year = year_match.group(1) if year_match else None

            # Clean name
            name = re.sub(r'\(?(20\d{2}|19\d{2})\)?', '', line).strip()
            name = re.sub(r'[|\-–(),]+$', '', name).strip()

            if len(name) < 4:
                continue

            category = self.categorize_certification(name)

            certifications.append({
                "name":     name,
                "year":     year,
                "category": category,
                "raw":      line,
            })

        return certifications

    # ── Education Relevance Scoring ───────────────────────────────────────────

    def score_education_relevance(
        self, qualifications: list, job_requirements: dict
    ) -> dict:
        """Score how relevant the candidate's education is to the job."""
        min_degree   = job_requirements.get("min_education", "")
        target_field = job_requirements.get("field_of_study", "")
        req_certs    = [c.lower() for c in
                        job_requirements.get("required_certifications", [])]

        # 1. Degree level score (50% weight)
        degree_score = 0.0
        if qualifications:
            candidate_levels = [
                DEGREE_HIERARCHY.get(q.get("degree_normalized", ""), 0)
                for q in qualifications
            ]
            max_level = max(candidate_levels) if candidate_levels else 0
            req_level = DEGREE_HIERARCHY.get(
                self.normalize_degree(min_degree), 0
            )
            degree_score = 1.0 if (req_level == 0 or max_level >= req_level) \
                           else round(max_level / max(req_level, 1), 2)

        # 2. Field relevance score (30% weight)
        field_score = 0.0
        if target_field and qualifications:
            for qual in qualifications:
                field  = qual.get("field_of_study", "").lower()
                target = target_field.lower()
                sim    = SequenceMatcher(None, field, target).ratio()
                field_score = max(field_score, round(sim, 2))
        elif not target_field:
            field_score = 1.0

        # 3. Certification relevance score (20% weight)
        cert_score = 1.0
        if req_certs:
            candidate_certs = [c.get("name", "").lower()
                                for c in job_requirements.get("certifications", [])]
            matched    = sum(1 for rc in req_certs
                             if any(rc in cc for cc in candidate_certs))
            cert_score = round(matched / len(req_certs), 2)

        final_score = round(
            (degree_score * 0.50) + (field_score * 0.30) + (cert_score * 0.20),
            2
        )

        return {
            "relevance_score":      final_score,
            "degree_score":         degree_score,
            "field_score":          field_score,
            "certification_score":  cert_score,
            "grade": (
                "A" if final_score >= 0.80 else
                "B" if final_score >= 0.65 else
                "C" if final_score >= 0.50 else "D"
            ),
            "meets_min_degree": degree_score >= 1.0,
        }

    # ── Main Parse ────────────────────────────────────────────────────────────

    def parse(self, full_text: str, job_requirements: dict = None) -> dict:
        """Main function. Parses education and certifications from resume."""
        edu_text  = self.extract_education_section(full_text)
        cert_text = self.extract_certification_section(full_text)

        # Parse education blocks
        edu_blocks     = self.split_education_blocks(edu_text)
        qualifications = []

        for block in edu_blocks:
            degree_raw        = self.extract_degree(block)
            degree_normalized = self.normalize_degree(degree_raw)
            field             = self.extract_field_of_study(block)
            institution       = self.extract_institution(block)
            grad_year         = self.extract_graduation_year(block)

            qualifications.append({
                "degree_raw":        degree_raw,
                "degree_normalized": degree_normalized,
                "field_of_study":    field,
                "institution":       institution,
                "graduation_year":   grad_year,
                "raw_text":          block[:200],
            })

        # Parse certifications
        certifications = self.extract_certifications(cert_text)

        # Relevance scoring
        relevance = None
        if job_requirements:
            relevance = self.score_education_relevance(
                qualifications, job_requirements
            )

        # Highest degree
        highest_degree = "Not specified"
        if qualifications:
            sorted_quals   = sorted(
                qualifications,
                key=lambda x: DEGREE_HIERARCHY.get(x["degree_normalized"], 0),
                reverse=True
            )
            highest_degree = sorted_quals[0]["degree_normalized"]

        return {
            "metadata": {
                "parsed_at":            datetime.now().isoformat(),
                "parser_version":       "2.0",
                "total_qualifications": len(qualifications),
                "total_certifications": len(certifications),
                "highest_degree":       highest_degree,
            },
            "qualifications":  qualifications,
            "certifications":  certifications,
            "relevance":       relevance,
        }

    def parse_file(self, file_path: str,
                   job_requirements: dict = None) -> dict:
        """Parse education from a resume text file."""
        text   = Path(file_path).read_text(encoding="utf-8")
        result = self.parse(text, job_requirements)
        result["metadata"]["source_file"] = Path(file_path).name
        return result

    def save_output(self, result: dict, output_path: str):
        """Save result to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"✅ Saved → {output_path}")