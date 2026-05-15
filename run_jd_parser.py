import json
import sys
from pathlib import Path
from parsers.jd_parser import JDParser

def run_parser(pdf_path, output_dir="data/outputs"):
    print("\n" + "=" * 60)
    print("   AI RECRUITMENT SYSTEM — JD PARSER v2.0")
    print("=" * 60)

    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"\nInput  : {pdf_path}")
    print(f"Output : {output_dir}")
    print("\nParsing job descriptions...\n")

    parser = JDParser()
    jd_profiles = parser.parse_pdf(pdf_path)

    print(f"{'─'*60}")
    print(f"{'#':<5} {'Role':<40} {'Salary (India)'}")
    print(f"{'─'*60}")

    for i, jd in enumerate(jd_profiles, 1):
        role = jd["role_name"][:38]
        salary = jd["salary"]["india"] or "Not specified"
        print(f"{i:<5} {role:<40} {salary}")

    print(f"{'─'*60}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = str(Path(output_dir) / "parsed_jds.json")
    parser.save_output(jd_profiles, output_file)

    print(f"\nTotal JDs parsed : {len(jd_profiles)}")
    print(f"Output saved to  : {output_file}\n")

if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample_jds/management_trainee.pdf"
    run_parser(pdf_file)
