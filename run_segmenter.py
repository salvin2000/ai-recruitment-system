import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parsers.section_segmenter import ResumeSectionSegmenter

def run_segmenter(input_dir="data/sample_resumes", output_dir="data/outputs"):
    print("\n" + "=" * 60)
    print("   ZECPATH AI — RESUME SECTION SEGMENTER v1.0")
    print("=" * 60)
    segmenter = ResumeSectionSegmenter()
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    resume_files = list(Path(input_dir).glob("*.txt"))
    if not resume_files:
        print(f"No .txt files found in {input_dir}")
        sys.exit(1)
    print(f"\nFound {len(resume_files)} resume(s)\n")
    all_results = []
    for resume_file in sorted(resume_files):
        print(f"Processing: {resume_file.name}")
        result = segmenter.segment_file(str(resume_file))
        all_results.append(result)
        print(f"Accuracy: {result['metadata']['accuracy']}%")
        for section in result["sections"]:
            print(f"  {'OK' if section['type'] != 'unknown' else '??'} {section['type']:<20} '{section['heading'][:30]}'")
        output_file = Path(output_dir) / f"{resume_file.stem}_segmented.json"
        segmenter.save_output(result, str(output_file))
        print()
    report = segmenter.generate_accuracy_report(all_results)
    report_path = Path(output_dir) / "section_detection_accuracy_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nAverage Accuracy : {report['average_accuracy']}%")
    print(f"Total Sections   : {report['total_sections']}")
    print(f"Report saved to  : {report_path}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_segmenter()
