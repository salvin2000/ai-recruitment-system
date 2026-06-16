"""
Day 28 – AI Screening Report Generator
Zecpath AI Recruitment Platform

Transforms raw AI evaluations into recruiter-friendly insights.
Generates structured screening reports with key answers, strengths,
risks, missing data, salary expectations, availability, and skill confirmations.
"""

import json
from datetime import datetime
from typing import Optional


# ── Report Sections ───────────────────────────────────────────────────────────

REPORT_SECTIONS = {
    "candidate_summary":    "Basic candidate information and screening metadata",
    "screening_score":      "Final score, grade, outcome from Day 26 scoring engine",
    "communication_profile":"Confidence, sentiment, and behavioral signals from Day 27",
    "key_answers":          "The most important answers given during the screening",
    "skill_confirmations":  "Skills the candidate confirmed they have",
    "availability":         "Notice period, joining timeline, location preference",
    "salary_expectation":   "Current and expected compensation details",
    "strengths":            "Positive indicators from the screening session",
    "risks":                "Concerns or gaps identified during screening",
    "missing_data":         "Mandatory questions not answered or answered vaguely",
    "recommendation":       "AI recommendation for the recruiter based on all signals",
}

# ── Strength Indicators ───────────────────────────────────────────────────────

STRENGTH_INDICATORS = {
    "strong_experience_match": "Candidate's stated experience closely matches ATS profile",
    "skill_depth_confirmed":   "Candidate confirmed depth in primary skills with specific examples",
    "high_confidence_signals": "Candidate communicated with ownership language and confidence",
    "positive_sentiment":      "Candidate expressed positive framing throughout the screening",
    "salary_aligned":          "Candidate's salary expectation is within the budget range",
    "immediate_availability":  "Candidate is immediately available or has a short notice period",
    "location_confirmed":      "Candidate confirmed comfort with the job location",
    "education_relevant":      "Candidate's degree and field of study match role requirements",
    "on_topic_throughout":     "Candidate stayed on topic for all questions",
    "complete_answers":        "Candidate provided complete answers to all mandatory questions",
}

# ── Risk Indicators ───────────────────────────────────────────────────────────

RISK_INDICATORS = {
    "experience_mismatch":     "Stated experience does not match ATS resume data",
    "primary_skill_missing":   "Candidate did not confirm the primary mandatory skill",
    "vague_on_key_questions":  "Candidate was vague on critical questions",
    "negative_framing":        "Candidate expressed negativity about past experiences",
    "salary_over_budget":      "Candidate's expected salary is above the approved budget",
    "long_notice_period":      "Notice period may delay onboarding beyond the target date",
    "location_unwilling":      "Candidate showed reluctance about the job location",
    "off_topic_responses":     "Candidate gave off-topic answers to key questions",
    "high_hesitation":         "Candidate showed significant hesitation patterns",
    "contradictory_statements":"Candidate made statements that contradicted each other",
    "low_confidence_signals":  "Candidate communicated with low confidence throughout",
    "missing_mandatory_answers":"One or more mandatory questions were not answered",
}

# ── Report Templates ──────────────────────────────────────────────────────────

REPORT_TEMPLATES = {
    "standard":   "Full report with all sections — for final recruiter review",
    "brief":      "Summary only — candidate snapshot for quick review",
    "technical":  "Focuses on skill confirmations and experience depth",
    "executive":  "Top-line metrics only — for hiring manager dashboard",
}

# ── Recommendation Levels ─────────────────────────────────────────────────────

RECOMMENDATION_LEVELS = {
    "strongly_recommend": {
        "label":       "Strongly Recommend",
        "description": "Candidate passed all screening criteria with high confidence. Proceed to technical interview immediately.",
        "color":       "green",
        "score_range": (80, 100),
    },
    "recommend": {
        "label":       "Recommend",
        "description": "Candidate meets most criteria. Proceed to technical interview with minor items to verify.",
        "color":       "light_green",
        "score_range": (65, 79),
    },
    "review": {
        "label":       "Review Required",
        "description": "Candidate shows potential but has gaps. Recruiter should review before proceeding.",
        "color":       "amber",
        "score_range": (45, 64),
    },
    "not_recommend": {
        "label":       "Not Recommended",
        "description": "Candidate does not meet minimum screening criteria. Consider rejecting.",
        "color":       "red",
        "score_range": (0, 44),
    },
}

# ── Export Formats ────────────────────────────────────────────────────────────

EXPORT_FORMATS = {
    "json":     "Machine-readable JSON for API integration",
    "markdown": "Markdown text for email or documentation",
    "summary":  "Plain text summary for quick reading",
}


class ReportDataCollector:
    """
    Collects and structures raw data from Day 25-27 outputs
    into a unified input object for the report generator.
    """

    def collect(self,
                candidate_profile:   dict,
                job_profile:         dict,
                answer_objects:      list,
                screening_score:     dict,
                behavioral_report:   dict) -> dict:
        """
        Collect and normalize all inputs into a unified report input.
        """
        # Extract key answers
        key_answers = {}
        for ans in answer_objects:
            qid = ans.get("question_id", "")
            if ans.get("is_valid") and ans.get("extracted"):
                key_answers[qid] = {
                    "question_id": qid,
                    "category":    ans.get("question_category", ""),
                    "clean_text":  ans.get("clean_text", ""),
                    "intent":      ans.get("intent", ""),
                    "extracted":   ans.get("extracted", {}),
                }

        # Collect skills mentioned across all answers
        all_skills = []
        for ans in answer_objects:
            skills = ans.get("extracted", {}).get("skills_mentioned", [])
            all_skills.extend(skills)
        confirmed_skills = list(dict.fromkeys(all_skills))

        # Extract salary info
        salary_info = {}
        for ans in answer_objects:
            ext = ans.get("extracted", {})
            if "salary_lpa" in ext:
                salary_info["stated_lpa"] = ext["salary_lpa"]
            if ans.get("question_id") == "Q052":
                salary_info["budget_aligned"] = ext.get("boolean_value")

        # Extract availability info
        availability = {}
        for ans in answer_objects:
            ext = ans.get("extracted", {})
            if "notice_period" in ext:
                availability["notice_period"] = ext["notice_period"]
            if "location" in ext:
                availability["preferred_location"] = ext["location"]
            if ans.get("question_id") == "Q041":
                availability["location_comfortable"] = ext.get("boolean_value")

        # Collect vague and off-topic
        vague_questions  = [a["question_id"] for a in answer_objects if a.get("is_vague")]
        offtopic_questions = [a["question_id"] for a in answer_objects if a.get("is_off_topic")]
        missing_data     = [a["question_id"] for a in answer_objects
                            if not a.get("is_valid") or a.get("needs_followup")]

        return {
            "candidate_profile":   candidate_profile,
            "job_profile":         job_profile,
            "key_answers":         key_answers,
            "confirmed_skills":    confirmed_skills,
            "salary_info":         salary_info,
            "availability":        availability,
            "screening_score":     screening_score,
            "behavioral_report":   behavioral_report,
            "vague_questions":     vague_questions,
            "offtopic_questions":  offtopic_questions,
            "missing_data":        missing_data,
            "total_answers":       len(answer_objects),
            "valid_answers":       sum(1 for a in answer_objects if a.get("is_valid")),
        }


class StrengthRiskAnalyzer:
    """
    Identifies strengths and risks from the collected screening data.
    """

    def __init__(self):
        self.strength_map = STRENGTH_INDICATORS
        self.risk_map     = RISK_INDICATORS

    def identify_strengths(self, data: dict) -> list:
        """Identify positive indicators from screening data."""
        strengths = []
        score     = data.get("screening_score", {})
        behav     = data.get("behavioral_report", {}).get("summary", {})
        avail     = data.get("availability", {})
        salary    = data.get("salary_info", {})
        skills    = data.get("confirmed_skills", [])
        job       = data.get("job_profile", {})
        tags      = [t for r in data.get("behavioral_report", {}).get("per_answer_results", [])
                     for t in r.get("behavioral_tags", [])]

        final_score = score.get("final_score", 0)
        if final_score >= 70:
            strengths.append({
                "indicator": "strong_experience_match",
                "label":     self.strength_map["strong_experience_match"],
                "evidence":  f"Screening score: {final_score}",
            })

        if skills:
            req_skills = set(s.lower() for s in job.get("required_skills", []))
            match      = [s for s in skills if s.lower() in req_skills]
            if len(match) >= 2:
                strengths.append({
                    "indicator": "skill_depth_confirmed",
                    "label":     self.strength_map["skill_depth_confirmed"],
                    "evidence":  f"Confirmed: {', '.join(match[:4])}",
                })

        if "highly_confident" in tags or behav.get("avg_confidence_score", 0) >= 0.55:
            strengths.append({
                "indicator": "high_confidence_signals",
                "label":     self.strength_map["high_confidence_signals"],
                "evidence":  f"Avg confidence: {behav.get('avg_confidence_score', 0):.2f}",
            })

        if behav.get("avg_sentiment_score", 0) >= 0.3:
            strengths.append({
                "indicator": "positive_sentiment",
                "label":     self.strength_map["positive_sentiment"],
                "evidence":  f"Avg sentiment: {behav.get('avg_sentiment_score', 0):.2f}",
            })

        if salary.get("budget_aligned") == True:
            strengths.append({
                "indicator": "salary_aligned",
                "label":     self.strength_map["salary_aligned"],
                "evidence":  "Candidate confirmed budget alignment",
            })

        notice = avail.get("notice_period", {})
        if notice.get("value", 999) <= 30:
            strengths.append({
                "indicator": "immediate_availability",
                "label":     self.strength_map["immediate_availability"],
                "evidence":  f"Notice period: {notice.get('value', 'N/A')} days",
            })

        if avail.get("location_comfortable") == True:
            strengths.append({
                "indicator": "location_confirmed",
                "label":     self.strength_map["location_confirmed"],
                "evidence":  f"Comfortable with {avail.get('preferred_location', 'job location')}",
            })

        missing = data.get("missing_data", [])
        if not missing:
            strengths.append({
                "indicator": "complete_answers",
                "label":     self.strength_map["complete_answers"],
                "evidence":  f"All {data.get('total_answers', 0)} answers were complete",
            })

        return strengths

    def identify_risks(self, data: dict) -> list:
        """Identify risk signals from screening data."""
        risks  = []
        score  = data.get("screening_score", {})
        behav  = data.get("behavioral_report", {}).get("summary", {})
        avail  = data.get("availability", {})
        salary = data.get("salary_info", {})
        tags   = [t for r in data.get("behavioral_report", {}).get("per_answer_results", [])
                  for t in r.get("behavioral_tags", [])]

        missing_q = data.get("missing_data", [])
        if missing_q:
            risks.append({
                "indicator": "missing_mandatory_answers",
                "label":     self.risk_map["missing_mandatory_answers"],
                "evidence":  f"Questions unanswered: {', '.join(missing_q[:4])}",
                "severity":  "high",
            })

        if data.get("vague_questions"):
            risks.append({
                "indicator": "vague_on_key_questions",
                "label":     self.risk_map["vague_on_key_questions"],
                "evidence":  f"Vague on: {', '.join(data['vague_questions'][:3])}",
                "severity":  "medium",
            })

        if data.get("offtopic_questions"):
            risks.append({
                "indicator": "off_topic_responses",
                "label":     self.risk_map["off_topic_responses"],
                "evidence":  f"Off-topic on: {', '.join(data['offtopic_questions'][:3])}",
                "severity":  "medium",
            })

        if "negative_framing" in tags:
            risks.append({
                "indicator": "negative_framing",
                "label":     self.risk_map["negative_framing"],
                "evidence":  "Negative sentiment detected in one or more answers",
                "severity":  "low",
            })

        if "contradictory" in tags:
            risks.append({
                "indicator": "contradictory_statements",
                "label":     self.risk_map["contradictory_statements"],
                "evidence":  "Contradiction detected in one answer",
                "severity":  "medium",
            })

        if behav.get("total_hesitations", 0) >= 8:
            risks.append({
                "indicator": "high_hesitation",
                "label":     self.risk_map["high_hesitation"],
                "evidence":  f"Total hesitations: {behav.get('total_hesitations', 0)}",
                "severity":  "low",
            })

        notice = avail.get("notice_period", {})
        if notice.get("value", 0) > 60:
            risks.append({
                "indicator": "long_notice_period",
                "label":     self.risk_map["long_notice_period"],
                "evidence":  f"Notice period: {notice.get('value')} days",
                "severity":  "medium",
            })

        return risks


class ScreeningReportGenerator:
    """
    Generates recruiter-friendly screening reports from AI evaluation data.
    Combines Day 25-27 outputs into structured, exportable reports.
    """

    def __init__(self):
        self.collector  = ReportDataCollector()
        self.analyzer   = StrengthRiskAnalyzer()
        self.sections   = REPORT_SECTIONS
        self.rec_levels = RECOMMENDATION_LEVELS
        self.templates  = REPORT_TEMPLATES

    def _get_recommendation(self, score: float, risks: list) -> dict:
        """Determine recommendation level from score and risk count."""
        high_risks = [r for r in risks if r.get("severity") == "high"]
        adj_score  = score - len(high_risks) * 10

        for level, data in self.rec_levels.items():
            lo, hi = data["score_range"]
            if lo <= adj_score <= hi:
                return {"level": level, **data}
        return {"level": "not_recommend", **self.rec_levels["not_recommend"]}

    def generate(self,
                 candidate_profile: dict,
                 job_profile:       dict,
                 answer_objects:    list,
                 screening_score:   dict,
                 behavioral_report: dict,
                 template:          str = "standard") -> dict:
        """
        Generate a complete recruiter-friendly screening report.
        """
        data        = self.collector.collect(
            candidate_profile, job_profile, answer_objects,
            screening_score, behavioral_report
        )
        strengths   = self.analyzer.identify_strengths(data)
        risks       = self.analyzer.identify_risks(data)
        final_score = screening_score.get("final_score", 0)
        recommendation = self._get_recommendation(final_score, risks)

        behav_summary  = behavioral_report.get("summary", {})
        score_obj      = screening_score

        report = {
            "report_metadata": {
                "generated_at":  datetime.now().isoformat(),
                "report_version":"1.0",
                "template":      template,
                "session_id":    candidate_profile.get("session_id", ""),
                "candidate_id":  candidate_profile.get("candidate_id", ""),
                "job_id":        job_profile.get("job_id", ""),
            },
            "candidate_summary": {
                "name":           candidate_profile.get("name", ""),
                "candidate_id":   candidate_profile.get("candidate_id", ""),
                "role_applied":   job_profile.get("role_name", ""),
                "company":        job_profile.get("company", ""),
                "ats_score":      candidate_profile.get("ats_score", 0),
                "screening_score":final_score,
                "grade":          score_obj.get("grade", ""),
                "outcome":        score_obj.get("outcome", ""),
            },
            "screening_score": {
                "final_score":       final_score,
                "grade":             score_obj.get("grade", ""),
                "grade_label":       score_obj.get("grade_label", ""),
                "outcome":           score_obj.get("outcome", ""),
                "category_scores":   score_obj.get("category_scores", {}),
                "dimension_averages":score_obj.get("dimension_averages", {}),
                "explanation":       score_obj.get("explanation", []),
                "mandatory_failed":  score_obj.get("mandatory_failed", []),
            },
            "communication_profile": {
                "avg_confidence":        behav_summary.get("avg_confidence_score", 0),
                "avg_sentiment":         behav_summary.get("avg_sentiment_score", 0),
                "avg_strength":          behav_summary.get("avg_strength_score", 0),
                "overall_strength_level":behav_summary.get("overall_strength_level", ""),
                "overall_strength_label":behav_summary.get("overall_strength_label", ""),
                "total_hesitations":     behav_summary.get("total_hesitations", 0),
                "total_uncertainties":   behav_summary.get("total_uncertainties", 0),
                "behavioral_tags":       behavioral_report.get("behavioral_tag_frequency", {}),
            },
            "key_answers":         data.get("key_answers", {}),
            "skill_confirmations": {
                "confirmed":     data.get("confirmed_skills", []),
                "required_match":[s for s in data.get("confirmed_skills", [])
                                   if s.lower() in [r.lower() for r in
                                                    job_profile.get("required_skills", [])]],
                "preferred_match":[s for s in data.get("confirmed_skills", [])
                                    if s.lower() in [p.lower() for p in
                                                     job_profile.get("preferred_skills", [])]],
            },
            "availability": {
                **data.get("availability", {}),
                "target_joining_days": job_profile.get("max_notice_days", 60),
                "availability_ok":     data.get("availability", {}).get(
                    "notice_period", {}).get("value", 999) <=
                    job_profile.get("max_notice_days", 60),
            },
            "salary_expectation": {
                **data.get("salary_info", {}),
                "budget_min_lpa": job_profile.get("min_salary_lpa", 0),
                "budget_max_lpa": job_profile.get("max_salary_lpa", 0),
            },
            "strengths":     strengths,
            "risks":         risks,
            "missing_data": {
                "unanswered_questions":  data.get("missing_data", []),
                "vague_questions":       data.get("vague_questions", []),
                "offtopic_questions":    data.get("offtopic_questions", []),
                "total_valid_answers":   data.get("valid_answers", 0),
                "total_answers":         data.get("total_answers", 0),
            },
            "recommendation": recommendation,
        }
        return report

    def export_markdown(self, report: dict) -> str:
        """Export report as markdown text."""
        c    = report["candidate_summary"]
        sc   = report["screening_score"]
        comm = report["communication_profile"]
        avail= report["availability"]
        sal  = report["salary_expectation"]
        rec  = report["recommendation"]

        lines = [
            f"# AI Screening Report — {c['name']}",
            f"**Role:** {c['role_applied']} at {c['company']}",
            f"**Generated:** {report['report_metadata']['generated_at'][:10]}",
            "",
            "## Screening Score",
            f"- **Final Score:** {sc['final_score']} / 100",
            f"- **Grade:** {sc['grade']} — {sc['grade_label']}",
            f"- **Outcome:** {sc['outcome'].upper()}",
            "",
            "## Communication Profile",
            f"- **Confidence:** {comm['avg_confidence']:.2f}",
            f"- **Sentiment:** {comm['avg_sentiment']:.2f}",
            f"- **Strength:** {comm['avg_strength']:.1f}/100 — {comm['overall_strength_label']}",
            f"- **Hesitations:** {comm['total_hesitations']}",
            "",
            "## Skill Confirmations",
        ]

        skills = report["skill_confirmations"]
        if skills["required_match"]:
            lines.append(f"- **Required Skills Confirmed:** {', '.join(skills['required_match'])}")
        if skills["preferred_match"]:
            lines.append(f"- **Preferred Skills Confirmed:** {', '.join(skills['preferred_match'])}")

        lines += [
            "",
            "## Availability",
            f"- **Notice Period:** {avail.get('notice_period', {}).get('value', 'N/A')} days",
            f"- **Location Comfortable:** {avail.get('location_comfortable', 'N/A')}",
            f"- **Availability OK:** {avail.get('availability_ok', 'N/A')}",
            "",
            "## Salary Expectation",
            f"- **Stated CTC:** {sal.get('stated_lpa', 'N/A')} LPA",
            f"- **Budget Range:** {sal.get('budget_min_lpa', 'N/A')} — {sal.get('budget_max_lpa', 'N/A')} LPA",
            f"- **Budget Aligned:** {sal.get('budget_aligned', 'N/A')}",
            "",
            "## Strengths",
        ]
        for s in report["strengths"]:
            lines.append(f"- **{s['label']}:** {s['evidence']}")

        lines += ["", "## Risks"]
        for r in report["risks"]:
            lines.append(f"- [{r['severity'].upper()}] **{r['label']}:** {r['evidence']}")

        missing = report["missing_data"]
        if missing["unanswered_questions"]:
            lines += ["", "## Missing Data"]
            lines.append(f"- Unanswered: {', '.join(missing['unanswered_questions'])}")
        if missing["vague_questions"]:
            lines.append(f"- Vague: {', '.join(missing['vague_questions'])}")

        lines += [
            "",
            "## Recommendation",
            f"**{rec['label']}**",
            f"{rec['description']}",
        ]
        return "\n".join(lines)

    def export_summary(self, report: dict) -> str:
        """Export a plain-text one-page summary."""
        c    = report["candidate_summary"]
        sc   = report["screening_score"]
        rec  = report["recommendation"]
        comm = report["communication_profile"]
        avail= report["availability"]
        sal  = report["salary_expectation"]
        skills = report["skill_confirmations"]

        sep  = "=" * 60
        lines = [
            sep,
            f"  ZECPATH AI SCREENING REPORT",
            f"  Candidate : {c['name']}",
            f"  Role      : {c['role_applied']} at {c['company']}",
            f"  Date      : {report['report_metadata']['generated_at'][:10]}",
            sep,
            f"  Screening Score : {sc['final_score']} / 100  |  Grade: {sc['grade']}",
            f"  Communication   : {comm['avg_strength']:.1f}/100  |  {comm['overall_strength_label']}",
            f"  Confidence      : {comm['avg_confidence']:.2f}  |  Sentiment: {comm['avg_sentiment']:.2f}",
            sep,
            f"  Skills Confirmed: {', '.join(skills['required_match']) or 'None'}",
            f"  Notice Period   : {avail.get('notice_period', {}).get('value', 'N/A')} days",
            f"  Location OK     : {avail.get('location_comfortable', 'N/A')}",
            f"  Salary Stated   : {sal.get('stated_lpa', 'N/A')} LPA  |  Budget: {sal.get('budget_min_lpa', 'N/A')}-{sal.get('budget_max_lpa', 'N/A')} LPA",
            f"  Budget Aligned  : {sal.get('budget_aligned', 'N/A')}",
            sep,
            f"  Strengths ({len(report['strengths'])}):",
        ]
        for s in report["strengths"][:4]:
            lines.append(f"    + {s['label']}")
        lines.append(f"  Risks ({len(report['risks'])}):")
        for r in report["risks"][:4]:
            lines.append(f"    ! [{r['severity'].upper()}] {r['label']}")
        lines += [
            sep,
            f"  RECOMMENDATION: {rec['label'].upper()}",
            f"  {rec['description']}",
            sep,
        ]
        return "\n".join(lines)

    def save_report(self, report: dict, output_path: str):
        """Save report to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
