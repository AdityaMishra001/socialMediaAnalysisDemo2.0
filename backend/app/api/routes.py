from __future__ import annotations
import io
import csv
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.config import settings
from app.models.analysis import FeedbackAnalysis
from app.schemas.analysis import AnalysisResponse, AnalysisResult
from app.services.file_parser import parse_csv_bytes, parse_txt_content, FileParseError
from app.services.llm_analyzer import analyze_feedback
from app.services.social_fetcher import fetch_social_content, identify_social_url, SocialFetcherError

router = APIRouter()

class SocialParseRequest(BaseModel):
    url: str

class SocialAnalyzeRequest(BaseModel):
    url: str
    goal: str = "improve_content"
    language: str = "auto"

@router.post("/social/parse")
async def parse_social_url_endpoint(payload: SocialParseRequest):
    """Inspect and preview a social media link (YouTube Video/Short/Channel or Reddit post)."""
    try:
        content = await fetch_social_content(payload.url)
        return {
            "platform": content["platform"],
            "scope": content["scope"],
            "title": content["title"],
            "author": content["author"],
            "thumbnail_url": content["thumbnail_url"],
            "item_count": content["item_count"],
            "stats": content["stats"],
            "sample_comments": content["comments"][:3],
        }
    except SocialFetcherError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect URL: {str(e)}")

@router.post("/social/analyze", response_model=AnalysisResponse)
async def analyze_social_url_endpoint(
    payload: SocialAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Directly fetch comments and analyze a YouTube or Reddit URL."""
    try:
        social_data = await fetch_social_content(payload.url)
    except SocialFetcherError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch social comments: {str(e)}")

    feedback_items = social_data["comments"]
    if not feedback_items:
        raise HTTPException(status_code=400, detail="No comments available to analyze for this link.")

    feedback_source = social_data["platform"]
    analysis_goal = payload.goal
    raw_sample = "\n---\n".join(feedback_items[:3])

    try:
        analysis_result = await analyze_feedback(
            feedback_items=feedback_items,
            feedback_source=feedback_source,
            analysis_goal=analysis_goal,
            language=payload.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    social_meta = {
        "title": social_data["title"],
        "author": social_data["author"],
        "thumbnail_url": social_data["thumbnail_url"],
        "url": social_data["url"],
        "platform": social_data["platform"],
        "scope": social_data["scope"],
        "stats": social_data["stats"],
    }

    db_record = FeedbackAnalysis(
        feedback_source=feedback_source,
        analysis_goal=analysis_goal,
        language=payload.language,
        item_count=len(feedback_items),
        raw_sample=raw_sample,
        status="completed",
        social_metadata=social_meta,
        result=analysis_result.model_dump(),
    )
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)

    return AnalysisResponse(
        id=db_record.id,
        feedback_source=db_record.feedback_source,
        analysis_goal=db_record.analysis_goal,
        language=db_record.language,
        item_count=db_record.item_count,
        raw_sample=db_record.raw_sample,
        status=db_record.status,
        social_metadata=social_meta,
        result=analysis_result,
        error_message=db_record.error_message,
        created_at=db_record.created_at.isoformat() if db_record.created_at else None,
    )

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_configured": bool(settings.OPENAI_API_KEY),
    }

@router.post("/analysis", response_model=AnalysisResponse)
async def create_analysis(
    feedback_text: Optional[str] = Form(None),
    feedback_source: str = Form("general"),
    analysis_goal: str = Form("general"),
    language: str = Form("auto"),
    social_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    feedback_items: List[str] = []
    social_meta = None

    # 1. Process Social URL if provided
    if social_url and social_url.strip():
        try:
            social_data = await fetch_social_content(social_url.strip())
            feedback_items.extend(social_data["comments"])
            feedback_source = social_data["platform"]
            social_meta = {
                "title": social_data["title"],
                "author": social_data["author"],
                "thumbnail_url": social_data["thumbnail_url"],
                "url": social_data["url"],
                "platform": social_data["platform"],
                "scope": social_data["scope"],
                "stats": social_data["stats"],
            }
        except SocialFetcherError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch social comments: {str(e)}")

    # 2. Process File if provided
    elif file and file.filename:
        filename_lower = file.filename.lower()
        content_bytes = await file.read()

        if len(content_bytes) > 20 * 1024 * 1024:  # 20MB limit
            raise HTTPException(status_code=400, detail="Uploaded file exceeds the maximum 20MB limit.")

        try:
            if filename_lower.endswith(".csv"):
                feedback_items = parse_csv_bytes(content_bytes, file.filename)
            elif filename_lower.endswith(".txt"):
                try:
                    text_str = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text_str = content_bytes.decode("latin-1")
                feedback_items = parse_txt_content(text_str)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format '{file.filename}'. Please upload a CSV (.csv) or plain text (.txt) file.",
                )
        except FileParseError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 3. Process text area if provided (or append)
    if feedback_text and feedback_text.strip():
        text_items = parse_txt_content(feedback_text)
        feedback_items.extend(text_items)

    # 4. Validate extracted items
    if not feedback_items:
        raise HTTPException(
            status_code=400,
            detail="No feedback content detected. Please paste comments, provide a social link, or upload a valid CSV/TXT file.",
        )

    # Limit maximum items to prevent abuse
    if len(feedback_items) > settings.MAX_ITEMS:
        feedback_items = feedback_items[:settings.MAX_ITEMS]

    # Sample preview for storage
    raw_sample = "\n---\n".join(feedback_items[:3])

    # 5. Perform AI Analysis
    try:
        analysis_result = await analyze_feedback(
            feedback_items=feedback_items,
            feedback_source=feedback_source,
            analysis_goal=analysis_goal,
            language=language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # 6. Persist into Database
    db_record = FeedbackAnalysis(
        feedback_source=feedback_source,
        analysis_goal=analysis_goal,
        language=language,
        item_count=len(feedback_items),
        raw_sample=raw_sample,
        status="completed",
        social_metadata=social_meta,
        result=analysis_result.model_dump(),
    )
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)

    return AnalysisResponse(
        id=db_record.id,
        feedback_source=db_record.feedback_source,
        analysis_goal=db_record.analysis_goal,
        language=db_record.language,
        item_count=db_record.item_count,
        raw_sample=db_record.raw_sample,
        status=db_record.status,
        social_metadata=social_meta,
        result=analysis_result,
        error_message=db_record.error_message,
        created_at=db_record.created_at.isoformat() if db_record.created_at else None,
    )

@router.get("/analysis", response_model=List[AnalysisResponse])
async def list_recent_analyses(
    limit: int = 15,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackAnalysis).order_by(desc(FeedbackAnalysis.created_at)).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    items = []
    for r in records:
        try:
            res_obj = AnalysisResult(**r.result)
            items.append(
                AnalysisResponse(
                    id=r.id,
                    feedback_source=r.feedback_source,
                    analysis_goal=r.analysis_goal,
                    language=r.language,
                    item_count=r.item_count,
                    raw_sample=r.raw_sample,
                    status=r.status,
                    social_metadata=r.social_metadata,
                    result=res_obj,
                    error_message=r.error_message,
                    created_at=r.created_at.isoformat() if r.created_at else None,
                )
            )
        except Exception:
            continue
    return items

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackAnalysis).where(FeedbackAnalysis.id == analysis_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    res_obj = AnalysisResult(**record.result)
    return AnalysisResponse(
        id=record.id,
        feedback_source=record.feedback_source,
        analysis_goal=record.analysis_goal,
        language=record.language,
        item_count=record.item_count,
        raw_sample=record.raw_sample,
        status=record.status,
        social_metadata=record.social_metadata,
        result=res_obj,
        error_message=record.error_message,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackAnalysis).where(FeedbackAnalysis.id == analysis_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    await db.delete(record)
    await db.commit()
    return {"message": "Analysis deleted successfully", "id": analysis_id}

@router.get("/export/{analysis_id}/json")
async def export_json(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackAnalysis).where(FeedbackAnalysis.id == analysis_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    payload = {
        "id": record.id,
        "metadata": {
            "source": record.feedback_source,
            "goal": record.analysis_goal,
            "language": record.language,
            "item_count": record.item_count,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        },
        "analysis": record.result,
    }

    content_str = json.dumps(payload, indent=2)
    return Response(
        content=content_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="feedbackai-report-{analysis_id}.json"'},
    )

@router.get("/export/{analysis_id}/csv")
async def export_csv(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackAnalysis).where(FeedbackAnalysis.id == analysis_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    res = record.result
    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Summary
    writer.writerow(["FEEDBACKAI ANALYSIS REPORT"])
    writer.writerow(["ID", record.id])
    writer.writerow(["Source", record.feedback_source])
    writer.writerow(["Goal", record.analysis_goal])
    writer.writerow(["Total Items Analyzed", record.item_count])
    writer.writerow(["Overall Sentiment", res.get("overall_sentiment")])
    writer.writerow([])

    # 2. Sentiment Breakdown
    writer.writerow(["SENTIMENT DISTRIBUTION (%)"])
    dist = res.get("sentiment_distribution", {})
    writer.writerow(["Positive", "Negative", "Neutral", "Mixed"])
    writer.writerow([dist.get("positive"), dist.get("negative"), dist.get("neutral"), dist.get("mixed")])
    writer.writerow([])

    # 3. Key Themes
    writer.writerow(["KEY THEMES"])
    writer.writerow(["Theme", "Mentions", "Sentiment", "Urgency", "Representative Quotes"])
    for theme in res.get("key_themes", []):
        quotes = " | ".join(theme.get("representative_quotes", []))
        writer.writerow([theme.get("theme"), theme.get("count"), theme.get("sentiment"), theme.get("urgency"), quotes])
    writer.writerow([])

    # 4. Aspect Sentiments
    writer.writerow(["ASPECT-BASED SENTIMENT"])
    writer.writerow(["Aspect", "Sentiment", "Score (0-1)", "Examples"])
    for aspect in res.get("aspect_sentiments", []):
        examples = " | ".join(aspect.get("supporting_examples", []))
        writer.writerow([aspect.get("aspect"), aspect.get("sentiment"), aspect.get("score"), examples])
    writer.writerow([])

    # 5. Prioritized Recommendations
    writer.writerow(["ACTIONABLE RECOMMENDATIONS"])
    writer.writerow(["Title", "Priority", "Effort", "Category", "Rationale", "Expected Impact"])
    for rec in res.get("recommendations", []):
        writer.writerow([
            rec.get("title"),
            rec.get("priority"),
            rec.get("effort"),
            rec.get("category"),
            rec.get("rationale"),
            rec.get("expected_impact"),
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="feedbackai-summary-{analysis_id}.csv"'},
    )
