import os
import pytest

def test_folders_exist():
    folders = [
        "data", "parsers", "ats_engine",
        "screening_ai", "interview_ai",
        "scoring", "utils", "tests"
    ]
    for folder in folders:
        assert os.path.isdir(folder), f"Missing: {folder}"

def test_logger_works():
    from utils.logger import logger
    logger.info("Test log entry")
    assert os.path.exists("logs/ai_system.log")