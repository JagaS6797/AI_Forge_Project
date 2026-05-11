from __future__ import annotations

from app.services.image_generation_service import extract_image_prompt


def test_extract_image_prompt_with_explicit_command() -> None:
    assert extract_image_prompt("/image a red fox in snow") == "a red fox in snow"


def test_extract_image_prompt_with_natural_language_request() -> None:
    assert extract_image_prompt("Please generate an image of a futuristic city") == "a futuristic city"


def test_extract_image_prompt_with_non_image_text_returns_none() -> None:
    assert extract_image_prompt("Summarize this document") is None


def test_extract_image_prompt_handles_imagine_prefix() -> None:
    assert extract_image_prompt("/imagine watercolor mountain landscape") == "watercolor mountain landscape"
