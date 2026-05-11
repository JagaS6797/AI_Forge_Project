from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone

import httpx
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import image_client
from app.core.config import settings
from app.models.file_attachment import FileAttachment
from app.services.attachment_service import save_uploaded_file
from app.services.user_service import get_or_create_user_id

logger = logging.getLogger(__name__)

IMAGE_COMMAND_PREFIXES = ("/image ", "/imagine ")
IMAGE_ACTION_WORDS = (
    "generate",
    "create",
    "make",
    "draw",
    "illustrate",
    "design",
    "render",
)
IMAGE_SUBJECT_WORDS = (
    "image",
    "picture",
    "pic",
    "photo",
    "art",
    "artwork",
    "illustration",
    "poster",
)


def _strip_image_request_prefix(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message).strip()
    lowered = normalized.lower()

    polite_prefixes = (
        "can you ",
        "could you ",
        "please ",
        "can u ",
    )
    for prefix in polite_prefixes:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            lowered = normalized.lower()
            break

    patterns = [
        r"^(?:generate|create|make|draw|illustrate|design|render)\s+(?:an?\s+)?(?:image|picture|pic|photo|art|artwork|illustration|poster)\s+(?:of|for|showing|with)\s+(.+)$",
        r"^(?:generate|create|make|draw|illustrate|design|render)\s+(?:an?\s+)?(?:image|picture|pic|photo|art|artwork|illustration|poster)\s+(.+)$",
        r"^(?:image|picture|pic|photo|art|artwork|illustration|poster)\s+(?:of|for|showing|with)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, lowered, flags=re.IGNORECASE)
        if match and match.group(1).strip():
            source_match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if source_match:
                return source_match.group(1).strip()

    return normalized


def _looks_like_image_generation_request(message: str) -> bool:
    lowered = message.lower()
    has_action = any(word in lowered for word in IMAGE_ACTION_WORDS)
    has_subject = any(word in lowered for word in IMAGE_SUBJECT_WORDS)
    return has_action and has_subject


def extract_image_prompt(message: str) -> str | None:
    message_text = message.strip()
    message_lower = message_text.lower()

    for prefix in IMAGE_COMMAND_PREFIXES:
        if message_lower.startswith(prefix):
            prompt = message_text[len(prefix) :].strip()
            return prompt or None

    if _looks_like_image_generation_request(message_text):
        prompt = _strip_image_request_prefix(message_text)
        return prompt or None

    return None


def _safe_file_stem(prompt: str, max_chars: int = 50) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", prompt).strip("-").lower()
    if not cleaned:
        return "generated-image"
    return cleaned[:max_chars]


async def _download_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def _event_attachment_metadata(attachment: FileAttachment) -> dict[str, object]:
    created_at = attachment.created_at
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    return {
        "id": attachment.id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "created_at": created_at.isoformat(),
    }


async def generate_image_attachment(
    *,
    db: AsyncSession,
    user_email: str,
    prompt: str,
) -> tuple[FileAttachment, dict[str, object]]:
    response = await image_client.images.generate(
        model=settings.image_gen_model,
        prompt=prompt,
        n=1,
    )

    if not response.data:
        raise OpenAIError("Image generation returned no image data")

    image_result = response.data[0]
    b64_image = getattr(image_result, "b64_json", None)
    image_url = getattr(image_result, "url", None)

    image_bytes: bytes | None = None
    if b64_image:
        image_bytes = base64.b64decode(b64_image)
    elif image_url:
        image_bytes = await _download_image_bytes(image_url)

    if not image_bytes:
        raise OpenAIError("Image generation completed but no usable image payload was returned")

    file_name = f"{_safe_file_stem(prompt)}.png"
    file_path = save_uploaded_file(image_bytes, file_name, "image/png")

    user_id = await get_or_create_user_id(db, user_email)
    attachment = FileAttachment(
        user_id=user_id,
        file_name=file_name,
        file_type="image/png",
        file_size=len(image_bytes),
        file_path=file_path,
    )

    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return attachment, _event_attachment_metadata(attachment)
