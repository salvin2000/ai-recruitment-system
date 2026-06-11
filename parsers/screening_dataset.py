"""
Day 22 – HR Screening Dataset Creation
Zecpath AI Recruitment Platform

Creates a structured, AI-ready question bank for automated screening calls.
Questions are categorized, tagged with metadata, and designed as reusable
conversation objects ready for the AI screening engine.
"""

import json
from datetime import datetime
from typing import Optional


# ── Question Categories ───────────────────────────────────────────────────────

QUESTION_CATEGORIES = {
    "introduction":   "Opening questions to establish rapport and confirm candidate identity",
    "education":      "Questions about academic qualifications and certifications",
    "experience":     "Questions about work history, roles, and responsibilities",
    "skills":         "Questions about technical and soft skills relevant to the role",
    "location":       "Questions about work location, relocation, and remote preferences",
    "salary":         "Questions about current compensation and expectations",
    "notice_period":  "Questions about availability and notice period",
}

# ── Answer Types ──────────────────────────────────────────────────────────────

ANSWER_TYPES = {
    "text":          "Free-form text response from the candidate",
    "yes_no":        "Simple yes or no answer",
    "numeric":       "A number such as years of experience or expected salary",
    "choice":        "Selection from a predefined list of options",
    "date":          "A specific date or time frame",
    "confirmation":  "Candidate confirms a specific fact",
}

# ── Scoring Importance ────────────────────────────────────────────────────────

SCORING_IMPORTANCE = {
    "critical":   "Answer directly affects eligibility decision — must be asked",
    "high":       "Answer strongly influences scoring — highly recommended",
    "medium":     "Answer provides useful context — ask when time permits",
    "low":        "Nice-to-have information — optional background",
}

# ── Language Support ──────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    "en":    "English",
    "hi":    "Hindi",
    "ml":    "Malayalam",
    "ta":    "Tamil",
    "te":    "Telugu",
    "kn":    "Kannada",
    "mr":    "Marathi",
    "bn":    "Bengali",
}

# ── Question Templates ────────────────────────────────────────────────────────

QUESTION_TEMPLATES = {
    "role_specific_skill": "How many years of experience do you have with {skill}?",
    "role_confirmation":   "This role is for a {role_name} position at {company}. Can you confirm you are applying for this role?",
    "salary_range":        "Our budget for this role is between {min_salary} and {max_salary} per annum. Does this align with your expectations?",
    "experience_years":    "The role requires {min_years} to {max_years} years of experience. How many years of relevant experience do you have?",
    "location_check":      "This role is based in {location}. Are you comfortable working from {location}?",
    "notice_period_check": "Our ideal joining date is within {max_days} days. What is your current notice period?",
    "open_intro":          "Could you briefly introduce yourself and walk me through your current role?",
    "skill_proficiency":   "On a scale of 1 to 5, how would you rate your proficiency in {skill}?",
    "certification_check": "Do you hold a {certification} certification?",
    "team_size":           "In your current or most recent role, how large was the team you worked with?",
}

# ── Master Question Bank ──────────────────────────────────────────────────────

QUESTION_BANK = [

    # ── Introduction ─────────────────────────────────────────────────────────
    {
        "question_id":     "Q001",
        "category":        "introduction",
        "question_text":   "Good {time_of_day}, {candidate_name}. I am an AI screening assistant from Zecpath. This call will take about 10 minutes. Are you ready to proceed?",
        "answer_type":     "yes_no",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"yes": "proceed", "no": "reschedule"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["opener", "consent", "all_roles"],
        "translations":    {"hi": "\u0928\u092e\u0938\u094d\u0924\u0947 {candidate_name}. \u092e\u0948\u0902 Zecpath \u0938\u0947 AI \u0938\u094d\u0915\u094d\u0930\u0940\u0928\u093f\u0902\u0917 \u0905\u0938\u093f\u0938\u094d\u0924\u0947\u0902\u091f \u0939\u0942\u0902. \u0915\u094d\u092f\u093e \u0906\u092a \u0906\u0917\u0947 \u092c\u095d\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0924\u0948\u092f\u093e\u0930 \u0939\u0948\u0902?"},
    },
    {
        "question_id":     "Q002",
        "category":        "introduction",
        "question_text":   "Could you please confirm your full name and the position you have applied for?",
        "answer_type":     "confirmation",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "name_and_role_match"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["identity", "verification", "all_roles"],
        "translations":    {"hi": "\u0915\u094d\u092f\u093e \u0906\u092a \u0905\u092a\u0928\u093e \u092a\u0942\u0930\u093e \u0928\u093e\u092e \u0914\u0930 \u0906\u0935\u0947\u0926\u093f\u0924 \u092a\u0926 \u092c\u0924\u093e \u0938\u0915\u0924\u0947 \u0939\u0948\u0902?"},
    },
    {
        "question_id":     "Q003",
        "category":        "introduction",
        "question_text":   "Could you briefly walk me through your background and current role?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "narrative", "min_words": 30},
        "follow_up":       "Q004",
        "role_specific":   False,
        "tags":            ["intro", "summary", "all_roles"],
        "translations":    {},
    },
    {
        "question_id":     "Q004",
        "category":        "introduction",
        "question_text":   "What motivated you to apply for this role at {company}?",
        "answer_type":     "text",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"type": "motivation_narrative"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["motivation", "culture_fit"],
        "translations":    {},
    },

    # ── Education ─────────────────────────────────────────────────────────────
    {
        "question_id":     "Q010",
        "category":        "education",
        "question_text":   "What is your highest educational qualification?",
        "answer_type":     "choice",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"options": ["B.Tech/B.E.", "M.Tech/M.E.", "B.Sc/M.Sc", "BCA/MCA", "MBA", "Diploma", "Other"]},
        "follow_up":       "Q011",
        "role_specific":   False,
        "tags":            ["degree", "qualification", "all_roles"],
        "translations":    {},
    },
    {
        "question_id":     "Q011",
        "category":        "education",
        "question_text":   "What was your field of study or specialization?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "field_of_study"},
        "follow_up":       "Q012",
        "role_specific":   False,
        "tags":            ["major", "specialization"],
        "translations":    {},
    },
    {
        "question_id":     "Q012",
        "category":        "education",
        "question_text":   "Which college or university did you graduate from, and in which year?",
        "answer_type":     "text",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"type": "institution_and_year"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["institution", "graduation_year"],
        "translations":    {},
    },
    {
        "question_id":     "Q013",
        "category":        "education",
        "question_text":   "Do you hold any professional certifications relevant to this role?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"yes": "ask_Q014", "no": "continue"},
        "follow_up":       "Q014",
        "role_specific":   False,
        "tags":            ["certifications", "professional_training"],
        "translations":    {},
    },
    {
        "question_id":     "Q014",
        "category":        "education",
        "question_text":   "Please name the certifications you hold and when they were obtained.",
        "answer_type":     "text",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"type": "certification_list"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["certifications", "follow_up"],
        "translations":    {},
    },

    # ── Experience ────────────────────────────────────────────────────────────
    {
        "question_id":     "Q020",
        "category":        "experience",
        "question_text":   "How many years of total professional experience do you have?",
        "answer_type":     "numeric",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "years", "min": 0, "max": 40},
        "follow_up":       "Q021",
        "role_specific":   False,
        "tags":            ["experience", "years", "all_roles"],
        "translations":    {"hi": "\u0906\u092a\u0915\u0947 \u092a\u093e\u0938 \u0915\u0941\u0932 \u0915\u093f\u0924\u0928\u0947 \u0935\u0930\u094d\u0937\u094b\u0902 \u0915\u093e \u092a\u0947\u0936\u0947\u0935\u0930 \u0905\u0928\u0941\u092d\u0935 \u0939\u0948?"},
    },
    {
        "question_id":     "Q021",
        "category":        "experience",
        "question_text":   "What is your current or most recent job title and company?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "title_and_company"},
        "follow_up":       "Q022",
        "role_specific":   False,
        "tags":            ["current_role", "employer"],
        "translations":    {},
    },
    {
        "question_id":     "Q022",
        "category":        "experience",
        "question_text":   "Could you briefly describe your key responsibilities in your current or most recent role?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "responsibilities_narrative", "min_words": 20},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["responsibilities", "current_role"],
        "translations":    {},
    },
    {
        "question_id":     "Q023",
        "category":        "experience",
        "question_text":   "Have you worked in a similar role or domain before?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "high",
        "expected_answer": {"yes": "ask_Q024", "no": "continue"},
        "follow_up":       "Q024",
        "role_specific":   False,
        "tags":            ["domain_relevance", "role_match"],
        "translations":    {},
    },
    {
        "question_id":     "Q024",
        "category":        "experience",
        "question_text":   "Can you describe a specific project or achievement that demonstrates your experience in this domain?",
        "answer_type":     "text",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"type": "project_narrative", "min_words": 30},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["projects", "achievements"],
        "translations":    {},
    },

    # ── Skills ────────────────────────────────────────────────────────────────
    {
        "question_id":     "Q030",
        "category":        "skills",
        "question_text":   "What are your top three technical skills?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "skill_list", "min_count": 1},
        "follow_up":       "Q031",
        "role_specific":   False,
        "tags":            ["technical_skills", "all_roles"],
        "translations":    {},
    },
    {
        "question_id":     "Q031",
        "category":        "skills",
        "question_text":   "How many years of experience do you have with {primary_skill}?",
        "answer_type":     "numeric",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "years", "min": 0, "max": 30},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["skill_depth", "primary_skill"],
        "translations":    {},
    },
    {
        "question_id":     "Q032",
        "category":        "skills",
        "question_text":   "Have you worked with {secondary_skill} professionally?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "high",
        "expected_answer": {"yes": "ask_years", "no": "continue"},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["secondary_skill", "skill_check"],
        "translations":    {},
    },
    {
        "question_id":     "Q033",
        "category":        "skills",
        "question_text":   "On a scale of 1 to 5, how would you rate your proficiency in {skill}?",
        "answer_type":     "numeric",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"type": "rating", "min": 1, "max": 5},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["self_assessment", "skill_rating"],
        "translations":    {},
    },
    {
        "question_id":     "Q034",
        "category":        "skills",
        "question_text":   "Would you describe yourself as comfortable working in an Agile or Scrum environment?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"yes": "proceed", "no": "note"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["agile", "methodology", "soft_skills"],
        "translations":    {},
    },
    {
        "question_id":     "Q035",
        "category":        "skills",
        "question_text":   "Do you have experience leading a team or mentoring junior developers?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"yes": "ask_Q036", "no": "continue"},
        "follow_up":       "Q036",
        "role_specific":   False,
        "tags":            ["leadership", "mentoring", "soft_skills"],
        "translations":    {},
    },
    {
        "question_id":     "Q036",
        "category":        "skills",
        "question_text":   "How large was the team you led or mentored?",
        "answer_type":     "numeric",
        "mandatory":       False,
        "scoring_importance": "low",
        "expected_answer": {"type": "team_size", "min": 1},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["leadership", "team_size"],
        "translations":    {},
    },

    # ── Location ──────────────────────────────────────────────────────────────
    {
        "question_id":     "Q040",
        "category":        "location",
        "question_text":   "What is your current city of residence?",
        "answer_type":     "text",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "city_name"},
        "follow_up":       "Q041",
        "role_specific":   False,
        "tags":            ["location", "city", "all_roles"],
        "translations":    {},
    },
    {
        "question_id":     "Q041",
        "category":        "location",
        "question_text":   "This role requires working from {job_location}. Are you comfortable with this?",
        "answer_type":     "yes_no",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"yes": "eligible", "no": "ask_Q042"},
        "follow_up":       "Q042",
        "role_specific":   True,
        "tags":            ["location_fit", "relocation"],
        "translations":    {},
    },
    {
        "question_id":     "Q042",
        "category":        "location",
        "question_text":   "Would you be open to relocating to {job_location} for this role?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "critical",
        "expected_answer": {"yes": "eligible", "no": "flag_location_issue"},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["relocation", "location_flexibility"],
        "translations":    {},
    },
    {
        "question_id":     "Q043",
        "category":        "location",
        "question_text":   "Are you open to a hybrid work arrangement with {office_days} days per week in the office?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"yes": "proceed", "no": "note"},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["hybrid", "remote", "work_arrangement"],
        "translations":    {},
    },

    # ── Salary ────────────────────────────────────────────────────────────────
    {
        "question_id":     "Q050",
        "category":        "salary",
        "question_text":   "What is your current annual compensation, including all components?",
        "answer_type":     "numeric",
        "mandatory":       False,
        "scoring_importance": "high",
        "expected_answer": {"type": "amount_inr", "min": 0},
        "follow_up":       "Q051",
        "role_specific":   False,
        "tags":            ["current_ctc", "compensation"],
        "translations":    {},
    },
    {
        "question_id":     "Q051",
        "category":        "salary",
        "question_text":   "What is your expected annual compensation for this role?",
        "answer_type":     "numeric",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"type": "amount_inr", "min": 0},
        "follow_up":       "Q052",
        "role_specific":   False,
        "tags":            ["expected_ctc", "salary_expectation"],
        "translations":    {},
    },
    {
        "question_id":     "Q052",
        "category":        "salary",
        "question_text":   "Our budget for this role is between {min_salary} and {max_salary} LPA. Does this align with your expectations?",
        "answer_type":     "yes_no",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"yes": "eligible", "no": "flag_salary_mismatch"},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["salary_fit", "budget_alignment"],
        "translations":    {},
    },
    {
        "question_id":     "Q053",
        "category":        "salary",
        "question_text":   "Are you currently receiving or expecting any competing offers?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "medium",
        "expected_answer": {"yes": "note_urgency", "no": "continue"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["competing_offers", "urgency"],
        "translations":    {},
    },

    # ── Notice Period ─────────────────────────────────────────────────────────
    {
        "question_id":     "Q060",
        "category":        "notice_period",
        "question_text":   "Are you currently employed?",
        "answer_type":     "yes_no",
        "mandatory":       True,
        "scoring_importance": "high",
        "expected_answer": {"yes": "ask_Q061", "no": "ask_Q063"},
        "follow_up":       "Q061",
        "role_specific":   False,
        "tags":            ["employment_status", "availability"],
        "translations":    {},
    },
    {
        "question_id":     "Q061",
        "category":        "notice_period",
        "question_text":   "What is your current notice period?",
        "answer_type":     "numeric",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "days", "min": 0, "max": 180},
        "follow_up":       "Q062",
        "role_specific":   False,
        "tags":            ["notice_period", "all_roles"],
        "translations":    {},
    },
    {
        "question_id":     "Q062",
        "category":        "notice_period",
        "question_text":   "Would you be able to negotiate a shorter notice period if required?",
        "answer_type":     "yes_no",
        "mandatory":       False,
        "scoring_importance": "high",
        "expected_answer": {"yes": "note_negotiable", "no": "note_fixed"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["notice_negotiable", "availability"],
        "translations":    {},
    },
    {
        "question_id":     "Q063",
        "category":        "notice_period",
        "question_text":   "When would you be available to start if selected?",
        "answer_type":     "date",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"type": "date_or_timeframe"},
        "follow_up":       None,
        "role_specific":   False,
        "tags":            ["availability", "start_date"],
        "translations":    {},
    },
    {
        "question_id":     "Q064",
        "category":        "notice_period",
        "question_text":   "Our ideal joining date is within {max_days} days. Can you commit to joining within this timeline?",
        "answer_type":     "yes_no",
        "mandatory":       True,
        "scoring_importance": "critical",
        "expected_answer": {"yes": "eligible", "no": "flag_availability"},
        "follow_up":       None,
        "role_specific":   True,
        "tags":            ["joining_timeline", "commitment"],
        "translations":    {},
    },
]

# ── Role-Specific Question Sets ───────────────────────────────────────────────

ROLE_QUESTION_SETS = {
    "software_engineer": {
        "mandatory_categories":  ["introduction", "experience", "skills", "notice_period"],
        "optional_categories":   ["education", "location", "salary"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q010","Q020","Q021","Q030","Q031","Q060","Q061","Q064"],
        "optional_question_ids":  ["Q004","Q011","Q012","Q013","Q023","Q024","Q032","Q033","Q034","Q041","Q051","Q052"],
        "primary_skills":        ["python", "django", "aws", "docker"],
        "secondary_skills":      ["react", "postgresql", "kubernetes", "redis"],
        "min_experience_years":  1.5,
        "max_experience_years":  10.0,
    },
    "data_analyst": {
        "mandatory_categories":  ["introduction", "experience", "skills", "notice_period"],
        "optional_categories":   ["education", "salary"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q010","Q020","Q021","Q030","Q031","Q060","Q061","Q064"],
        "optional_question_ids":  ["Q012","Q013","Q023","Q032","Q033","Q051","Q052"],
        "primary_skills":        ["sql", "python", "power bi"],
        "secondary_skills":      ["tableau", "excel", "data visualization"],
        "min_experience_years":  1.0,
        "max_experience_years":  8.0,
    },
    "data_scientist": {
        "mandatory_categories":  ["introduction", "experience", "skills", "education", "notice_period"],
        "optional_categories":   ["salary", "location"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q010","Q011","Q020","Q021","Q030","Q031","Q060","Q061","Q064"],
        "optional_question_ids":  ["Q013","Q023","Q024","Q032","Q033","Q035","Q051","Q052"],
        "primary_skills":        ["python", "machine learning", "tensorflow"],
        "secondary_skills":      ["pytorch", "scikit-learn", "sql", "deep learning"],
        "min_experience_years":  2.0,
        "max_experience_years":  10.0,
    },
    "devops_engineer": {
        "mandatory_categories":  ["introduction", "experience", "skills", "notice_period"],
        "optional_categories":   ["education", "salary", "location"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q020","Q021","Q030","Q031","Q060","Q061","Q064"],
        "optional_question_ids":  ["Q010","Q013","Q023","Q032","Q033","Q034","Q041","Q051","Q052"],
        "primary_skills":        ["docker", "linux", "kubernetes"],
        "secondary_skills":      ["aws", "terraform", "ci/cd", "ansible"],
        "min_experience_years":  2.0,
        "max_experience_years":  12.0,
    },
    "hr_manager": {
        "mandatory_categories":  ["introduction", "experience", "skills", "notice_period"],
        "optional_categories":   ["education", "salary"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q010","Q020","Q021","Q030","Q060","Q061","Q064"],
        "optional_question_ids":  ["Q004","Q012","Q013","Q022","Q023","Q035","Q051","Q052"],
        "primary_skills":        ["recruitment", "hris", "payroll"],
        "secondary_skills":      ["training", "employee relations", "compliance"],
        "min_experience_years":  3.0,
        "max_experience_years":  15.0,
    },
    "management_trainee": {
        "mandatory_categories":  ["introduction", "education", "notice_period"],
        "optional_categories":   ["experience", "skills", "salary"],
        "mandatory_question_ids": ["Q001","Q002","Q003","Q010","Q011","Q060","Q063","Q064"],
        "optional_question_ids":  ["Q004","Q012","Q013","Q020","Q030","Q033","Q051"],
        "primary_skills":        ["communication", "excel", "presentation"],
        "secondary_skills":      ["leadership", "problem solving", "teamwork"],
        "min_experience_years":  0.0,
        "max_experience_years":  2.0,
    },
}


class ScreeningDatasetManager:
    """
    Manages the HR screening question dataset.
    Provides methods to query, filter, render, and export questions
    for the AI screening engine.
    """

    def __init__(self):
        self.questions        = QUESTION_BANK
        self.categories       = QUESTION_CATEGORIES
        self.role_sets        = ROLE_QUESTION_SETS
        self.templates        = QUESTION_TEMPLATES
        self.answer_types     = ANSWER_TYPES
        self.scoring_levels   = SCORING_IMPORTANCE
        self.languages        = SUPPORTED_LANGUAGES

    def get_questions_by_category(self, category: str) -> list:
        """Return all questions in a given category."""
        return [q for q in self.questions if q["category"] == category]

    def get_mandatory_questions(self, role_type: str = None) -> list:
        """Return all mandatory questions, optionally filtered by role."""
        if role_type and role_type in self.role_sets:
            ids = self.role_sets[role_type]["mandatory_question_ids"]
            return [q for q in self.questions if q["question_id"] in ids]
        return [q for q in self.questions if q["mandatory"]]

    def get_questions_by_importance(self, level: str) -> list:
        """Return all questions of a given scoring importance level."""
        return [q for q in self.questions if q["scoring_importance"] == level]

    def get_role_question_set(self, role_type: str) -> dict:
        """Return the complete question set for a specific role."""
        if role_type not in self.role_sets:
            return {}
        config = self.role_sets[role_type]
        mandatory = [q for q in self.questions
                     if q["question_id"] in config["mandatory_question_ids"]]
        optional  = [q for q in self.questions
                     if q["question_id"] in config["optional_question_ids"]]
        return {
            "role_type": role_type,
            "config":    config,
            "mandatory_questions": mandatory,
            "optional_questions":  optional,
            "total_mandatory":     len(mandatory),
            "total_optional":      len(optional),
            "total_questions":     len(mandatory) + len(optional),
        }

    def render_question(self, question_id: str, context: dict = None) -> str:
        """
        Render a question with context variables filled in.
        context dict can contain: candidate_name, company, role_name,
        primary_skill, job_location, min_salary, max_salary, max_days, etc.
        """
        q = next((q for q in self.questions if q["question_id"] == question_id), None)
        if not q:
            return ""
        text = q["question_text"]
        if context:
            for key, value in context.items():
                text = text.replace("{" + key + "}", str(value))
        return text

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        """Return a single question dict by ID."""
        return next((q for q in self.questions if q["question_id"] == question_id), None)

    def generate_dataset_summary(self) -> dict:
        """Generate a summary of the complete dataset."""
        by_category = {}
        for cat in self.categories:
            qs = self.get_questions_by_category(cat)
            by_category[cat] = {
                "count":     len(qs),
                "mandatory": sum(1 for q in qs if q["mandatory"]),
                "optional":  sum(1 for q in qs if not q["mandatory"]),
            }

        by_importance = {}
        for level in self.scoring_levels:
            by_importance[level] = len(self.get_questions_by_importance(level))

        return {
            "dataset_metadata": {
                "generated_at":     datetime.now().isoformat(),
                "total_questions":  len(self.questions),
                "total_categories": len(self.categories),
                "total_roles":      len(self.role_sets),
                "total_languages":  len(self.languages),
                "total_templates":  len(self.templates),
            },
            "by_category":   by_category,
            "by_importance": by_importance,
            "role_coverage": {
                role: {
                    "mandatory": len(cfg["mandatory_question_ids"]),
                    "optional":  len(cfg["optional_question_ids"]),
                }
                for role, cfg in self.role_sets.items()
            },
        }

    def save_dataset(self, output_path: str):
        """Save the complete dataset to JSON."""
        dataset = {
            "metadata": {
                "generated_at":   datetime.now().isoformat(),
                "version":        "1.0",
                "project":        "Zecpath AI Recruitment System",
                "day":            22,
            },
            "categories":          self.categories,
            "answer_types":        self.answer_types,
            "scoring_importance":  self.scoring_levels,
            "supported_languages": self.languages,
            "question_templates":  self.templates,
            "question_bank":       self.questions,
            "role_question_sets":  self.role_sets,
            "summary":             self.generate_dataset_summary(),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
