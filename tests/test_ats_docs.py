"""
Tests for Day 19 – ATS Documentation & Knowledge Transfer
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_docs import (
    ATSDocumentationGenerator,
    PIPELINE_ARCHITECTURE, MODULE_REGISTRY,
    SCORING_LOGIC, TROUBLESHOOTING_GUIDE,
    DEVELOPER_QUICK_REFERENCE,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def gen():
    return ATSDocumentationGenerator()

@pytest.fixture
def arch_summary(gen):
    return gen.generate_architecture_summary()

@pytest.fixture
def scoring_explainer(gen):
    return gen.generate_scoring_explainer()

@pytest.fixture
def full_docs(gen):
    return gen.generate_full_documentation()


# ── Generator Instance Tests ──────────────────────────────────────────────────

def test_generator_creates_instance(gen):
    assert gen is not None
    assert gen.architecture is not None
    assert gen.modules      is not None
    assert gen.scoring      is not None

def test_generator_has_troubleshooting(gen):
    assert len(gen.troubleshoot) > 0

def test_generator_has_quick_ref(gen):
    assert len(gen.quick_ref) > 0


# ── Architecture Summary Tests ────────────────────────────────────────────────

def test_arch_summary_returns_dict(arch_summary):
    assert isinstance(arch_summary, dict)

def test_arch_summary_has_required_fields(arch_summary):
    assert "pipeline_name" in arch_summary
    assert "version"       in arch_summary
    assert "total_days"    in arch_summary
    assert "total_layers"  in arch_summary
    assert "total_modules" in arch_summary
    assert "layers"        in arch_summary

def test_arch_summary_has_all_layers(arch_summary):
    expected = ["data_ingestion", "parsing", "intelligence",
                "decision", "integration", "quality"]
    for layer in expected:
        assert layer in arch_summary["layers"]

def test_arch_summary_layer_has_fields(arch_summary):
    for layer_name, layer in arch_summary["layers"].items():
        assert "days"        in layer
        assert "description" in layer
        assert "modules"     in layer
        assert "input"       in layer
        assert "output"      in layer

def test_arch_total_modules_correct(arch_summary):
    assert arch_summary["total_modules"] == len(MODULE_REGISTRY)

def test_arch_total_days_correct(arch_summary):
    assert arch_summary["total_days"] == PIPELINE_ARCHITECTURE["total_days"]


# ── Module Registry Tests ─────────────────────────────────────────────────────

def test_module_registry_has_all_modules(gen):
    expected = ["extractor.py", "jd_parser.py", "skill_extractor.py",
                "experience_parser.py", "education_parser.py",
                "semantic_matcher.py", "ats_scorer.py",
                "candidate_ranker.py", "bias_reducer.py",
                "ats_api.py", "ats_tester.py", "ats_optimizer.py"]
    for module in expected:
        assert module in gen.modules

def test_each_module_has_required_fields(gen):
    for name, data in gen.modules.items():
        assert "day"         in data
        assert "layer"       in data
        assert "class"       in data
        assert "purpose"     in data
        assert "key_methods" in data

def test_get_module_docs_single(gen):
    doc = gen.get_module_docs("ats_scorer.py")
    assert doc["day"]   == 13
    assert doc["layer"] == "intelligence"

def test_get_module_docs_unknown(gen):
    doc = gen.get_module_docs("nonexistent.py")
    assert doc == {}

def test_get_module_docs_all(gen):
    all_docs = gen.get_module_docs()
    assert isinstance(all_docs, dict)
    assert len(all_docs) == len(MODULE_REGISTRY)

def test_get_modules_by_layer(gen):
    parsing_modules = gen.get_modules_by_layer("parsing")
    assert isinstance(parsing_modules, list)
    assert len(parsing_modules) > 0
    for m in parsing_modules:
        assert m["layer"] == "parsing"

def test_module_days_sequential(gen):
    days = [data["day"] for data in gen.modules.values()]
    assert min(days) >= 5
    assert max(days) <= 18


# ── Scoring Logic Tests ───────────────────────────────────────────────────────

def test_scoring_explainer_returns_dict(scoring_explainer):
    assert isinstance(scoring_explainer, dict)

def test_scoring_explainer_has_required_fields(scoring_explainer):
    assert "overview"         in scoring_explainer
    assert "formula"          in scoring_explainer
    assert "components"       in scoring_explainer
    assert "grade_thresholds" in scoring_explainer
    assert "weight_profiles"  in scoring_explainer
    assert "example"          in scoring_explainer

def test_scoring_has_all_components(scoring_explainer):
    required = ["skill_match", "experience_relevance",
                "education_alignment", "semantic_similarity"]
    for comp in required:
        assert comp in scoring_explainer["components"]

def test_component_has_required_fields(scoring_explainer):
    for comp, data in scoring_explainer["components"].items():
        assert "weight_default" in data
        assert "source"         in data
        assert "range"          in data
        assert "description"    in data

def test_weight_profiles_sum_to_one(scoring_explainer):
    for role, weights in scoring_explainer["weight_profiles"].items():
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01

def test_grade_thresholds_all_defined(scoring_explainer):
    required = ["A+", "A", "B+", "B", "C+", "C", "D"]
    for grade in required:
        assert grade in scoring_explainer["grade_thresholds"]

def test_scoring_example_calculation_correct(scoring_explainer):
    ex    = scoring_explainer["example"]
    calc  = ex["calculation"]
    total = round(sum(calc.values()), 2)
    assert abs(total - ex["final_score"]) < 0.1

def test_scoring_example_has_grade(scoring_explainer):
    ex = scoring_explainer["example"]
    assert ex["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D"]


# ── Troubleshooting Tests ─────────────────────────────────────────────────────

def test_troubleshooting_returns_list(gen):
    result = gen.get_troubleshooting_guide()
    assert isinstance(result, list)
    assert len(result) > 0

def test_each_issue_has_required_fields(gen):
    for entry in gen.get_troubleshooting_guide():
        assert "issue"     in entry
        assert "symptoms"  in entry
        assert "causes"    in entry
        assert "solutions" in entry

def test_troubleshooting_filter_works(gen):
    result = gen.get_troubleshooting_guide("memory")
    assert isinstance(result, list)
    for entry in result:
        assert ("memory" in entry["issue"].lower() or
                any("memory" in s.lower() for s in entry["symptoms"]))

def test_troubleshooting_empty_filter(gen):
    result = gen.get_troubleshooting_guide("xyz_nonexistent_issue_xyz")
    assert result == []

def test_troubleshooting_covers_common_issues(gen):
    issues = [e["issue"].lower() for e in gen.get_troubleshooting_guide()]
    assert any("extract" in issue for issue in issues)
    assert any("scor" in issue for issue in issues)
    assert any("memory" in issue for issue in issues)


# ── Developer Guide Tests ─────────────────────────────────────────────────────

def test_developer_guide_returns_dict(gen):
    result = gen.get_developer_guide()
    assert isinstance(result, dict)
    assert len(result) > 0

def test_each_task_has_required_fields(gen):
    for task_key, task in gen.get_developer_guide().items():
        assert "title" in task
        assert "steps" in task
        assert len(task["steps"]) > 0

def test_developer_guide_has_key_tasks(gen):
    guide = gen.get_developer_guide()
    assert "add_new_role_type"  in guide
    assert "run_full_pipeline"  in guide
    assert "run_all_tests"      in guide

def test_developer_guide_single_task(gen):
    task = gen.get_developer_guide("run_all_tests")
    assert "title" in task
    assert "steps" in task

def test_developer_guide_unknown_task(gen):
    result = gen.get_developer_guide("nonexistent_task_xyz")
    assert result == {}


# ── Full Documentation Tests ──────────────────────────────────────────────────

def test_full_docs_returns_dict(full_docs):
    assert isinstance(full_docs, dict)

def test_full_docs_has_required_sections(full_docs):
    assert "doc_metadata"    in full_docs
    assert "architecture"    in full_docs
    assert "module_registry" in full_docs
    assert "scoring_logic"   in full_docs
    assert "troubleshooting" in full_docs
    assert "developer_guide" in full_docs

def test_full_docs_metadata_fields(full_docs):
    meta = full_docs["doc_metadata"]
    assert "generated_at"  in meta
    assert "doc_version"   in meta
    assert "pipeline_name" in meta
    assert "total_modules" in meta

def test_full_docs_total_modules(full_docs):
    assert full_docs["doc_metadata"]["total_modules"] == len(MODULE_REGISTRY)


# ── ASCII Architecture Tests ──────────────────────────────────────────────────

def test_ascii_arch_returns_string(gen):
    result = gen.generate_ascii_architecture()
    assert isinstance(result, str)

def test_ascii_arch_has_all_layers(gen):
    result = gen.generate_ascii_architecture()
    layers = ["DATA INGESTION", "PARSING", "INTELLIGENCE",
              "DECISION", "INTEGRATION", "QUALITY"]
    for layer in layers:
        assert layer in result

def test_ascii_arch_has_pipeline_name(gen):
    result = gen.generate_ascii_architecture()
    assert "ZECPATH" in result


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_pipeline_architecture_defined():
    assert "name"   in PIPELINE_ARCHITECTURE
    assert "layers" in PIPELINE_ARCHITECTURE
    assert len(PIPELINE_ARCHITECTURE["layers"]) == 6

def test_module_registry_not_empty():
    assert len(MODULE_REGISTRY) >= 10

def test_scoring_logic_has_components():
    assert "components" in SCORING_LOGIC
    assert len(SCORING_LOGIC["components"]) == 4

def test_troubleshooting_guide_not_empty():
    assert len(TROUBLESHOOTING_GUIDE) >= 5

def test_developer_quick_ref_not_empty():
    assert len(DEVELOPER_QUICK_REFERENCE) >= 3


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_documentation(gen, tmp_path):
    output_file = str(tmp_path / "test_docs.json")
    gen.save_documentation(output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "architecture"  in data
    assert "scoring_logic" in data
    assert "troubleshooting" in data
