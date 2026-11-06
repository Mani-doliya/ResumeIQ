import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import UPLOAD_DIR
from app.models.schemas import AnalysisResult, HealthResponse, ErrorResponse
from app.utils.file_utils import validate_file, sanitize_filename, extract_text
from app.services.analysis_service import analysis_service
from app.services.skill_extractor import skill_extractor
import sys

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        python_version=sys.version.split()[0]
    )


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: Optional[str] = Form(None)
):
    if not job_description or len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description must be at least 50 characters")

    content = await resume.read()
    file_size = len(content)
    valid, error_msg = validate_file(resume.filename or "", file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)

    safe_name = sanitize_filename(resume.filename or "resume.pdf")
    unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    file_path = UPLOAD_DIR / unique_name

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        resume_text = extract_text(file_path)
        if not resume_text or len(resume_text.strip()) < 80:
            raise HTTPException(
                status_code=422,
                detail="Could not extract sufficient text from the resume. Ensure it is a text-based PDF or TXT."
            )

        result = analysis_service.analyze(resume_text, job_description)
        return result

    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=f"Internal analysis error: {str(e)}")
    finally:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass


@router.get("/skills/taxonomy")
async def get_skills_taxonomy():
    domains = {}
    for domain, skills in skill_extractor.skills_by_domain.items():
        domains[domain] = sorted(list(skills))
    return {
        "total_skills": len(skill_extractor.all_skills),
        "domains": domains
    }


@router.post("/skills/extract")
async def extract_skills_only(text: str = Form(...)):
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Text too short")
    skills = skill_extractor.extract_skills(text)
    by_domain = skill_extractor.get_skills_by_domain(skills)
    return {"skills": skills, "by_domain": by_domain, "count": len(skills)}