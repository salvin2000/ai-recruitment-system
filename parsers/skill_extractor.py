"""
Day 9 – Skill Extraction Engine
Zecpath AI Recruitment Platform

Extracts technical and non-technical skills from resumes using
NLP-based entity recognition with confidence scoring.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from parsers.skill_dictionary import (
    MASTER_SKILL_DICT,
    SKILL_CATEGORIES,
    SKILL_STACKS,
)


# ── Confidence Score Weights ──────────────────────────────────────────────────

CONFIDENCE_WEIGHTS = {
    "exact_match":      1.00,   # Exact skill name match
    "synonym_match":    0.90,   # Matched via synonym
    "stack_match":      0.85,   # Matched via skill stack
    "fuzzy_match":      0.75,   # Fuzzy/spelling variation match
    "context_match":    0.70,   # Matched via context signals
    "partial_match":    0.60,   # Partial name match
}

# ── Context Signal Patterns ───────────────────────────────────────────────────

CONTEXT_PATTERNS = [
    r"experience\s+(?:in|with)\s+([\w\s\+\#\.]+)",
    r"proficient\s+(?:in|with)\s+([\w\s\+\#\.]+)",
    r"knowledge\s+of\s+([\w\s\+\#\.]+)",
    r"skilled\s+(?:in|at)\s+([\w\s\+\#\.]+)",
    r"expertise\s+(?:in|with)\s+([\w\s\+\#\.]+)",
    r"working\s+knowledge\s+of\s+([\w\s\+\#\.]+)",
    r"hands.on\s+(?:experience\s+(?:in|with)\s+)?([\w\s\+\#\.]+)",
    r"(?:used|using|worked\s+with|working\s+with)\s+([\w\s\+\#\.]+)",
    r"developed\s+(?:using|with|in)\s+([\w\s\+\#\.]+)",
    r"built\s+(?:using|with|in)\s+([\w\s\+\#\.]+)",
    r"tech\s+stack\s*:\s*([\w\s\+\#\.,]+)",
    r"technologies\s*:\s*([\w\s\+\#\.,]+)",
    r"tools\s*:\s*([\w\s\+\#\.,]+)",
    r"languages\s*:\s*([\w\s\+\#\.,]+)",
    r"frameworks\s*:\s*([\w\s\+\#\.,]+)",
]


class SkillExtractionEngine:
    """
    Extracts skills from resume text using rule-based + NLP approaches
    with confidence scoring, synonym handling, and deduplication.
    """

    def __init__(self):
        self.master_dict = MASTER_SKILL_DICT
        self.skill_categories = SKILL_CATEGORIES
        self.skill_stacks = SKILL_STACKS
        self._build_flat_lookup()

    def _build_flat_lookup(self):
        """
        Build a flat lookup dictionary for fast skill matching.
        Maps every skill name and synonym → (canonical_name, category)
        """
        self.flat_lookup = {}

        for category, skills in self.master_dict.items():
            for canonical, synonyms in skills.items():
                # Add canonical name
                self.flat_lookup[canonical.lower()] = (canonical, category)
                # Add all synonyms
                for synonym in synonyms:
                    self.flat_lookup[synonym.lower()] = (canonical, category)

    # ── Text Preprocessing ────────────────────────────────────────────────────

    def preprocess(self, text: str) -> str:
        """Clean and normalize resume text."""
        # Lowercase
        text = text.lower()
        # Normalize separators
        text = re.sub(r'[•\-\*▪►,;|/]', ' ', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # ── Exact & Synonym Matching ──────────────────────────────────────────────

    def exact_match(self, text: str) -> list:
        """
        Find exact skill matches in text.

        Returns:
            list of (canonical_name, category, confidence, match_type)
        """
        found = []
        text_lower = text.lower()

        # Sort by length (longest first) to match longer phrases first
        sorted_skills = sorted(
            self.flat_lookup.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        matched_spans = set()

        for skill_text, (canonical, category) in sorted_skills:
            # Use word boundary matching
            pattern = r'\b' + re.escape(skill_text) + r'\b'
            for match in re.finditer(pattern, text_lower):
                span = (match.start(), match.end())
                # Check if this span overlaps with an already matched span
                overlap = any(
                    span[0] < ms[1] and span[1] > ms[0]
                    for ms in matched_spans
                )
                if not overlap:
                    # Determine if exact or synonym match
                    is_exact = skill_text == canonical.lower()
                    confidence = (
                        CONFIDENCE_WEIGHTS["exact_match"] if is_exact
                        else CONFIDENCE_WEIGHTS["synonym_match"]
                    )
                    match_type = "exact" if is_exact else "synonym"
                    found.append((canonical, category, confidence, match_type))
                    matched_spans.add(span)

        return found

    # ── Fuzzy Matching ────────────────────────────────────────────────────────

    def fuzzy_match(self, text: str, threshold: float = 0.85) -> list:
        """
        Find skills with spelling variations using fuzzy matching.

        Args:
            text: Resume text
            threshold: Minimum similarity ratio (0-1)

        Returns:
            list of (canonical_name, category, confidence, match_type)
        """
        found = []
        words = re.findall(r'\b\w[\w\+\#\.]*\b', text.lower())

        # Check single words and bigrams
        candidates = words.copy()
        for i in range(len(words) - 1):
            candidates.append(f"{words[i]} {words[i+1]}")

        for candidate in candidates:
            if len(candidate) < 3:
                continue

            best_ratio = 0
            best_match = None

            for skill_text, (canonical, category) in self.flat_lookup.items():
                ratio = SequenceMatcher(None, candidate, skill_text).ratio()
                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    best_match = (canonical, category)

            if best_match and best_ratio >= threshold:
                canonical, category = best_match
                confidence = CONFIDENCE_WEIGHTS["fuzzy_match"] * best_ratio
                found.append((canonical, category, round(confidence, 2), "fuzzy"))

        return found

    # ── Context-Based Extraction ──────────────────────────────────────────────

    def context_match(self, text: str) -> list:
        """
        Extract skills mentioned in context patterns like
        'experience in Python' or 'tech stack: React, Node'.

        Returns:
            list of (canonical_name, category, confidence, match_type)
        """
        found = []
        text_lower = text.lower()

        for pattern in CONTEXT_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                # Split by comma or space for multiple skills
                tokens = re.split(r'[,\s]+', match.strip())
                for token in tokens:
                    token = token.strip()
                    if token in self.flat_lookup:
                        canonical, category = self.flat_lookup[token]
                        found.append((
                            canonical, category,
                            CONFIDENCE_WEIGHTS["context_match"],
                            "context"
                        ))

        return found

    # ── Skill Stack Expansion ─────────────────────────────────────────────────

    def expand_skill_stacks(self, text: str) -> list:
        """
        Detect skill stacks (MERN, MEAN, etc.) and expand them
        to individual skills.

        Returns:
            list of (canonical_name, category, confidence, match_type)
        """
        found = []
        text_lower = text.lower()

        for stack_name, component_skills in self.skill_stacks.items():
            if stack_name.lower() in text_lower:
                for skill in component_skills:
                    if skill in self.flat_lookup:
                        canonical, category = self.flat_lookup[skill]
                        found.append((
                            canonical, category,
                            CONFIDENCE_WEIGHTS["stack_match"],
                            f"stack:{stack_name}"
                        ))

        return found

    # ── Confidence Scoring ────────────────────────────────────────────────────

    def calculate_final_confidence(
        self,
        skill_name: str,
        occurrences: list,
        text: str
    ) -> float:
        """
        Calculate final confidence score for a skill based on:
        - Match type (exact, synonym, fuzzy, context, stack)
        - Number of occurrences
        - Context quality

        Args:
            skill_name: Canonical skill name
            occurrences: List of (confidence, match_type) tuples
            text: Original text for context check

        Returns:
            float: Final confidence score (0.0 - 1.0)
        """
        if not occurrences:
            return 0.0

        # Base confidence: highest match confidence
        base_confidence = max(conf for conf, _ in occurrences)

        # Occurrence bonus: more occurrences = higher confidence
        occurrence_count = len(occurrences)
        occurrence_bonus = min(0.05 * (occurrence_count - 1), 0.15)

        # Context bonus: skill mentioned in skills section
        context_bonus = 0.0
        text_lower = text.lower()
        skill_lower = skill_name.lower()

        # Check if skill appears near section headings
        skills_section_pattern = r'skills?.*?' + re.escape(skill_lower)
        if re.search(skills_section_pattern, text_lower, re.DOTALL):
            context_bonus = 0.05

        final = min(base_confidence + occurrence_bonus + context_bonus, 1.0)
        return round(final, 2)

    # ── Main Extraction ───────────────────────────────────────────────────────

    def extract(self, text: str) -> dict:
        """
        Main skill extraction function.

        Args:
            text: Resume text

        Returns:
            dict: Structured skill output with confidence scores
        """
        preprocessed = self.preprocess(text)

        # Collect all matches from all methods
        all_matches = []
        all_matches.extend(self.exact_match(preprocessed))
        all_matches.extend(self.context_match(preprocessed))
        all_matches.extend(self.expand_skill_stacks(preprocessed))

        # Group by canonical skill name
        skill_groups = {}
        for canonical, category, confidence, match_type in all_matches:
            if canonical not in skill_groups:
                skill_groups[canonical] = {
                    "category":     category,
                    "occurrences":  [],
                }
            skill_groups[canonical]["occurrences"].append((confidence, match_type))

        # Build final skill list with confidence scores
        extracted_skills = []
        for canonical, data in skill_groups.items():
            final_confidence = self.calculate_final_confidence(
                canonical,
                data["occurrences"],
                preprocessed
            )

            # Get best match type
            best_match = max(data["occurrences"], key=lambda x: x[0])

            extracted_skills.append({
                "skill":        canonical,
                "category":     self.skill_categories.get(data["category"], "Technical"),
                "sub_category": data["category"],
                "confidence":   final_confidence,
                "match_type":   best_match[1],
                "occurrences":  len(data["occurrences"]),
            })

        # Sort by confidence (highest first)
        extracted_skills.sort(key=lambda x: x["confidence"], reverse=True)

        # Deduplicate
        extracted_skills = self._deduplicate(extracted_skills)

        # Group by category
        grouped = self._group_by_category(extracted_skills)

        return {
            "metadata": {
                "extracted_at":     datetime.now().isoformat(),
                "engine_version":   "1.0",
                "total_skills":     len(extracted_skills),
                "high_confidence":  sum(1 for s in extracted_skills if s["confidence"] >= 0.85),
                "medium_confidence":sum(1 for s in extracted_skills if 0.70 <= s["confidence"] < 0.85),
                "low_confidence":   sum(1 for s in extracted_skills if s["confidence"] < 0.70),
            },
            "skills":           extracted_skills,
            "skills_by_category": grouped,
            "skill_summary": {
                "technical":    [s["skill"] for s in extracted_skills if s["category"] == "Technical"],
                "business":     [s["skill"] for s in extracted_skills if s["category"] == "Business"],
                "soft":         [s["skill"] for s in extracted_skills if s["category"] == "Soft"],
                "creative":     [s["skill"] for s in extracted_skills if s["category"] == "Creative"],
            }
        }

    def _deduplicate(self, skills: list) -> list:
        """Remove duplicate skills keeping highest confidence."""
        seen = {}
        for skill in skills:
            name = skill["skill"].lower()
            if name not in seen or skill["confidence"] > seen[name]["confidence"]:
                seen[name] = skill
        return list(seen.values())

    def _group_by_category(self, skills: list) -> dict:
        """Group skills by their category."""
        grouped = {}
        for skill in skills:
            cat = skill["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({
                "skill":      skill["skill"],
                "confidence": skill["confidence"],
                "match_type": skill["match_type"],
            })
        return grouped

    # ── File Processing ───────────────────────────────────────────────────────

    def extract_from_file(self, file_path: str) -> dict:
        """Extract skills from a resume text file."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        result = self.extract(text)
        result["metadata"]["source_file"] = Path(file_path).name
        return result

    def save_output(self, result: dict, output_path: str):
        """Save extraction result to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved → {output_path}")
