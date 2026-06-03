"""
Day 12 – Semantic Matching Engine
Zecpath AI Recruitment Platform

Converts resumes and job descriptions into embeddings and measures
deep semantic similarity beyond simple keyword matching.
"""

import re
import json
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ── TF-IDF Based Embedding Engine ────────────────────────────────────────────
# Uses TF-IDF vectors as lightweight semantic representations
# No external API or GPU required — works fully offline

class TFIDFEmbedder:
    """
    Builds TF-IDF vector representations of text.
    These vectors capture the importance of terms relative to
    a corpus, enabling meaningful semantic comparison.
    """

    def __init__(self):
        self.vocabulary    = {}       # word -> index
        self.idf_scores    = {}       # word -> IDF score
        self.corpus_docs   = []       # all documents seen
        self.is_fitted     = False

    def _tokenize(self, text: str) -> list:
        """Tokenize text into cleaned lowercase tokens."""
        text  = text.lower()
        text  = re.sub(r'[^a-z0-9\s\+\#\.]', ' ', text)
        tokens= re.findall(r'\b[a-z][a-z0-9\+\#\.]{1,}\b', text)
        # Remove common stopwords
        stops = {
            'the','and','for','are','was','were','has','have','had',
            'this','that','with','from','will','can','been','but',
            'not','all','also','they','their','our','its','into',
            'more','about','than','when','which','there','an','in',
            'of','to','is','it','be','by','on','as','at','or','we',
            'you','my','do','if','up','so','no','us','he','she',
        }
        return [t for t in tokens if t not in stops and len(t) >= 2]

    def fit(self, documents: list):
        """
        Fit the embedder on a corpus of documents.
        Computes IDF scores for all terms in the corpus.
        """
        self.corpus_docs = documents
        N = len(documents)

        # Count document frequency for each term
        df = defaultdict(int)
        tokenized_docs = []
        for doc in documents:
            tokens = set(self._tokenize(doc))
            tokenized_docs.append(tokens)
            for token in tokens:
                df[token] += 1

        # Build vocabulary and compute IDF
        self.vocabulary = {}
        self.idf_scores = {}
        for i, (word, freq) in enumerate(sorted(df.items())):
            self.vocabulary[word] = i
            # Smooth IDF: log((N+1)/(df+1)) + 1
            self.idf_scores[word] = math.log((N + 1) / (freq + 1)) + 1

        self.is_fitted = True
        return self

    def transform(self, text: str) -> dict:
        """
        Convert text into a TF-IDF weighted vector.
        Returns sparse dict representation: {word: tfidf_score}
        """
        if not self.is_fitted:
            raise RuntimeError("Embedder must be fitted before transform.")

        tokens = self._tokenize(text)
        if not tokens:
            return {}

        # Compute TF (term frequency)
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1

        # Compute TF-IDF vector
        vector = {}
        for word, count in tf.items():
            if word in self.idf_scores:
                tf_score  = count / len(tokens)
                idf_score = self.idf_scores[word]
                vector[word] = round(tf_score * idf_score, 6)

        return vector

    def fit_transform(self, documents: list) -> list:
        """Fit on corpus and transform all documents."""
        self.fit(documents)
        return [self.transform(doc) for doc in documents]


# ── Similarity Functions ──────────────────────────────────────────────────────

def cosine_similarity(vec1: dict, vec2: dict) -> float:
    """
    Compute cosine similarity between two sparse TF-IDF vectors.
    Returns value between 0.0 (no similarity) and 1.0 (identical).
    """
    if not vec1 or not vec2:
        return 0.0

    # Dot product
    dot_product = sum(
        vec1.get(word, 0) * vec2.get(word, 0)
        for word in set(vec1) | set(vec2)
    )

    # Magnitudes
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return round(dot_product / (mag1 * mag2), 4)


def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Compute Jaccard similarity between two texts based on shared terms.
    Good for measuring vocabulary overlap between skills lists.
    """
    tokens1 = set(re.findall(r'\b[a-z][a-z0-9\+\#\.]{1,}\b',
                              text1.lower()))
    tokens2 = set(re.findall(r'\b[a-z][a-z0-9\+\#\.]{1,}\b',
                              text2.lower()))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union        = tokens1 | tokens2

    return round(len(intersection) / len(union), 4)


# ── Background Corpus ────────────────────────────────────────────────────────
# These documents provide corpus diversity so IDF scores are meaningful
# even when only a few resumes are being processed

BACKGROUND_CORPUS = [
    "marketing sales crm customers revenue growth lead generation brand management",
    "cooking chef restaurant kitchen food hospitality hotel management",
    "accounting finance audit tax budget financial statements balance sheet",
    "nursing medical doctor hospital patient healthcare pharmacy clinical",
    "teaching education school curriculum lesson plan classroom students",
    "law legal contracts litigation compliance regulatory attorney paralegal",
    "civil mechanical electrical construction infrastructure engineering project",
    "graphic design creative photography video editing animation adobe photoshop",
    "human resources recruitment payroll performance appraisal training development",
    "supply chain logistics warehouse inventory shipping procurement operations",
]

# ── Similarity Thresholds ─────────────────────────────────────────────────────

SIMILARITY_THRESHOLDS = {
    # Thresholds calibrated for TF-IDF cosine similarity scores.
    # TF-IDF naturally produces lower scores than neural embeddings.
    # A score of 0.35+ in TF-IDF represents a strong semantic match.
    "skills": {
        "high":   0.35,   # Strong skill match — many shared technical terms
        "medium": 0.18,   # Moderate skill overlap — some shared terms
        "low":    0.05,   # Weak skill match — few shared terms
    },
    "experience": {
        "high":   0.25,   # Strong experience relevance
        "medium": 0.12,   # Some relevant experience
        "low":    0.05,   # Limited relevant experience
    },
    "projects": {
        "high":   0.18,   # Projects closely related to job domain
        "medium": 0.08,   # Some project relevance
        "low":    0.03,   # Low project relevance
    },
    "overall": {
        "high":   0.28,   # Excellent overall match — recommend interview
        "medium": 0.15,   # Good match — consider for interview
        "low":    0.08,   # Weak match — likely reject
    }
}

# ── Weights for overall score ─────────────────────────────────────────────────

COMPONENT_WEIGHTS = {
    "skills":     0.45,   # Skills are most important
    "experience": 0.35,   # Experience second
    "projects":   0.20,   # Projects third
}


# ── Semantic Matching Engine ──────────────────────────────────────────────────

class SemanticMatchingEngine:
    """
    Converts resumes and job descriptions into TF-IDF embeddings
    and measures semantic similarity across skills, experience,
    and project descriptions.
    """

    def __init__(self):
        self.embedder   = TFIDFEmbedder()
        self.thresholds = SIMILARITY_THRESHOLDS
        self.weights    = COMPONENT_WEIGHTS
        self._corpus    = []
        self._fitted    = False

    # ── Text Extraction Helpers ───────────────────────────────────────────────

    def extract_skills_text(self, resume_text: str) -> str:
        """Extract skills section text from resume."""
        skill_headings = [
            "technical skills", "skills", "core competencies",
            "key skills", "technologies", "expertise",
        ]
        stop_headings = [
            "experience", "work experience", "education",
            "projects", "certifications", "achievements",
            "summary", "objective",
        ]
        return self._extract_section(resume_text, skill_headings, stop_headings)

    def extract_experience_text(self, resume_text: str) -> str:
        """Extract experience section text from resume."""
        exp_headings = [
            "work experience", "professional experience",
            "employment history", "experience", "career history",
        ]
        stop_headings = [
            "education", "projects", "certifications",
            "achievements", "skills", "technical skills",
            "languages", "hobbies",
        ]
        return self._extract_section(resume_text, exp_headings, stop_headings)

    def extract_projects_text(self, resume_text: str) -> str:
        """Extract projects section text from resume."""
        proj_headings = [
            "projects", "academic projects", "key projects",
            "personal projects", "portfolio",
        ]
        stop_headings = [
            "education", "certifications", "achievements",
            "skills", "languages", "hobbies", "references",
        ]
        return self._extract_section(resume_text, proj_headings, stop_headings)

    def _extract_section(self, text: str,
                          start_headings: list,
                          stop_headings: list) -> str:
        """Generic section extractor."""
        lines    = text.split('\n')
        result   = []
        in_sect  = False

        for line in lines:
            lower = line.strip().lower().rstrip(':')
            if lower in start_headings:
                in_sect = True
                continue
            if lower in stop_headings and in_sect:
                break
            if in_sect and line.strip():
                result.append(line.strip())

        return ' '.join(result)

    def extract_jd_skills(self, jd_text: str) -> str:
        """Extract required skills from job description."""
        patterns = [
            r'required skills?[:\s]+([^\n]+(?:\n[^\n]+){0,5})',
            r'skills?[:\s]+([^\n]+(?:\n[^\n]+){0,3})',
            r'technical skills?[:\s]+([^\n]+(?:\n[^\n]+){0,3})',
        ]
        for pat in patterns:
            m = re.search(pat, jd_text, re.IGNORECASE)
            if m:
                return m.group(1)
        return jd_text[:500]

    def extract_jd_responsibilities(self, jd_text: str) -> str:
        """Extract responsibilities from job description."""
        patterns = [
            r'responsibilities[:\s]+([^\n]+(?:\n[^\n]+){0,8})',
            r'key responsibilities[:\s]+([^\n]+(?:\n[^\n]+){0,8})',
            r'what you.ll do[:\s]+([^\n]+(?:\n[^\n]+){0,8})',
        ]
        for pat in patterns:
            m = re.search(pat, jd_text, re.IGNORECASE)
            if m:
                return m.group(1)
        return jd_text[:800]

    # ── Corpus Building ───────────────────────────────────────────────────────

    def build_corpus(self, resume_texts: list, jd_texts: list):
        """
        Build and fit the TF-IDF embedder on all available text.
        Includes background corpus documents to ensure IDF scores
        are meaningful even with small resume collections.
        """
        self._corpus = resume_texts + jd_texts + BACKGROUND_CORPUS
        self.embedder.fit(self._corpus)
        self._fitted = True

    # ── Component Similarity ──────────────────────────────────────────────────

    def compute_skills_similarity(self,
                                   resume_text: str,
                                   jd_text: str) -> dict:
        """Compute semantic similarity between resume skills and JD skills."""
        resume_skills = self.extract_skills_text(resume_text)
        jd_skills     = self.extract_jd_skills(jd_text)

        if not resume_skills:
            resume_skills = resume_text[:500]
        if not jd_skills:
            jd_skills = jd_text[:500]

        # TF-IDF cosine similarity
        vec_r    = self.embedder.transform(resume_skills)
        vec_j    = self.embedder.transform(jd_skills)
        cosine   = cosine_similarity(vec_r, vec_j)

        # Jaccard for exact term overlap
        jaccard  = jaccard_similarity(resume_skills, jd_skills)

        # Combined score — average of cosine and jaccard
        combined = round((cosine * 0.60 + jaccard * 0.40), 4)

        return {
            "score":   combined,
            "cosine":  cosine,
            "jaccard": jaccard,
            "level":   self._classify(combined, "skills"),
        }

    def compute_experience_similarity(self,
                                       resume_text: str,
                                       jd_text: str) -> dict:
        """Compute semantic similarity between resume experience and JD."""
        resume_exp = self.extract_experience_text(resume_text)
        jd_resp    = self.extract_jd_responsibilities(jd_text)

        if not resume_exp:
            resume_exp = resume_text[:800]
        if not jd_resp:
            jd_resp = jd_text[:800]

        vec_r    = self.embedder.transform(resume_exp)
        vec_j    = self.embedder.transform(jd_resp)
        cosine   = cosine_similarity(vec_r, vec_j)
        jaccard  = jaccard_similarity(resume_exp, jd_resp)
        combined = round((cosine * 0.70 + jaccard * 0.30), 4)

        return {
            "score":   combined,
            "cosine":  cosine,
            "jaccard": jaccard,
            "level":   self._classify(combined, "experience"),
        }

    def compute_projects_similarity(self,
                                     resume_text: str,
                                     jd_text: str) -> dict:
        """Compute semantic similarity between resume projects and JD."""
        resume_proj = self.extract_projects_text(resume_text)
        jd_full     = jd_text[:1000]

        if not resume_proj:
            return {
                "score": 0.0, "cosine": 0.0,
                "jaccard": 0.0, "level": "low",
                "note": "No projects section found"
            }

        vec_r    = self.embedder.transform(resume_proj)
        vec_j    = self.embedder.transform(jd_full)
        cosine   = cosine_similarity(vec_r, vec_j)
        jaccard  = jaccard_similarity(resume_proj, jd_full)
        combined = round((cosine * 0.65 + jaccard * 0.35), 4)

        return {
            "score":   combined,
            "cosine":  cosine,
            "jaccard": jaccard,
            "level":   self._classify(combined, "projects"),
        }

    def _classify(self, score: float, component: str) -> str:
        """Classify a similarity score as high, medium, or low."""
        thresholds = self.thresholds.get(component, self.thresholds["overall"])
        if score >= thresholds["high"]:
            return "high"
        elif score >= thresholds["medium"]:
            return "medium"
        else:
            return "low"

    # ── Overall Match Score ───────────────────────────────────────────────────

    def compute_overall_match(self,
                               skills_sim: dict,
                               experience_sim: dict,
                               projects_sim: dict) -> dict:
        """Compute weighted overall semantic match score."""
        overall = round(
            skills_sim["score"]     * self.weights["skills"] +
            experience_sim["score"] * self.weights["experience"] +
            projects_sim["score"]   * self.weights["projects"],
            4
        )

        return {
            "score": overall,
            "level": self._classify(overall, "overall"),
            "grade": (
                "A" if overall >= 0.28 else
                "B" if overall >= 0.15 else
                "C" if overall >= 0.08 else "D"
            ),
            "recommendation": (
                "Strong Match \u2014 Recommend for Interview" if overall >= 0.28 else
                "Good Match \u2014 Consider for Interview"    if overall >= 0.15 else
                "Moderate Match \u2014 Review Manually"       if overall >= 0.08 else
                "Weak Match \u2014 Not Recommended"
            ),
            "weights_used": self.weights,
        }

    # ── Main Match Function ───────────────────────────────────────────────────

    def match(self,
              resume_text: str,
              jd_text: str,
              resume_name: str = "",
              jd_name: str = "") -> dict:
        """
        Main function. Computes full semantic match between
        a resume and a job description.
        """
        if not self._fitted:
            self.build_corpus([resume_text], [jd_text])

        skills_sim     = self.compute_skills_similarity(resume_text, jd_text)
        experience_sim = self.compute_experience_similarity(resume_text, jd_text)
        projects_sim   = self.compute_projects_similarity(resume_text, jd_text)
        overall        = self.compute_overall_match(
            skills_sim, experience_sim, projects_sim
        )

        return {
            "metadata": {
                "matched_at":     datetime.now().isoformat(),
                "engine_version": "1.0",
                "resume_file":    resume_name,
                "jd_file":        jd_name,
                "embedding_type": "TF-IDF + Cosine + Jaccard",
            },
            "similarity_scores": {
                "skills":     skills_sim,
                "experience": experience_sim,
                "projects":   projects_sim,
            },
            "overall_match": overall,
        }

    def match_batch(self,
                    resume_texts: list,
                    jd_text: str,
                    resume_names: list = None,
                    jd_name: str = "") -> list:
        """
        Match multiple resumes against one job description.
        Builds corpus from all texts first for consistent IDF scores.
        """
        # Build corpus from all documents
        self.build_corpus(resume_texts, [jd_text])

        resume_names = resume_names or [f"resume_{i}" for i in
                                         range(len(resume_texts))]
        results = []
        for text, name in zip(resume_texts, resume_names):
            result = self.match(text, jd_text, name, jd_name)
            results.append(result)

        return results

    def save_output(self, result, output_path: str):
        """Save match result to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\u2705 Saved \u2192 {output_path}")

    def generate_accuracy_report(self, results: list) -> dict:
        """
        Generate a matching accuracy report across all resume-JD pairs.
        Shows score distribution, average scores, and recommendations.
        """
        total = len(results)
        if total == 0:
            return {}

        grades     = {"A": 0, "B": 0, "C": 0, "D": 0}
        levels     = {"high": 0, "medium": 0, "low": 0}
        avg_skills = avg_exp = avg_proj = avg_overall = 0.0

        for r in results:
            grade = r["overall_match"]["grade"]
            level = r["overall_match"]["level"]
            grades[grade] += 1
            levels[level] += 1
            avg_skills  += r["similarity_scores"]["skills"]["score"]
            avg_exp     += r["similarity_scores"]["experience"]["score"]
            avg_proj    += r["similarity_scores"]["projects"]["score"]
            avg_overall += r["overall_match"]["score"]

        return {
            "report_generated_at": datetime.now().isoformat(),
            "total_resumes":       total,
            "grade_distribution":  {
                g: {"count": c, "percentage": round(c/total*100, 1)}
                for g, c in grades.items()
            },
            "level_distribution":  levels,
            "average_scores": {
                "skills":     round(avg_skills  / total, 4),
                "experience": round(avg_exp     / total, 4),
                "projects":   round(avg_proj    / total, 4),
                "overall":    round(avg_overall / total, 4),
            },
            "thresholds_used": SIMILARITY_THRESHOLDS,
            "weights_used":    COMPONENT_WEIGHTS,
        }