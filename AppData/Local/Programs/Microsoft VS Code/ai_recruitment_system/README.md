# AI Recruitment System

An AI-powered recruitment pipeline with resume parsing, screening, and interview scoring.

## Project Structure
- `data/` — Sample resumes and job descriptions
- `parsers/` — Resume and JD parsing logic
- `ats_engine/` — Applicant tracking system core
- `screening_ai/` — AI screening and filtering
- `interview_ai/` — Interview question generation
- `scoring/` — Candidate scoring engine
- `utils/` — Logging, helpers, config
- `tests/` — Unit and integration tests

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run Tests
```bash
pytest tests/ -v
```
