from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db_session
from app.models.file_attachment import FileAttachment
from app.schemas.attachment import AttachmentMetadata, FileUploadResponse
from app.schemas.chat import ChatMessageOut, ChatRequest
from app.schemas.rag import PdfUploadResponse
from app.services.attachment_service import delete_file, get_file_content, save_uploaded_file, validate_file
from app.services.chat_service import list_chat_messages, stream_chat_events
from app.services.rag_service import upload_and_index_pdf
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    return StreamingResponse(
        stream_chat_events(
            db=db,
            message=payload.message,
            thread_id=payload.thread_id,
            user_email=current_user.email,
            attachment_ids=payload.attachment_ids,
            rag_enabled=payload.rag_enabled,
        ),
        media_type="text/event-stream",
    )


@router.get("/history", response_model=list[ChatMessageOut])
async def chat_history_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageOut]:
    """Backward-compat: returns all messages for the user (no thread filter)."""
    messages = await list_chat_messages(db=db, user_email=current_user.email)
    return [
        ChatMessageOut(
            id=item.id,
            role=item.role,
            content=item.content,
            attachment_ids=item.attachment_ids or [],
            created_at=item.created_at,
        )
        for item in messages
    ]


@router.post("/upload", response_model=FileUploadResponse)
async def upload_attachment(
    files: list[UploadFile] = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FileUploadResponse:
    """Upload file attachments."""
    attachments: list[AttachmentMetadata] = []
    
    for file in files:
        try:
            content = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            
            is_valid, error_msg = validate_file(file.filename or "file", len(content), mime_type)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "file_validation_error", "message": error_msg},
                )
            
            file_path = save_uploaded_file(content, file.filename or "file", mime_type)
            
            attachment = FileAttachment(
                user_id=await _get_user_id(db, current_user.email),
                file_name=file.filename or "file",
                file_type=mime_type,
                attachment_type=_attachment_type_for_mime(mime_type),
                file_size=len(content),
                file_path=file_path,
            )
            db.add(attachment)
            await db.commit()
            await db.refresh(attachment)
            
            attachments.append(
                AttachmentMetadata(
                    id=attachment.id,
                    file_name=attachment.file_name,
                    file_type=attachment.file_type,
                    attachment_type=attachment.attachment_type,
                    file_size=attachment.file_size,
                    created_at=attachment.created_at,
                )
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Failed to upload file: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "upload_failed", "message": str(exc)},
            )
    
    return FileUploadResponse(attachments=attachments)


@router.post("/upload-pdf", response_model=PdfUploadResponse)
async def upload_pdf_for_rag(
    thread_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PdfUploadResponse:
    try:
        content = await file.read()
        result = await upload_and_index_pdf(
            db=db,
            user_email=current_user.email,
            thread_id=thread_id,
            file_name=file.filename or "document.pdf",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "pdf_upload_failed", "message": str(exc)},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to upload and index PDF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "pdf_upload_failed", "message": str(exc)},
        )


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Download attachment file."""
    try:
        attachment = await db.scalar(
            select(FileAttachment).where(FileAttachment.id == attachment_id)
        )
        
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
        
        try:
            user_id = await _get_user_id(db, current_user.email)
        except Exception as e:
            logger.exception(f"Failed to get user ID: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        if attachment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        if not attachment.file_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File path not found in database")
        
        content = get_file_content(attachment.file_path)
        if content is None:
            logger.warning(f"File not found on disk: {attachment.file_path}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
        
        return FileResponse(
            path=attachment.file_path,
            media_type=attachment.file_type,
            filename=attachment.file_name,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to download attachment {attachment_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "download_failed", "message": str(exc)},
        )


@router.get("/images/{attachment_id}")
async def view_image(
    attachment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """View/stream image file (for LLM access)."""
    try:
        attachment = await db.scalar(
            select(FileAttachment).where(FileAttachment.id == attachment_id)
        )
        
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        
        if not attachment.file_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not an image")
        
        user_id = await _get_user_id(db, current_user.email)
        if attachment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        content = get_file_content(attachment.file_path)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found on disk")
        
        return FileResponse(
            path=attachment.file_path,
            media_type=attachment.file_type,
            filename=attachment.file_name,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to view image: {attachment_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "view_failed", "message": str(exc)},
        )


async def _get_user_id(db: AsyncSession, email: str) -> str:
    """Helper to get user ID from email."""
    from app.services.user_service import get_or_create_user_id
    return await get_or_create_user_id(db, email)


def _attachment_type_for_mime(mime_type: str) -> str:
    if mime_type.startswith("image/"):
        return "image"
    if mime_type == "application/pdf":
        return "pdf"
    return "file"
