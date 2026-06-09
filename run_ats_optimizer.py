"""
Day 18 - Optimization & Performance Tuning
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_optimizer import (
    TextCleaner, OptimizedSectionExtractor, MemoryOptimizer,
    PerformanceBenchmarker, EntityRefiner, LRUCache,
    PERFORMANCE_BASELINES, PERFORMANCE_TARGETS
)


NOISY_RESUME = """CURRICULUM VITAE - Arjun Krishnan
Page 1 of 2
https://linkedin.com/in/arjunkrishnan

<html><b>Software Engineer</b></html>
arjun.krishnan@email.com   |   +91-9876543210

Summary
Passionate and enthusiastic    rockstar developer with   cutting-edge skills.
3 years of  experience  in   Python   and  Machine Learning...............

-------------------------------------------------------------------

Technical Skills
Python,   Django,   REST  API,   Machine  Learning,   AWS,   Docker

Work Experience
Software Engineer - TechCorp India Pvt Ltd
June 2022 - Present
- Developed  RESTful   APIs    using    Django REST Framework
- Implemented ML models for  customer  churn  prediction

Page 2 of 2

Education
Bachelor of Technology - Computer Science Engineering
RV College of Engineering, Bangalore | 2017 - 2021

Certifications
- AWS Certified Developer Associate (2023)
- Machine Learning Specialization - Coursera (2022)"""


def run_optimizer():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - OPTIMIZATION & PERFORMANCE TUNING v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    # ── Step 1: Text Cleaning ─────────────────────────────────────────────────
    print("\nStep 1: Text Cleaning")
    print("─" * 65)

    cleaner = TextCleaner()
    result  = cleaner.clean(NOISY_RESUME)
    print(f"  Original Length    : {result['original_length']} chars")
    print(f"  Cleaned Length     : {result['cleaned_length']} chars")
    print(f"  Reduction          : {result['reduction_pct']}%")
    print(f"  Noise Items Removed: {result['noise_items_removed']}")
    if result["removal_log"]:
        for pattern, count in result["removal_log"].items():
            if isinstance(count, int):
                print(f"    {pattern:<30} : {count} instance(s)")

    # Test cache hit
    result2 = cleaner.clean(NOISY_RESUME)
    stats   = cleaner.cache.stats()
    print(f"\n  Cache Stats: hits={stats['hits']} misses={stats['misses']} "
          f"hit_rate={stats['hit_rate']}")

    # ── Step 2: Optimized Section Extraction ──────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Optimized Section Extraction (Single Pass)")
    print("─" * 65)

    extractor = OptimizedSectionExtractor()
    sections  = extractor.extract_all_sections(result["cleaned_text"])
    for name, content in sections.items():
        if content.strip():
            preview = content[:60].replace("\n", " ")
            print(f"  {name:<20} : {len(content)} chars — {preview}...")

    # ── Step 3: Entity Refinement ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Entity Refinement")
    print("─" * 65)

    refiner = EntityRefiner()

    raw_skills = ["Python", "Django", "reactjs", "nodejs", "experience",
                  "the", "AWS", "amazon web services", "good", "git"]
    refined    = refiner.filter_false_positives(raw_skills)
    print(f"\n  Raw skills    : {raw_skills}")
    print(f"  Refined skills: {refined}")

    date_result = refiner.refine_date_range("June 2022 - Present")
    print(f"\n  Date Range: June 2022 - Present")
    print(f"    Start Year  : {date_result['start_year']}")
    print(f"    Start Month : {date_result['start_month']}")
    print(f"    Is Current  : {date_result['is_current']}")

    degree_result = refiner.refine_degree_detection(
        "Bachelor of Technology - Computer Science Engineering"
    )
    print(f"\n  Degree Detection:")
    print(f"    Degree      : {degree_result['degree']}")
    print(f"    Confidence  : {degree_result['confidence']}")

    # ── Step 4: Memory Optimization ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Memory Optimization")
    print("─" * 65)

    mem_opt = MemoryOptimizer()
    sparse_vec = {"python": 0.45, "django": 0.38, "noise": 0.0003,
                  "aws": 0.29, "tiny": 0.0002, "docker": 0.31}
    pruned = mem_opt.prune_sparse_vector(sparse_vec)
    print(f"\n  Original vector size : {len(sparse_vec)} entries")
    print(f"  Pruned vector size   : {len(pruned)} entries")
    print(f"  Removed entries      : {len(sparse_vec) - len(pruned)}")

    text, truncated = mem_opt.truncate_text("A" * 15000)
    print(f"\n  Text truncation: 15000 chars -> {len(text)} chars "
          f"(truncated: {truncated})")

    # ── Step 5: Performance Benchmarks ───────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Performance Benchmarks")
    print("─" * 65)

    benchmarker = PerformanceBenchmarker()
    before      = benchmarker.run_benchmark(n_resumes=5, optimized=False)
    after       = benchmarker.run_benchmark(n_resumes=5, optimized=True)
    report      = benchmarker.generate_performance_report(before, after)

    print(f"\n  {'Stage':<28} {'Before':>8} {'After':>8} {'Saved':>8} {'Target Met'}")
    print(f"  {'─'*28} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")

    for stage, data in report["improvements"].items():
        stage_name = stage.replace("_ms","").replace("_"," ").title()
        met = "PASS" if data["meets_target"] else "FAIL"
        print(f"  {stage_name:<28} {data['before_ms']:>7}ms "
              f"{data['after_ms']:>7}ms "
              f"{data['improvement_pct']:>7}% {met:>10}")

    print(f"\n  Overall Pass : {'YES' if report['overall_pass'] else 'NO'}")

    benchmarker.save_report(report, "data/outputs/performance_report.json")

    # ── Step 6: LRU Cache Demo ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: LRU Cache Performance")
    print("─" * 65)

    cache = LRUCache(max_size=3)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    _ = cache.get("key1")
    _ = cache.get("key1")
    _ = cache.get("key2")
    _ = cache.get("key_miss")

    stats = cache.stats()
    print(f"\n  Cache Size   : {stats['size']} / {stats['max_size']}")
    print(f"  Cache Hits   : {stats['hits']}")
    print(f"  Cache Misses : {stats['misses']}")
    print(f"  Hit Rate     : {round(stats['hit_rate']*100, 1)}%")

    print("\n" + "=" * 65)
    print("Optimization and performance tuning complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_optimizer()
