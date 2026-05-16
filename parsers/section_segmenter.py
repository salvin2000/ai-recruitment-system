import re
import json
from pathlib import Path
from datetime import datetime
from enum import Enum

class SectionType(Enum):
    HEADER          = "header"
    SUMMARY         = "summary"
    SKILLS          = "skills"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION       = "education"
    CERTIFICATIONS  = "certifications"
    PROJECTS        = "projects"
    ACHIEVEMENTS    = "achievements"
    LANGUAGES       = "languages"
    HOBBIES         = "hobbies"
    REFERENCES      = "references"
    UNKNOWN         = "unknown"

SECTION_PATTERNS = {
    SectionType.SUMMARY: [r"^\s*(professional\s+)?summary\s*$", r"^\s*profile\s*$", r"^\s*objective\s*$", r"^\s*career\s+objective\s*$", r"^\s*about\s+me\s*$", r"^\s*overview\s*$"],
    SectionType.SKILLS: [r"^\s*(technical\s+)?skills?\s*$", r"^\s*core\s+competencies\s*$", r"^\s*key\s+skills?\s*$", r"^\s*areas?\s+of\s+expertise\s*$", r"^\s*technologies?\s*$", r"^\s*competencies\s*$", r"^\s*expertise\s*$"],
    SectionType.WORK_EXPERIENCE: [r"^\s*work\s+experience\s*$", r"^\s*experience\s*$", r"^\s*professional\s+experience\s*$", r"^\s*employment\s+(history|experience)?\s*$", r"^\s*career\s+history\s*$", r"^\s*internship(s)?\s*$"],
    SectionType.EDUCATION: [r"^\s*education(al)?\s*(background|qualification)?\s*$", r"^\s*academic\s+(background|qualification|details)?\s*$", r"^\s*qualifications?\s*$", r"^\s*academics?\s*$"],
    SectionType.CERTIFICATIONS: [r"^\s*certifications?\s*$", r"^\s*certificates?\s*$", r"^\s*professional\s+certifications?\s*$", r"^\s*certifications?\s+(&|and)\s+training\s*$", r"^\s*training\s*$", r"^\s*courses?\s*$"],
    SectionType.PROJECTS: [r"^\s*projects?\s*$", r"^\s*personal\s+projects?\s*$", r"^\s*academic\s+projects?\s*$", r"^\s*key\s+projects?\s*$", r"^\s*project\s+experience\s*$"],
    SectionType.ACHIEVEMENTS: [r"^\s*achievements?\s*$", r"^\s*accomplishments?\s*$", r"^\s*awards?\s*$", r"^\s*achievements?\s+(&|and)\s+awards?\s*$", r"^\s*awards?\s+(&|and)\s+achievements?\s*$"],
    SectionType.LANGUAGES: [r"^\s*languages?\s*$", r"^\s*language\s+skills?\s*$", r"^\s*languages?\s+known\s*$"],
    SectionType.HOBBIES: [r"^\s*hobbies\s*$", r"^\s*interests?\s*$", r"^\s*hobbies\s+(&|and)\s+interests?\s*$", r"^\s*personal\s+interests?\s*$"],
    SectionType.REFERENCES: [r"^\s*references?\s*$", r"^\s*referees?\s*$"],
}

NLP_SIGNALS = {
    SectionType.WORK_EXPERIENCE: ["worked at", "responsible for", "managed", "developed", "led", "implemented", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "present", "current"],
    SectionType.EDUCATION: ["bachelor", "master", "b.tech", "m.tech", "bca", "mca", "b.com", "mba", "university", "college", "cgpa", "gpa", "percentage", "graduated", "diploma"],
    SectionType.SKILLS: ["python", "java", "javascript", "sql", "html", "css", "react", "machine learning", "excel", "tableau", "power bi", "git", "docker", "aws"],
    SectionType.CERTIFICATIONS: ["certified", "certification", "certificate", "coursera", "udemy", "google", "microsoft", "aws", "issued by"],
    SectionType.PROJECTS: ["built", "developed", "created", "implemented", "github", "tech stack", "technologies used", "frontend", "backend"],
    SectionType.ACHIEVEMENTS: ["award", "winner", "rank", "topper", "scholarship", "first place", "merit", "recognized"],
}

HEADER_PATTERNS = {
    "email":    r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone":    r"(\+?\d[\d\s\-\(\)]{8,14}\d)",
    "linkedin": r"linkedin\.com/in/[\w\-]+",
    "github":   r"github\.com/[\w\-]+",
}

class ResumeSectionSegmenter:
    def __init__(self):
        self.section_patterns = SECTION_PATTERNS
        self.nlp_signals = NLP_SIGNALS

    def preprocess_text(self, text):
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            line = re.sub(r'\s+', ' ', line).strip()
            line = re.sub(r'^[•\-\*▪►]\s*', '', line).strip()
            cleaned.append(line)
        return cleaned

    def is_section_heading(self, line):
        line_lower = line.lower().strip()
        if not line_lower:
            return SectionType.UNKNOWN
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    return section_type
        if len(line_lower) < 40 and not line_lower.endswith('.'):
            if re.match(r'^[A-Z][A-Z\s&/]+$', line.strip()):
                return self._classify_by_keywords(line_lower)
        return SectionType.UNKNOWN

    def _classify_by_keywords(self, text):
        text_lower = text.lower()
        keyword_map = {
            SectionType.SKILLS:          ["skill", "technical", "tool", "technology", "competenc"],
            SectionType.WORK_EXPERIENCE: ["experience", "work", "employment", "career"],
            SectionType.EDUCATION:       ["education", "academic", "qualification", "degree"],
            SectionType.CERTIFICATIONS:  ["certification", "certificate", "training", "course"],
            SectionType.PROJECTS:        ["project", "portfolio"],
            SectionType.ACHIEVEMENTS:    ["achievement", "award", "honor"],
            SectionType.SUMMARY:         ["summary", "profile", "objective", "about"],
            SectionType.LANGUAGES:       ["language"],
            SectionType.HOBBIES:         ["hobby", "interest", "extracurricular"],
        }
        for section_type, keywords in keyword_map.items():
            if any(kw in text_lower for kw in keywords):
                return section_type
        return SectionType.UNKNOWN

    def classify_by_nlp(self, text):
        text_lower = text.lower()
        scores = {section: 0 for section in SectionType}
        for section_type, signals in self.nlp_signals.items():
            for signal in signals:
                scores[section_type] += text_lower.count(signal)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else SectionType.UNKNOWN

    def is_header_block(self, text):
        matches = sum(1 for pattern in HEADER_PATTERNS.values() if re.search(pattern, text, re.IGNORECASE))
        return matches >= 1

    def extract_header_info(self, text):
        header = {"name": "", "email": "", "phone": "", "linkedin": "", "github": ""}
        email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email: header["email"] = email.group()
        phone = re.search(r"(\+?\d[\d\s\-\(\)]{8,14}\d)", text)
        if phone: header["phone"] = phone.group().strip()
        linkedin = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
        if linkedin: header["linkedin"] = linkedin.group()
        github = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
        if github: header["github"] = github.group()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            first = lines[0]
            if not re.search(r"@|linkedin|github|\d{10}", first, re.IGNORECASE):
                header["name"] = first
        return header

    def segment(self, text):
        lines = self.preprocess_text(text)
        sections = []
        current_section = {"type": SectionType.UNKNOWN.value, "heading": "", "content": [], "line_start": 0, "line_end": 0}
        first_block = "\n".join(lines[:8])
        if self.is_header_block(first_block):
            sections.append({"type": SectionType.HEADER.value, "heading": "Header", "content": lines[:8], "line_start": 0, "line_end": 8, "header_info": self.extract_header_info(first_block)})
            start_line = 8
        else:
            start_line = 0
        i = start_line
        while i < len(lines):
            line = lines[i]
            detected_type = self.is_section_heading(line)
            if detected_type != SectionType.UNKNOWN and line:
                if current_section["content"] or current_section["heading"]:
                    content_text = "\n".join(current_section["content"])
                    if current_section["type"] == SectionType.UNKNOWN.value and content_text:
                        nlp_type = self.classify_by_nlp(content_text)
                        if nlp_type != SectionType.UNKNOWN:
                            current_section["type"] = nlp_type.value
                    current_section["line_end"] = i
                    sections.append(current_section)
                current_section = {"type": detected_type.value, "heading": line, "content": [], "line_start": i, "line_end": i}
            else:
                if line:
                    current_section["content"].append(line)
            i += 1
        if current_section["content"] or current_section["heading"]:
            content_text = "\n".join(current_section["content"])
            if current_section["type"] == SectionType.UNKNOWN.value and content_text:
                nlp_type = self.classify_by_nlp(content_text)
                if nlp_type != SectionType.UNKNOWN:
                    current_section["type"] = nlp_type.value
            current_section["line_end"] = len(lines)
            sections.append(current_section)
        return self._build_output(sections, text)

    def _build_output(self, sections, original_text):
        section_counts = {}
        for s in sections:
            t = s["type"]
            section_counts[t] = section_counts.get(t, 0) + 1
        detected = sum(1 for s in sections if s["type"] != SectionType.UNKNOWN.value)
        total = len(sections)
        accuracy = round((detected / total * 100), 1) if total > 0 else 0.0
        return {"metadata": {"segmented_at": datetime.now().isoformat(), "segmenter_version": "1.0", "total_sections": total, "detected_sections": detected, "accuracy": accuracy, "section_types_found": list(section_counts.keys())}, "sections": sections, "section_summary": section_counts}

    def segment_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        result = self.segment(text)
        result["metadata"]["source_file"] = Path(file_path).name
        return result

    def save_output(self, result, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved -> {output_path}")

    def generate_accuracy_report(self, results):
        total_sections = sum(r["metadata"]["total_sections"] for r in results)
        detected_sections = sum(r["metadata"]["detected_sections"] for r in results)
        accuracy_scores = [r["metadata"]["accuracy"] for r in results]
        section_type_counts = {}
        for result in results:
            for section_type in result["metadata"]["section_types_found"]:
                section_type_counts[section_type] = section_type_counts.get(section_type, 0) + 1
        avg_accuracy = round(sum(accuracy_scores) / len(accuracy_scores), 1) if accuracy_scores else 0.0
        return {"report_generated_at": datetime.now().isoformat(), "resumes_processed": len(results), "total_sections": total_sections, "detected_sections": detected_sections, "average_accuracy": avg_accuracy, "accuracy_per_resume": accuracy_scores, "section_frequency": section_type_counts, "most_common_section": max(section_type_counts, key=section_type_counts.get) if section_type_counts else "none"}
