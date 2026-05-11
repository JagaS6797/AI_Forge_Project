from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db_session
from app.schemas.thread import CreateThreadRequest, RenameThreadRequest, ThreadOut
from app.services.thread_service import (
    create_thread,
    delete_thread,
    get_thread,
    list_threads,
    rename_thread,
)
from app.services.chat_service import list_chat_messages, get_attachments_by_ids
from app.schemas.chat import ChatMessageWithAttachmentsOut, AttachmentInfo

router = APIRouter(prefix="/api/threads", tags=["threads"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ThreadOut])
async def get_threads(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ThreadOut]:
    threads = await list_threads(db=db, user_email=current_user.email)
    return [ThreadOut.model_validate(t) for t in threads]


@router.post("", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
async def create_new_thread(
    payload: CreateThreadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThreadOut:
    thread = await create_thread(db=db, user_email=current_user.email, name=payload.name)
    return ThreadOut.model_validate(thread)


@router.patch("/{thread_id}", response_model=ThreadOut)
async def rename_thread_endpoint(
    thread_id: str,
    payload: RenameThreadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThreadOut:
    thread = await rename_thread(db=db, thread_id=thread_id, user_email=current_user.email, name=payload.name)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return ThreadOut.model_validate(thread)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread_endpoint(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    deleted = await delete_thread(db=db, thread_id=thread_id, user_email=current_user.email)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")


@router.get("/{thread_id}/messages", response_model=list[ChatMessageWithAttachmentsOut])
async def get_thread_messages(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageWithAttachmentsOut]:
    thread = await get_thread(db=db, thread_id=thread_id, user_email=current_user.email)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    messages = await list_chat_messages(db=db, user_email=current_user.email, thread_id=thread_id)
    
    result = []
    for m in messages:
        # Fetch attachment metadata if present
        attachments = []
        if m.attachment_ids:
            att_records = await get_attachments_by_ids(db, m.attachment_ids)
            attachments = [
                AttachmentInfo(
                    id=att.id,
                    file_name=att.file_name,
                    file_type=att.file_type,
                    attachment_type=att.attachment_type,
                    file_size=att.file_size,
                    created_at=att.created_at,
                )
                for att in att_records
            ]
        
        result.append(
            ChatMessageWithAttachmentsOut(
                id=m.id,
                role=m.role,
                content=m.content,
                attachment_ids=m.attachment_ids or [],
                attachments=attachments,
                created_at=m.created_at,
            )
        )
    
    return result
