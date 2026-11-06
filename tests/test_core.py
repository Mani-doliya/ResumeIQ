"""Basic integration tests for ATS Resume Intelligence System."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.skill_extractor import skill_extractor
from app.services.resume_parser import resume_parser
from app.services.analysis_service import analysis_service
from app.utils.file_utils import validate_file


def test_taxonomy_loaded():
    assert len(skill_extractor.all_skills) > 50
    assert "python" in skill_extractor.all_skills
    print("PASS: taxonomy loaded")


def test_skill_extraction():
    text = "Experienced with Python, PyTorch, Docker, Kubernetes and FastAPI for MLOps."
    skills = skill_extractor.extract_skills(text)
    assert "python" in skills
    assert "pytorch" in skills
    assert "docker" in skills
    print("PASS: skill extraction")


def test_resume_parse():
    sample = Path(__file__).parent.parent / "data" / "sample_resume.txt"
    text = sample.read_text()
    profile = resume_parser.parse(text)
    assert profile.email is not None
    assert profile.experience_years is not None
    assert len(profile.extracted_skills) > 5
    print("PASS: resume parsing")


def test_full_analysis():
    sample = Path(__file__).parent.parent / "data" / "sample_resume.txt"
    text = sample.read_text()
    jd = (
        "Machine Learning Engineer role requiring Python, PyTorch, NLP, "
        "Transformers, BERT, FastAPI, Docker, Kubernetes, MLOps and AWS experience."
    )
    result = analysis_service.analyze(text, jd)
    assert 0 <= result.ats_score.overall_score <= 100
    assert result.skill_gap.match_percentage > 0
    assert result.domain.domain
    assert result.processing_time_ms > 0
    print(f"PASS: full analysis (ATS={result.ats_score.overall_score})")


def test_file_validation():
    ok, _ = validate_file("resume.pdf", 1024)
    assert ok
    ok, msg = validate_file("resume.exe", 1024)
    assert not ok
    ok, msg = validate_file("resume.pdf", 50 * 1024 * 1024)
    assert not ok
    print("PASS: file validation")


if __name__ == "__main__":
    test_taxonomy_loaded()
    test_skill_extraction()
    test_resume_parse()
    test_full_analysis()
    test_file_validation()
    print("\nAll tests passed.")