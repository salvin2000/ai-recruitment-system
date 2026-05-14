import re
import json
import pdfplumber
from pathlib import Path
from datetime import datetime

SKILL_SYNONYMS = {
    "ms office": ["microsoft office", "ms word", "ms excel"],
    "crm": ["crm software", "crm tools", "salesforce", "hubspot"],
    "communication": ["communication skills", "verbal communication"],
    "negotiation": ["negotiation skills"],
    "lead generation": ["lead gen", "prospecting"],
    "market research": ["competitor research", "market analysis"],
    "relationship management": ["client relationship", "customer relationship"],
    "sales": ["sales aptitude", "sales skills"],
    "problem solving": ["problem-solving", "critical thinking"],
}

SECTION_KEYWORDS = {
    "responsibilities": ["responsibilities", "key responsibilities", "duties"],
    "skills": ["required skills", "skills", "technical skills"],
    "qualifications": ["qualifications", "education"],
    "experience": ["experience", "work experience"],
    "salary": ["salary", "compensation", "stipend", "package"],
}

class JDParser:
    def __init__(self):
        self.skill_synonyms = SKILL_SYNONYMS

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def normalize_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[•●▪▸►◦]', '•', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def detect_sections(self, text):
        sections = {
            "full_text": text,
            "responsibilities": "",
            "skills": "",
            "qualifications": "",
            "experience": "",
            "salary": "",
            "description": "",
        }
        lines = text.split('\n')
        current_section = "description"
        for line in lines:
            line_lower = line.lower().strip()
            detected = False
            for section, keywords in SECTION_KEYWORDS.items():
                if any(kw in line_lower for kw in keywords):
                    current_section = section
                    detected = True
                    break
            if not detected:
                sections[current_section] += line + "\n"
        return sections

    def extract_role_name(self, text):
        lines = text.strip().split('\n')
        for line in lines[:3]:
            line = line.strip()
            if len(line) > 3 and len(line) < 80:
                return re.sub(r'^\d+\.\s*', '', line).strip()
        return "Unknown Role"

    def _normalize_skill(self, skill):
        skill_lower = skill.lower().strip()
        for canonical, synonyms in self.skill_synonyms.items():
            if skill_lower == canonical or skill_lower in synonyms:
                return canonical
        return skill_lower

    def extract_skills(self, skills_text, full_text):
        skills = set()
        search_text = skills_text if skills_text else full_text
        # Handle both bullet points and dashes
        bullet_items = re.findall(r'[•\-\*]\s*([^\n•\-\*]+)', search_text)
        for item in bullet_items:
            skill = item.strip().lower()
            if 2 < len(skill) < 60:
                skills.add(self._normalize_skill(skill))
        return sorted(list(skills))

    def extract_experience(self, experience_text, full_text):
        search_text = experience_text if experience_text else full_text
        experience = {"min_years": 0, "max_years": None, "description": "", "fresher_eligible": False}
        if re.search(r'fresh(er)?s?\s*(eligible|welcome|ok)', search_text, re.IGNORECASE):
            experience["fresher_eligible"] = True
            experience["description"] = "Freshers eligible"
        year_range = re.search(r'(\d+)\s*[-to]+\s*(\d+)\s*years?', search_text, re.IGNORECASE)
        if year_range:
            experience["min_years"] = int(year_range.group(1))
            experience["max_years"] = int(year_range.group(2))
            experience["description"] = f"{year_range.group(1)}-{year_range.group(2)} years"
        return experience

    def extract_education(self, qual_text, full_text):
        search_text = qual_text if qual_text else full_text
        education = {"min_degree": "", "preferred_degree": "", "fields_of_study": [], "mba_preferred": False}
        if re.search(r"bachelor'?s?\s*(degree)?|b\.?tech|b\.?sc", search_text, re.IGNORECASE):
            education["min_degree"] = "Bachelor's Degree"
        if re.search(r'mba', search_text, re.IGNORECASE):
            education["mba_preferred"] = True
            education["preferred_degree"] = "MBA"
        return education

    def extract_salary(self, salary_text):
        salary = {"india": "", "international": "", "currency": "", "raw": salary_text.strip() if salary_text else ""}
        if not salary_text:
            return salary
        range_match = re.search(r'\$\s*([\d,\.]+)\s*[-]\s*\$?\s*([\d,\.]+)', salary_text)
        if range_match:
            salary["international"] = f"${range_match.group(1)} - ${range_match.group(2)}"
        return salary

    def parse_jd(self, text, source_file=""):
        sections = self.detect_sections(text)
        jd_profile = {
            "metadata": {"source_file": source_file, "parsed_at": datetime.now().isoformat()},
            "role_name": self.extract_role_name(text),
            "description": sections["description"].strip(),
            "required_skills": self.extract_skills(sections["skills"], text),
            "experience": self.extract_experience(sections["experience"], text),
            "education": self.extract_education(sections["qualifications"], text),
            "salary": self.extract_salary(sections["salary"]),
            "responsibilities": [
                line.strip().lstrip('•-*').strip()
                for line in sections["responsibilities"].split('\n')
                if line.strip() and len(line.strip()) > 5
            ],
            "ai_profile": {}
        }
        jd_profile["ai_profile"] = {
            "role": jd_profile["role_name"],
            "skills_required": jd_profile["required_skills"],
            "min_experience_years": jd_profile["experience"]["min_years"],
            "max_experience_years": jd_profile["experience"]["max_years"],
            "fresher_eligible": jd_profile["experience"]["fresher_eligible"],
            "min_education": jd_profile["education"]["min_degree"],
            "mba_preferred": jd_profile["education"]["mba_preferred"],
            "total_skills_count": len(jd_profile["required_skills"]),
        }
        return jd_profile

    def parse_pdf(self, pdf_path):
        raw_text = self.extract_text_from_pdf(pdf_path)
        jd_blocks = re.split(r'\n(?=\d+\.\s+[A-Z])', raw_text)
        if len(jd_blocks) <= 1:
            return [self.parse_jd(raw_text, Path(pdf_path).name)]
        return [self.parse_jd(block, Path(pdf_path).name) for block in jd_blocks if len(block.strip()) > 100]

    def save_output(self, jd_profiles, output_path):
        output = {"total_jds_parsed": len(jd_profiles), "generated_at": datetime.now().isoformat(), "job_descriptions": jd_profiles}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jd_profiles)} JD profiles to {output_path}")
