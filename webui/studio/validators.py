from dataclasses import dataclass
from typing import Any

from app.models.schema import VideoParams

VALID_VIDEO_SOURCES = {"pexels", "pixabay", "local", "tiktok"}


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
    level: str = "error"


def _has_configured_key(value: Any) -> bool:
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return bool(str(value or "").strip())


def validate_render_request(
    params: VideoParams, app_config: dict[str, Any]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not params.video_subject and not params.video_script:
        issues.append(
            ValidationIssue(
                field="video_subject",
                message="Video Script and Subject Cannot Both Be Empty",
            )
        )

    if params.video_source not in VALID_VIDEO_SOURCES:
        issues.append(
            ValidationIssue(
                field="video_source",
                message="Please Select a Valid Video Source",
            )
        )
        return issues

    if params.video_source == "pexels" and not _has_configured_key(
        app_config.get("pexels_api_keys")
    ):
        issues.append(
            ValidationIssue(field="pexels_api_keys", message="Please Enter the Pexels API Key")
        )

    if params.video_source == "pixabay" and not _has_configured_key(
        app_config.get("pixabay_api_keys")
    ):
        issues.append(
            ValidationIssue(field="pixabay_api_keys", message="Please Enter the Pixabay API Key")
        )

    if params.video_source == "local" and not params.video_materials:
        issues.append(
            ValidationIssue(field="local_video_materials", message="Please Upload Local Files")
        )

    if params.video_source == "tiktok":
        provider = (app_config.get("tiktok_search_provider") or "serpapi").strip().lower()
        if provider == "serpapi" and not _has_configured_key(
            app_config.get("tiktok_search_api_key")
        ):
            issues.append(
                ValidationIssue(
                    field="tiktok_search_api_key",
                    message="Please Enter the TikTok Search API Key",
                )
            )
        if provider == "openai_web_search" and not _has_configured_key(
            app_config.get("openai_api_key")
        ):
            issues.append(
                ValidationIssue(
                    field="openai_api_key",
                    message="Please Enter the OpenAI API Key",
                )
            )

    return issues

