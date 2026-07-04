"""
Day 33 - HR Interview Engine Design
Zecpath AI Recruitment Platform

Defines the foundational architecture of the AI HR Interview system.
Covers the 6 interview categories, a role-based question generator
(Fresher vs Experienced, Technical vs Non-technical), the interview
state structure, and the 4 conversation phases that orchestrate a
complete HR interview from introduction through closing.
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Constants — Interview Categories
# ---------------------------------------------------------------------------

HR_INTERVIEW_CATEGORIES = {
    "self_introduction": {
        "label":       "Self Introduction",
        "description": "Candidate introduces themselves, background, and current situation",
        "order":       1,
        "phase":       "introduction",
    },
    "career_journey": {
        "label":       "Career Journey",
        "description": "Candidate walks through their professional history and key milestones",
        "order":       2,
        "phase":       "core_hr",
    },
    "strengths_weaknesses": {
        "label":       "Strengths & Weaknesses",
        "description": "Candidate reflects on personal and professional attributes",
        "order":       3,
        "phase":       "core_hr",
    },
    "teamwork_culture_fit": {
        "label":       "Teamwork & Culture Fit",
        "description": "Candidate demonstrates how they work with others and align with company values",
        "order":       4,
        "phase":       "core_hr",
    },
    "career_goals": {
        "label":       "Career Goals",
        "description": "Candidate describes short-term and long-term professional aspirations",
        "order":       5,
        "phase":       "role_evaluation",
    },
    "availability_commitment": {
        "label":       "Availability & Commitment",
        "description": "Candidate confirms availability, notice period, and long-term commitment",
        "order":       6,
        "phase":       "closing",
    },
}

# ---------------------------------------------------------------------------
# Constants — Role Profiles
# ---------------------------------------------------------------------------

ROLE_PROFILES = {
    "fresher_technical": {
        "label":        "Fresher — Technical",
        "experience":   "0-1 years",
        "focus":        "Learning ability, academic projects, technical fundamentals",
    },
    "fresher_nontechnical": {
        "label":        "Fresher — Non-Technical",
        "experience":   "0-1 years",
        "focus":        "Communication, attitude, campus activities, adaptability",
    },
    "experienced_technical": {
        "label":        "Experienced — Technical",
        "experience":   "2+ years",
        "focus":        "Project impact, technical depth, problem-solving, leadership",
    },
    "experienced_nontechnical": {
        "label":        "Experienced — Non-Technical",
        "experience":   "2+ years",
        "focus":        "Client handling, process ownership, cross-functional collaboration",
    },
}

# ---------------------------------------------------------------------------
# Constants — Question Bank
# ---------------------------------------------------------------------------

QUESTION_BANK = {
    "self_introduction": {
        "fresher_technical":       "Tell me about yourself and what drew you to a technical career.",
        "fresher_nontechnical":    "Tell me about yourself and why you are interested in this role.",
        "experienced_technical":   "Give me a brief introduction — who you are, your current role, and what you have built.",
        "experienced_nontechnical":"Give me a brief introduction — who you are, your current role, and what you manage.",
        "follow_up":               "What is the one thing about yourself you most want us to remember?",
    },
    "career_journey": {
        "fresher_technical":       "Walk me through your academic projects and what you learned from them.",
        "fresher_nontechnical":    "Walk me through any internships, part-time work, or campus activities you have been part of.",
        "experienced_technical":   "Walk me through your career so far — the roles, the key projects, and why you made each move.",
        "experienced_nontechnical":"Walk me through your career so far — the roles you have held and what drove each transition.",
        "follow_up":               "Which experience has had the biggest impact on how you work today?",
    },
    "strengths_weaknesses": {
        "fresher_technical":       "What is your greatest technical strength, and what is one area you are actively trying to improve?",
        "fresher_nontechnical":    "What do you consider your biggest strength, and what is one weakness you are working on?",
        "experienced_technical":   "What technical strength sets you apart from other engineers at your level, and what is one gap you are closing?",
        "experienced_nontechnical":"What strength has been most valuable in your career so far, and what is one area you are still developing?",
        "follow_up":               "Can you give me a specific example of a time that weakness affected your work and what you did about it?",
    },
    "teamwork_culture_fit": {
        "fresher_technical":       "Tell me about a time you worked in a team on a project — what was your role and how did you contribute?",
        "fresher_nontechnical":    "Describe a situation where you had to work closely with someone very different from you. How did you handle it?",
        "experienced_technical":   "Tell me about a time you disagreed with a technical decision in your team. How did you handle it?",
        "experienced_nontechnical":"Tell me about a time you had to influence a team or stakeholder without having direct authority.",
        "follow_up":               "What kind of team environment brings out the best in you?",
    },
    "career_goals": {
        "fresher_technical":       "Where do you see yourself technically in the next 3 years?",
        "fresher_nontechnical":    "Where do you see yourself professionally in the next 3 years?",
        "experienced_technical":   "What does your ideal next step look like technically, and where do you want to be in 5 years?",
        "experienced_nontechnical":"What does your ideal next role look like, and where do you want to be in 5 years?",
        "follow_up":               "How does this role specifically fit into those goals?",
    },
    "availability_commitment": {
        "fresher_technical":       "When can you start, and are you looking at this as a long-term role?",
        "fresher_nontechnical":    "When can you start, and are you committed to staying for at least a year?",
        "experienced_technical":   "What is your current notice period, and is there any flexibility on that?",
        "experienced_nontechnical":"What is your current notice period, and are you open to discussing start dates?",
        "follow_up":               "Is there anything on your end that might affect your availability in the first 90 days?",
    },
}

# ---------------------------------------------------------------------------
# Constants — Interview State Structure
# ---------------------------------------------------------------------------

QUESTION_STATE_FIELDS = [
    "question_id",          # Unique identifier e.g. Q-INTRO-001
    "category",             # One of the 6 HR interview categories
    "role_profile",         # Which role profile variant was asked
    "question_text",        # The actual question delivered to the candidate
    "response_captured",    # The candidate's answer text
    "response_word_count",  # Word count of the captured response
    "follow_up_eligible",   # True if the response is vague, short, or unclear
    "follow_up_asked",      # True if the follow-up was actually delivered
    "follow_up_response",   # The candidate's follow-up answer if captured
    "score",                # Score assigned to this response (0-100)
    "timestamp",            # When this question was asked
]

# ---------------------------------------------------------------------------
# Constants — Conversation Phases
# ---------------------------------------------------------------------------

CONVERSATION_PHASES = {
    "introduction": {
        "order":       1,
        "label":       "Introduction",
        "categories":  ["self_introduction"],
        "description": "AI delivers a warm greeting, explains the interview format, and asks the candidate to introduce themselves.",
    },
    "core_hr": {
        "order":       2,
        "label":       "Core HR Questions",
        "categories":  ["career_journey", "strengths_weaknesses", "teamwork_culture_fit"],
        "description": "AI covers the three core HR evaluation areas that apply to every candidate regardless of role or experience level.",
    },
    "role_evaluation": {
        "order":       3,
        "label":       "Role-Based Evaluation",
        "categories":  ["career_goals"],
        "description": "AI asks role-specific and experience-level-specific questions to evaluate alignment with the target position.",
    },
    "closing": {
        "order":       4,
        "label":       "Closing",
        "categories":  ["availability_commitment"],
        "description": "AI confirms availability, notice period, and commitment, then closes the interview with a warm handoff message.",
    },
}

# ---------------------------------------------------------------------------
# RoleBasedQuestionGenerator
# ---------------------------------------------------------------------------

class RoleBasedQuestionGenerator:
    """Generates the correct question for any combination of interview
    category and role profile. Always returns both the main question
    and the follow-up question for that category."""

    def __init__(self):
        self.question_bank = QUESTION_BANK
        self.role_profiles = ROLE_PROFILES

    def get_question(self, category: str, role_profile: str) -> dict:
        if category not in self.question_bank:
            return {"error": f"Unknown category: {category}"}
        if role_profile not in self.role_profiles:
            return {"error": f"Unknown role profile: {role_profile}"}

        bank = self.question_bank[category]
        return {
            "category":      category,
            "role_profile":  role_profile,
            "question_text": bank.get(role_profile, ""),
            "follow_up":     bank.get("follow_up", ""),
        }

    def get_full_interview_set(self, role_profile: str) -> list:
        """Return the ordered set of questions for a complete interview
        for a given role profile, one per category in phase order."""
        categories_ordered = sorted(
            HR_INTERVIEW_CATEGORIES.keys(),
            key=lambda c: HR_INTERVIEW_CATEGORIES[c]["order"]
        )
        return [
            self.get_question(category, role_profile)
            for category in categories_ordered
        ]

    def get_all_role_profiles(self) -> list:
        return list(self.role_profiles.keys())

    def get_all_categories(self) -> list:
        return list(self.question_bank.keys())


# ---------------------------------------------------------------------------
# InterviewStateManager
# ---------------------------------------------------------------------------

class InterviewStateManager:
    """Creates and manages the state object for each interview question.
    Tracks which questions have been asked, which responses have been
    captured, and which questions are eligible for a follow-up."""

    def __init__(self, session_id: str, candidate_name: str, role_profile: str):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.role_profile = role_profile
        self.question_states = []
        self.current_phase = "introduction"

    def create_question_state(self, category: str, question_text: str) -> dict:
        qid = f"Q-{category.upper()[:6]}-{len(self.question_states) + 1:03d}"
        state = {field: None for field in QUESTION_STATE_FIELDS}
        state.update({
            "question_id":       qid,
            "category":          category,
            "role_profile":      self.role_profile,
            "question_text":     question_text,
            "response_captured": None,
            "response_word_count": 0,
            "follow_up_eligible": False,
            "follow_up_asked":   False,
            "follow_up_response": None,
            "score":             None,
            "timestamp":         datetime.now().isoformat(),
        })
        self.question_states.append(state)
        return state

    def record_response(self, question_id: str, response: str) -> dict:
        state = self._find_state(question_id)
        if not state:
            return {"error": f"Question ID {question_id} not found"}
        word_count = len(response.split()) if response else 0
        state["response_captured"] = response
        state["response_word_count"] = word_count
        state["follow_up_eligible"] = word_count < 20 or self._is_vague(response)
        return state

    def _is_vague(self, text: str) -> bool:
        vague_signals = ["i don't know", "not sure", "maybe", "i think so", "kind of"]
        return any(signal in text.lower() for signal in vague_signals)

    def _find_state(self, question_id: str):
        return next((s for s in self.question_states if s["question_id"] == question_id), None)

    def get_session_summary(self) -> dict:
        asked = len(self.question_states)
        with_followup = sum(1 for s in self.question_states if s["follow_up_eligible"])
        return {
            "session_id":      self.session_id,
            "candidate_name":  self.candidate_name,
            "role_profile":    self.role_profile,
            "questions_asked": asked,
            "follow_ups_eligible": with_followup,
            "question_states": self.question_states,
            "generated_at":    datetime.now().isoformat(),
        }


# ---------------------------------------------------------------------------
# InterviewFlowDesigner
# ---------------------------------------------------------------------------

class InterviewFlowDesigner:
    """Orchestrates the 4 conversation phases and produces the complete
    interview flow design document — a structured description of how
    an AI HR interview runs from start to finish, including all
    phase transitions and the question set for a given role profile."""

    def __init__(self):
        self.phases = CONVERSATION_PHASES
        self.generator = RoleBasedQuestionGenerator()

    def get_phase_flow(self) -> list:
        return sorted(
            [
                {
                    "phase":       key,
                    "order":       val["order"],
                    "label":       val["label"],
                    "categories":  val["categories"],
                    "description": val["description"],
                }
                for key, val in self.phases.items()
            ],
            key=lambda x: x["order"]
        )

    def generate_flow_document(self, role_profile: str) -> dict:
        question_set = self.generator.get_full_interview_set(role_profile)
        phase_flow = self.get_phase_flow()

        return {
            "document_title": "Zecpath AI HR Interview — Flow Design Document",
            "role_profile":   role_profile,
            "role_label":     ROLE_PROFILES[role_profile]["label"],
            "total_questions": len(question_set),
            "phase_flow":     phase_flow,
            "question_set":   question_set,
            "state_fields":   QUESTION_STATE_FIELDS,
            "categories":     HR_INTERVIEW_CATEGORIES,
            "generated_at":   datetime.now().isoformat(),
        }

    def get_architecture_summary(self) -> dict:
        return {
            "total_categories":    len(HR_INTERVIEW_CATEGORIES),
            "total_phases":        len(CONVERSATION_PHASES),
            "total_role_profiles": len(ROLE_PROFILES),
            "questions_per_profile": len(HR_INTERVIEW_CATEGORIES),
            "total_questions_in_bank": sum(
                len([k for k in v if k != "follow_up"])
                for v in QUESTION_BANK.values()
            ),
            "follow_up_questions": len(QUESTION_BANK),
        }
