"""Resume file upload endpoints with real DB persistence and text extraction."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.config import settings
from app.core.database import get_db
from app.models import Resume, ResumeAnalysis
from app.schemas.resume import ResumeAnalysisResponse
from app.security.auth import get_current_user, get_or_create_user
from app.security.upload import sanitize_filename, validate_file_upload
from app.utils.document_parser import clean_extracted_text, extract_text_from_file

router = APIRouter(prefix="/resumes", tags=["resumes"])
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    resume_id: str
    filename: str
    size: int
    message: str


class ResumeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_size: int
    mime_type: str | None
    created_at: str


@router.get(
    "",
    response_model=list[ResumeDetail],
    summary="List all uploaded resumes for current user",
)
async def list_resumes(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResumeDetail]:
    """List all resumes uploaded by the authenticated user."""
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == user["user_id"])
        .order_by(Resume.created_at.desc())
        .all()
    )
    return [
        ResumeDetail(
            id=r.id,
            filename=r.filename,
            file_size=r.file_size,
            mime_type=r.mime_type,
            created_at=r.created_at.isoformat(),
        )
        for r in resumes
    ]


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload resume file",
)
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload a resume file for analysis.

    Supported formats: PDF, DOCX, TXT (max 5MB)
    The file is stored on disk, a Resume record is created in the DB,
    and text is extracted and stored alongside.
    """
    file_path = ""
    try:
        storage_name, size = validate_file_upload(
            file=file,
            max_size_mb=settings.max_upload_size_mb,
            allowed_extensions=settings.allowed_extensions,
        )

        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)

        content = await file.read()
        file_path = os.path.join(upload_dir, storage_name)
        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = ""
        try:
            extracted_text = extract_text_from_file(file_path, file.content_type)
            extracted_text = clean_extracted_text(extracted_text)
        except Exception as exc:
            logger.warning("Text extraction failed for %s: %s", storage_name, exc)

        get_or_create_user(db, user["user_id"], user.get("email"))

        resume = Resume(
            id=storage_name,
            user_id=user["user_id"],
            filename=sanitize_filename(file.filename or "unknown"),
            storage_path=storage_name,
            file_size=size,
            mime_type=file.content_type,
            extracted_text=extracted_text or None,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        logger.info(
            "Resume uploaded: user=%s original=%s stored=%s size=%s db_id=%s text_len=%d",
            user["user_id"],
            file.filename,
            storage_name,
            size,
            resume.id,
            len(extracted_text or ""),
        )

        return UploadResponse(
            resume_id=resume.id,
            filename=resume.filename,
            size=resume.file_size,
            message="Resume uploaded successfully",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume upload failed")
        # If we wrote a file but the DB commit failed, remove the orphan file
        # to prevent disk storage from accumulating unreachable files.
        if file_path:
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload resume",
        ) from exc


@router.get(
    "/{resume_id}",
    response_model=ResumeDetail,
    summary="Get resume details",
)
async def get_resume(
    resume_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeDetail:
    """Get resume details by ID. Ownership is enforced."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return ResumeDetail(
        id=resume.id,
        filename=resume.filename,
        file_size=resume.file_size,
        mime_type=resume.mime_type,
        created_at=resume.created_at.isoformat(),
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resume",
)
async def delete_resume(
    resume_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a resume and its file. Ownership is enforced."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    file_path = os.path.join(settings.upload_dir, resume.storage_path)
    try:
        os.remove(file_path)
    except OSError:
        pass

    db.delete(resume)
    db.commit()
    logger.info("Resume deleted: user=%s resume=%s", user["user_id"], resume_id)


@router.post(
    "/{resume_id}/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Analyze an uploaded resume",
)
async def analyze_uploaded_resume(
    resume_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """End-to-end: take a previously uploaded resume, run analysis, persist result.

    Ownership is enforced. The text was extracted at upload time.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not resume.extracted_text or not resume.extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume has no extractable text. Please re-upload as PDF, DOCX, or TXT.",
        )

    ai_provider = get_ai_provider()
    raw_result = await ai_provider.analyze_resume(
        resume_text=resume.extracted_text,
        job_description=None,
    )
    result = ResumeAnalysisResponse.model_validate(raw_result)

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        score=result.score,
        result_json=result.model_dump(),
        summary=result.summary,
    )
    db.add(analysis)
    db.commit()

    logger.info(
        "Resume analyzed: user=%s resume=%s score=%d",
        user["user_id"],
        resume_id,
        result.score,
    )

    return result
