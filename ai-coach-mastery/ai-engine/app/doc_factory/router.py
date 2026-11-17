"""Document render endpoint.

POST /api/v1/engine/documents/render
  body: { stageNum: 1..6, format: pptx|docx, engagementData{}, stageResult{} }

Renders the boardroom deliverable, persists it via the storage adapter
(local filesystem by default — /data/artifacts in the container — or
S3/Azure Blob/GCS purely by STORAGE_PROVIDER env), and streams the bytes
back with a Content-Disposition attachment header for one-click download.
The storage key is echoed in the X-Artifact-Key response header.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.doc_factory.docx_builder import generate_stage_docx
from app.doc_factory.pptx_builder import generate_stage_pptx
from app.providers.storage import get_storage_provider

router = APIRouter(prefix="/documents", tags=["engine:documents"])

_CONTENT_TYPES = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class RenderRequest(BaseModel):
    stage_num: int = Field(alias="stageNum", ge=1, le=6)
    format: str = Field(pattern="^(pptx|docx)$")
    engagement_data: dict = Field(alias="engagementData", default_factory=dict)
    stage_result: dict = Field(alias="stageResult", default_factory=dict)

    model_config = {"populate_by_name": True}


def _slug(text: str) -> str:
    """ASCII-only slug — HTTP headers are latin-1, so non-ASCII must be dropped."""
    cleaned = "".join(
        c.lower() if (c.isascii() and c.isalnum()) else "-" for c in text)
    collapsed = "-".join(part for part in cleaned.split("-") if part)
    return collapsed[:48] or "client"


@router.post("/render")
def render_document(req: RenderRequest,
                    settings: Annotated[Settings, Depends(get_settings)]) -> Response:
    """Render a stage deliverable; save to artifact storage; stream for download."""
    generators = {"pptx": generate_stage_pptx, "docx": generate_stage_docx}
    try:
        data = generators[req.format](req.stage_num, req.engagement_data,
                                      req.stage_result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    client = _slug(req.engagement_data.get("clientName", "client"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"deliverables/stage{req.stage_num}/{timestamp}-{client}.{req.format}"

    # Persist through the cloud-agnostic storage port (local/S3/Blob/GCS).
    try:
        storage = get_storage_provider(settings)
        storage.put(key, data, _CONTENT_TYPES[req.format])
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    filename = f"stage{req.stage_num}-{client}.{req.format}"
    return Response(
        content=data,
        media_type=_CONTENT_TYPES[req.format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Artifact-Key": key,
        },
    )
