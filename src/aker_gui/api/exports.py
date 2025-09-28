"""
Export API endpoints for the GUI application.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from datetime import date, datetime

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from aker_core.exports import MemoContextService, to_word

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/excel")
async def export_excel():
    """Generate Excel export."""
    return {"message": "Excel export - Coming Soon"}


class WordExportRequest(BaseModel):
    """Payload for Word memo exports."""

    msa_id: str = Field(..., description="Target MSA identifier")
    run_id: str = Field(..., description="Run identifier associated with export")
    git_sha: str = Field(..., description="Git SHA for reproducibility metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    asset_id: Optional[int] = Field(default=None, description="Optional asset identifier")
    as_of: Optional[date] = Field(default=None, description="Override as-of date")
    state_code: Optional[str] = Field(default=None, description="Two-letter state code for state packs")
    images: Dict[str, str] = Field(default_factory=dict, description="Mapping of image key to file path")
    risk_perils: Optional[list[str]] = Field(default=None, description="Optional list of perils to include")
    template_path: Optional[str] = Field(
        default="templates/ic_memo.docx",
        description="Path to the docxtpl template",
    )
    outdir: Optional[str] = Field(
        default=None,
        description="Optional output directory for generated memos",
    )


try:  # pragma: no cover - optional dependency surface
    from aker_core.database import get_session as _get_session  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback for tests/dev
    _get_session = None


def _acquire_session():
    if _get_session is None:
        return None
    try:
        return _get_session()
    except Exception:  # pragma: no cover - optional database
        logger.debug("word_export_session_unavailable", exc_info=True)
        return None


@router.post("/word")
async def export_word(request: WordExportRequest):
    """Generate Word export using docxtpl."""
    session = _acquire_session()
    try:
        service = MemoContextService(session=session)
        payload = service.build_context(
            msa_id=request.msa_id,
            run_id=request.run_id,
            git_sha=request.git_sha,
            created_at=request.created_at,
            images=request.images,
            as_of=request.as_of,
            asset_id=request.asset_id,
            state_code=request.state_code,
            risk_perils=request.risk_perils,
        )
        context = dict(payload.data)
        context["_memo_meta"] = payload.metadata

        output_path = await run_in_threadpool(
            to_word,
            context,
            template_path=request.template_path or "templates/ic_memo.docx",
            outdir=request.outdir,
        )
        logger.info("word_export_api_completed", extra={"output_path": str(output_path)})
        return {"path": str(output_path)}
    except FileNotFoundError as exc:
        logger.error("word_export_template_missing", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("word_export_failed")
        raise HTTPException(status_code=500, detail="Word export failed") from exc
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.debug("word_export_session_close_failed", exc_info=True)


@router.post("/pdf")
async def export_pdf():
    """Generate PDF export."""
    return {"message": "PDF export - Coming Soon"}
