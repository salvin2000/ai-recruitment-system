"""
Tests for Day 22 – HR Screening Dataset Creation
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.screening_dataset import (
    ScreeningDatasetManager,
    QUESTION_BANK, QUESTION_CATEGORIES, ANSWER_TYPES,
    SCORING_IMPORTANCE, SUPPORTED_LANGUAGES,
    QUESTION_TEMPLATES, ROLE_QUESTION_SETS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def manager():
    return ScreeningDatasetManager()

@pytest.fixture
def summary(manager):
    return manager.generate_dataset_summary()

@pytest.fixture
def se_set(manager):
    return manager.get_role_question_set("software_engineer")

SAMPLE_CONTEXT = {
    "candidate_name": "Arjun Krishnan",
    "time_of_day":    "morning",
    "company":        "Zescer",
    "role_name":      "Software Engineer",
    "primary_skill":  "Python",
    "job_location":   "Bangalore",
    "min_salary":     "8",
    "max_salary":     "14",
    "max_days":       "60",
    "office_days":    "3",
}


# ── Manager Instance Tests ────────────────────────────────────────────────────

def test_manager_creates_instance(manager):
    assert manager is not None

def test_manager_has_questions(manager):
    assert len(manager.questions) > 0

def test_manager_has_categories(manager):
    assert len(manager.categories) > 0

def test_manager_has_role_sets(manager):
    assert len(manager.role_sets) > 0

def test_manager_has_templates(manager):
    assert len(manager.templates) > 0


# ── Question Bank Structure Tests ────────────────────────────────────────────

def test_all_questions_have_required_fields():
    required = ["question_id", "category", "question_text",
                "answer_type", "mandatory", "scoring_importance", "tags"]
    for q in QUESTION_BANK:
        for field in required:
            assert field in q, f"Question {q.get('question_id')} missing {field}"

def test_all_question_ids_unique():
    ids = [q["question_id"] for q in QUESTION_BANK]
    assert len(ids) == len(set(ids))

def test_all_categories_valid():
    for q in QUESTION_BANK:
        assert q["category"] in QUESTION_CATEGORIES

def test_all_answer_types_valid():
    for q in QUESTION_BANK:
        assert q["answer_type"] in ANSWER_TYPES

def test_all_scoring_levels_valid():
    for q in QUESTION_BANK:
        assert q["scoring_importance"] in SCORING_IMPORTANCE

def test_mandatory_field_is_bool():
    for q in QUESTION_BANK:
        assert isinstance(q["mandatory"], bool)


# ── Category Tests ────────────────────────────────────────────────────────────

def test_all_categories_defined():
    expected = ["introduction", "education", "experience",
                "skills", "location", "salary", "notice_period"]
    for cat in expected:
        assert cat in QUESTION_CATEGORIES

def test_each_category_has_questions(manager):
    for cat in QUESTION_CATEGORIES:
        questions = manager.get_questions_by_category(cat)
        assert len(questions) > 0, f"Category {cat} has no questions"

def test_get_questions_by_category_returns_list(manager):
    result = manager.get_questions_by_category("introduction")
    assert isinstance(result, list)
    assert len(result) > 0

def test_get_questions_by_category_filters_correctly(manager):
    result = manager.get_questions_by_category("skills")
    for q in result:
        assert q["category"] == "skills"


# ── Mandatory Question Tests ──────────────────────────────────────────────────

def test_get_mandatory_questions_returns_list(manager):
    result = manager.get_mandatory_questions()
    assert isinstance(result, list)
    assert len(result) > 0

def test_all_mandatory_questions_are_mandatory(manager):
    result = manager.get_mandatory_questions()
    for q in result:
        assert q["mandatory"] == True

def test_get_mandatory_questions_for_role(manager):
    result = manager.get_mandatory_questions("software_engineer")
    assert len(result) > 0

def test_mandatory_includes_opener(manager):
    mandatory = manager.get_mandatory_questions()
    ids = [q["question_id"] for q in mandatory]
    assert "Q001" in ids

def test_mandatory_includes_experience_question(manager):
    mandatory = manager.get_mandatory_questions()
    ids = [q["question_id"] for q in mandatory]
    assert "Q020" in ids


# ── Scoring Importance Tests ──────────────────────────────────────────────────

def test_get_questions_by_importance_returns_list(manager):
    result = manager.get_questions_by_importance("critical")
    assert isinstance(result, list)
    assert len(result) > 0

def test_questions_by_importance_filters_correctly(manager):
    result = manager.get_questions_by_importance("high")
    for q in result:
        assert q["scoring_importance"] == "high"

def test_all_importance_levels_have_questions(manager):
    for level in SCORING_IMPORTANCE:
        qs = manager.get_questions_by_importance(level)
        assert len(qs) > 0, f"No questions with importance {level}"


# ── Role Question Set Tests ───────────────────────────────────────────────────

def test_get_role_set_returns_dict(se_set):
    assert isinstance(se_set, dict)

def test_role_set_has_required_fields(se_set):
    assert "role_type"           in se_set
    assert "mandatory_questions" in se_set
    assert "optional_questions"  in se_set
    assert "total_mandatory"     in se_set
    assert "total_optional"      in se_set
    assert "total_questions"     in se_set

def test_role_set_counts_correct(se_set):
    assert se_set["total_questions"] == (
        se_set["total_mandatory"] + se_set["total_optional"]
    )

def test_role_set_unknown_role_returns_empty(manager):
    result = manager.get_role_question_set("unknown_xyz")
    assert result == {}

def test_all_roles_have_question_sets(manager):
    for role in ROLE_QUESTION_SETS:
        result = manager.get_role_question_set(role)
        assert result["total_mandatory"] > 0


# ── Render Question Tests ─────────────────────────────────────────────────────

def test_render_question_returns_string(manager):
    result = manager.render_question("Q001", SAMPLE_CONTEXT)
    assert isinstance(result, str)
    assert len(result) > 0

def test_render_question_fills_placeholders(manager):
    result = manager.render_question("Q001", SAMPLE_CONTEXT)
    assert "{candidate_name}" not in result
    assert "Arjun Krishnan" in result

def test_render_question_unknown_id_returns_empty(manager):
    result = manager.render_question("Q999")
    assert result == ""

def test_render_question_without_context_keeps_placeholders(manager):
    result = manager.render_question("Q001")
    assert "{candidate_name}" in result or "Arjun" not in result


# ── Get Question by ID Tests ──────────────────────────────────────────────────

def test_get_question_by_id_found(manager):
    q = manager.get_question_by_id("Q001")
    assert q is not None
    assert q["question_id"] == "Q001"

def test_get_question_by_id_not_found(manager):
    q = manager.get_question_by_id("Q999")
    assert q is None

def test_get_question_by_id_returns_correct_question(manager):
    q = manager.get_question_by_id("Q020")
    assert q["category"] == "experience"
    assert q["answer_type"] == "numeric"


# ── Dataset Summary Tests ─────────────────────────────────────────────────────

def test_summary_returns_dict(summary):
    assert isinstance(summary, dict)

def test_summary_has_required_sections(summary):
    assert "dataset_metadata" in summary
    assert "by_category"      in summary
    assert "by_importance"    in summary
    assert "role_coverage"    in summary

def test_summary_metadata_fields(summary):
    meta = summary["dataset_metadata"]
    assert "total_questions"  in meta
    assert "total_categories" in meta
    assert "total_roles"      in meta

def test_summary_total_questions_correct(summary):
    total = summary["dataset_metadata"]["total_questions"]
    assert total == len(QUESTION_BANK)

def test_summary_all_categories_covered(summary):
    for cat in QUESTION_CATEGORIES:
        assert cat in summary["by_category"]

def test_summary_all_roles_covered(summary):
    for role in ROLE_QUESTION_SETS:
        assert role in summary["role_coverage"]


# ── Save Dataset Tests ────────────────────────────────────────────────────────

def test_save_dataset(manager, tmp_path):
    output_file = str(tmp_path / "test_dataset.json")
    manager.save_dataset(output_file)
    assert os.path.exists(output_file)
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)
    assert "question_bank"      in data
    assert "question_templates" in data
    assert "role_question_sets" in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_answer_types_defined():
    for atype in ["text", "yes_no", "numeric", "choice", "date", "confirmation"]:
        assert atype in ANSWER_TYPES

def test_scoring_importance_defined():
    for level in ["critical", "high", "medium", "low"]:
        assert level in SCORING_IMPORTANCE

def test_supported_languages_defined():
    assert "en" in SUPPORTED_LANGUAGES
    assert "hi" in SUPPORTED_LANGUAGES
    assert "ml" in SUPPORTED_LANGUAGES

def test_question_templates_have_placeholders():
    no_placeholder = {"open_intro", "team_size"}
    templates_with_placeholders = {k:v for k,v in QUESTION_TEMPLATES.items() if k not in no_placeholder}
    for key, template in templates_with_placeholders.items():
        assert "{" in template and "}" in template

def test_role_configs_have_required_fields():
    required = ["mandatory_categories", "optional_categories",
                "mandatory_question_ids", "optional_question_ids",
                "primary_skills", "min_experience_years", "max_experience_years"]
    for role, cfg in ROLE_QUESTION_SETS.items():
        for field in required:
            assert field in cfg, f"Role {role} missing {field}"
