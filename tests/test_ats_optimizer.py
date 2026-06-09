"""
Tests for Day 18 – Optimization & Performance Tuning
"""

import os
import sys
import json
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_optimizer import (
    TextCleaner, OptimizedSectionExtractor, MemoryOptimizer,
    PerformanceBenchmarker, EntityRefiner, LRUCache, timer,
    NOISE_PATTERNS, CACHE_CONFIG, MEMORY_CONFIG,
    PERFORMANCE_BASELINES, PERFORMANCE_TARGETS,
)


# ── Sample Texts ──────────────────────────────────────────────────────────────

NOISY_TEXT = """CURRICULUM VITAE - John Smith
Page 1 of 2
https://linkedin.com/in/johnsmith
<html><b>Software Engineer</b></html>

Technical Skills
Python,   Django,   AWS,   Docker

Work Experience
Software Engineer - TechCorp
June 2022 - Present
Developed RESTful APIs using Django"""

CLEAN_TEXT = """Technical Skills
Python, Django, AWS, Docker

Work Experience
Software Engineer - TechCorp
June 2022 - Present
Developed RESTful APIs"""

HEADING_TEXT = """Summary
Experienced developer.

Technical Skills
Python, Django, AWS

Work Experience
Software Engineer at TechCorp
June 2022 - Present

Education
B.Tech Computer Science
RV College | 2017-2021"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cleaner():
    return TextCleaner()

@pytest.fixture
def extractor():
    return OptimizedSectionExtractor()

@pytest.fixture
def mem_opt():
    return MemoryOptimizer()

@pytest.fixture
def benchmarker():
    return PerformanceBenchmarker()

@pytest.fixture
def refiner():
    return EntityRefiner()

@pytest.fixture
def cache():
    return LRUCache(max_size=5)


# ── LRU Cache Tests ───────────────────────────────────────────────────────────

def test_cache_creates_instance(cache):
    assert cache is not None
    assert cache.max_size == 5
    assert len(cache.cache) == 0

def test_cache_set_and_get(cache):
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

def test_cache_miss_returns_none(cache):
    assert cache.get("nonexistent") is None

def test_cache_hit_increments_counter(cache):
    cache.set("key1", "value1")
    cache.get("key1")
    cache.get("key1")
    assert cache.hits == 2

def test_cache_miss_increments_counter(cache):
    cache.get("nonexistent")
    assert cache.misses == 1

def test_cache_evicts_lru(cache):
    for i in range(6):
        cache.set(f"key{i}", f"val{i}")
    assert len(cache.cache) == 5  # max_size is 5

def test_cache_stats_returns_dict(cache):
    stats = cache.stats()
    assert "size"     in stats
    assert "max_size" in stats
    assert "hits"     in stats
    assert "misses"   in stats
    assert "hit_rate" in stats

def test_cache_hit_rate_calculation(cache):
    cache.set("k", "v")
    cache.get("k")   # hit
    cache.get("miss") # miss
    stats = cache.stats()
    assert stats["hit_rate"] == 0.5

def test_cache_clear(cache):
    cache.set("k1", "v1")
    cache.clear()
    assert len(cache.cache) == 0
    assert cache.hits   == 0
    assert cache.misses == 0


# ── TextCleaner Tests ─────────────────────────────────────────────────────────

def test_cleaner_creates_instance(cleaner):
    assert cleaner is not None
    assert len(cleaner.compiled_patterns) > 0

def test_clean_returns_dict(cleaner):
    result = cleaner.clean(NOISY_TEXT)
    assert isinstance(result, dict)

def test_clean_has_required_fields(cleaner):
    result = cleaner.clean(NOISY_TEXT)
    assert "cleaned_text"     in result
    assert "original_length"  in result
    assert "cleaned_length"   in result
    assert "reduction_pct"    in result
    assert "removal_log"      in result
    assert "noise_items_removed" in result

def test_clean_removes_html_tags(cleaner):
    result = cleaner.clean("<html><b>Software Engineer</b></html>")
    assert "<html>" not in result["cleaned_text"]
    assert "<b>"    not in result["cleaned_text"]

def test_clean_removes_urls(cleaner):
    result = cleaner.clean("Visit https://linkedin.com/in/test for profile")
    assert "https://" not in result["cleaned_text"]

def test_clean_removes_page_numbers(cleaner):
    result = cleaner.clean("Page 1 of 2\nSome content\nPage 2 of 2")
    assert "page 1 of 2" not in result["cleaned_text"].lower()

def test_clean_reduces_length(cleaner):
    result = cleaner.clean(NOISY_TEXT)
    assert result["cleaned_length"] <= result["original_length"]

def test_clean_uses_cache_on_repeat(cleaner):
    cleaner.clean(NOISY_TEXT)
    cleaner.clean(NOISY_TEXT)
    stats = cleaner.cache.stats()
    assert stats["hits"] >= 1

def test_clean_truncates_long_text(cleaner):
    long_text = "A" * 15000
    result    = cleaner.clean(long_text)
    assert result["cleaned_length"] <= MEMORY_CONFIG["max_text_length"]

def test_batch_clean_returns_list(cleaner):
    results = cleaner.batch_clean([NOISY_TEXT, CLEAN_TEXT])
    assert isinstance(results, list)
    assert len(results) == 2


# ── OptimizedSectionExtractor Tests ──────────────────────────────────────────

def test_extractor_creates_instance(extractor):
    assert extractor is not None
    assert len(extractor.HEADING_PATTERNS) > 0

def test_extract_all_sections_returns_dict(extractor):
    result = extractor.extract_all_sections(HEADING_TEXT)
    assert isinstance(result, dict)

def test_extract_all_sections_finds_skills(extractor):
    result = extractor.extract_all_sections(HEADING_TEXT)
    assert "skills" in result
    assert len(result["skills"]) > 0

def test_extract_all_sections_finds_experience(extractor):
    result = extractor.extract_all_sections(HEADING_TEXT)
    assert "experience" in result
    assert len(result["experience"]) > 0

def test_extract_all_sections_finds_education(extractor):
    result = extractor.extract_all_sections(HEADING_TEXT)
    assert "education" in result
    assert len(result["education"]) > 0

def test_extract_uses_cache_on_repeat(extractor):
    extractor.extract_all_sections(HEADING_TEXT)
    extractor.extract_all_sections(HEADING_TEXT)
    stats = extractor.cache.stats()
    assert stats["hits"] >= 1

def test_extract_all_sections_coverage(extractor):
    expected_sections = ["experience","education","skills",
                          "projects","certifications","summary","unknown"]
    result = extractor.extract_all_sections(HEADING_TEXT)
    for section in expected_sections:
        assert section in result


# ── MemoryOptimizer Tests ─────────────────────────────────────────────────────

def test_memory_optimizer_creates_instance(mem_opt):
    assert mem_opt is not None
    assert mem_opt.processed_count == 0

def test_prune_sparse_vector(mem_opt):
    vec    = {"python": 0.45, "noise1": 0.0001, "django": 0.38, "noise2": 0.0002}
    pruned = mem_opt.prune_sparse_vector(vec)
    assert "python" in pruned
    assert "django" in pruned
    assert "noise1" not in pruned
    assert "noise2" not in pruned

def test_prune_keeps_significant_values(mem_opt):
    vec    = {"a": 0.5, "b": 0.3, "c": 0.1}
    pruned = mem_opt.prune_sparse_vector(vec)
    assert len(pruned) == 3

def test_truncate_text_long(mem_opt):
    text, truncated = mem_opt.truncate_text("A" * 15000)
    assert truncated  == True
    assert len(text)  == MEMORY_CONFIG["max_text_length"]

def test_truncate_text_short(mem_opt):
    text, truncated = mem_opt.truncate_text("Short text")
    assert truncated  == False
    assert text       == "Short text"

def test_estimate_memory_kb(mem_opt):
    size = mem_opt.estimate_memory_kb("some data")
    assert size > 0

def test_should_gc_false_initially(mem_opt):
    assert mem_opt.should_gc() == False

def test_record_processing_increments_count(mem_opt):
    mem_opt.record_processing("C1", 100.0)
    assert mem_opt.processed_count == 1

def test_memory_stats_returns_dict(mem_opt):
    stats = mem_opt.get_stats()
    assert "processed_count" in stats
    assert "peak_memory_kb"  in stats
    assert "batch_size"      in stats


# ── PerformanceBenchmarker Tests ──────────────────────────────────────────────

def test_benchmarker_creates_instance(benchmarker):
    assert benchmarker is not None
    assert benchmarker.baselines is not None
    assert benchmarker.targets   is not None

def test_run_benchmark_returns_dict(benchmarker):
    result = benchmarker.run_benchmark(n_resumes=2)
    assert isinstance(result, dict)

def test_benchmark_has_required_fields(benchmarker):
    result = benchmarker.run_benchmark(n_resumes=2)
    assert "n_resumes"    in result
    assert "optimized"    in result
    assert "avg_times_ms" in result

def test_benchmark_includes_all_stages(benchmarker):
    result = benchmarker.run_benchmark(n_resumes=2)
    stages = ["text_extraction_ms", "skill_extraction_ms",
              "experience_parsing_ms", "education_parsing_ms",
              "semantic_matching_ms", "ats_scoring_ms"]
    for stage in stages:
        assert stage in result["avg_times_ms"]

def test_optimized_faster_than_baseline(benchmarker):
    before = benchmarker.run_benchmark(n_resumes=3, optimized=False)
    after  = benchmarker.run_benchmark(n_resumes=3, optimized=True)
    assert after["avg_times_ms"]["total_pipeline_ms"] < \
           before["avg_times_ms"]["total_pipeline_ms"]

def test_performance_report_returns_dict(benchmarker):
    before = benchmarker.run_benchmark(n_resumes=2, optimized=False)
    after  = benchmarker.run_benchmark(n_resumes=2, optimized=True)
    report = benchmarker.generate_performance_report(before, after)
    assert isinstance(report, dict)

def test_performance_report_has_required_sections(benchmarker):
    before = benchmarker.run_benchmark(n_resumes=2, optimized=False)
    after  = benchmarker.run_benchmark(n_resumes=2, optimized=True)
    report = benchmarker.generate_performance_report(before, after)
    assert "report_metadata" in report
    assert "improvements"    in report
    assert "overall_pass"    in report
    assert "baselines"       in report
    assert "targets"         in report

def test_improvement_has_fields(benchmarker):
    before = benchmarker.run_benchmark(n_resumes=2, optimized=False)
    after  = benchmarker.run_benchmark(n_resumes=2, optimized=True)
    report = benchmarker.generate_performance_report(before, after)
    for stage, data in report["improvements"].items():
        assert "before_ms"        in data
        assert "after_ms"         in data
        assert "improvement_pct"  in data
        assert "meets_target"     in data

def test_save_report(benchmarker, tmp_path):
    before = benchmarker.run_benchmark(n_resumes=2, optimized=False)
    after  = benchmarker.run_benchmark(n_resumes=2, optimized=True)
    report = benchmarker.generate_performance_report(before, after)
    output_file = str(tmp_path / "test_perf.json")
    benchmarker.save_report(report, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "improvements" in data


# ── EntityRefiner Tests ───────────────────────────────────────────────────────

def test_refiner_creates_instance(refiner):
    assert refiner is not None

def test_normalize_skill_reactjs(refiner):
    assert refiner.normalize_skill("reactjs") == "react"

def test_normalize_skill_nodejs(refiner):
    assert refiner.normalize_skill("node.js") == "node"

def test_normalize_skill_amazon_aws(refiner):
    assert refiner.normalize_skill("amazon web services") == "aws"

def test_normalize_skill_canonical(refiner):
    assert refiner.normalize_skill("python") == "python"

def test_filter_false_positives_removes_stopwords(refiner):
    skills   = ["python", "the", "experience", "django", "good", "aws"]
    filtered = refiner.filter_false_positives(skills)
    assert "the"        not in filtered
    assert "experience" not in filtered
    assert "good"       not in filtered

def test_filter_false_positives_keeps_real_skills(refiner):
    skills   = ["python", "django", "aws", "the", "and"]
    filtered = refiner.filter_false_positives(skills)
    assert "python" in filtered
    assert "django" in filtered
    assert "aws"    in filtered

def test_filter_false_positives_deduplicates(refiner):
    skills   = ["python", "python", "django"]
    filtered = refiner.filter_false_positives(skills)
    assert filtered.count("python") == 1

def test_refine_date_range_current(refiner):
    result = refiner.refine_date_range("June 2022 - Present")
    assert result["is_current"] == True
    assert result["start_year"] == "2022"

def test_refine_date_range_not_current(refiner):
    result = refiner.refine_date_range("January 2019 - March 2022")
    assert result["is_current"] == False

def test_refine_date_range_extracts_years(refiner):
    result = refiner.refine_date_range("2019 - 2022")
    assert result["start_year"] == "2019"
    assert result["end_year"]   == "2022"

def test_refine_degree_btech(refiner):
    result = refiner.refine_degree_detection(
        "Bachelor of Technology - Computer Science"
    )
    assert result["degree"]     == "b.tech"
    assert result["confidence"] > 0.5

def test_refine_degree_confidence_range(refiner):
    result = refiner.refine_degree_detection("some text without degree")
    assert 0.0 <= result["confidence"] <= 1.0


# ── Timer Decorator Tests ─────────────────────────────────────────────────────

def test_timer_adds_execution_ms():
    @timer
    def sample_function():
        return {"result": "ok"}
    result = sample_function()
    assert "_execution_ms" in result
    assert result["_execution_ms"] >= 0


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_noise_patterns_defined():
    required = ["extra_whitespace", "html_tags", "url_noise",
                 "page_numbers", "bullet_noise"]
    for p in required:
        assert p in NOISE_PATTERNS

def test_performance_targets_all_stages():
    required = ["text_extraction_ms", "skill_extraction_ms",
                 "semantic_matching_ms", "total_pipeline_ms"]
    for stage in required:
        assert stage in PERFORMANCE_TARGETS

def test_targets_lower_than_baselines():
    for stage in PERFORMANCE_TARGETS:
        if stage in PERFORMANCE_BASELINES:
            assert PERFORMANCE_TARGETS[stage] < PERFORMANCE_BASELINES[stage]

def test_memory_config_defined():
    assert "max_text_length"        in MEMORY_CONFIG
    assert "batch_size"             in MEMORY_CONFIG
    assert "sparse_vector_threshold"in MEMORY_CONFIG
