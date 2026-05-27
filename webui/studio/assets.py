import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_MEDIA_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".flv",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}


@dataclass(frozen=True)
class AssetRecord:
    provider: str
    name: str
    path: str
    size_bytes: int
    modified_time: float


@dataclass(frozen=True)
class SourceDiagnostic:
    name: str
    state: str
    detail: str


def scan_asset_directory(path: str | Path, provider: str) -> list[AssetRecord]:
    root = Path(path)
    if not root.exists() or not root.is_dir():
        return []

    records = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_MEDIA_EXTENSIONS:
            continue
        stat = file_path.stat()
        records.append(
            AssetRecord(
                provider=provider,
                name=file_path.name,
                path=str(file_path),
                size_bytes=stat.st_size,
                modified_time=stat.st_mtime,
            )
        )
    return sorted(records, key=lambda item: item.modified_time, reverse=True)


def _has_key(value: Any) -> bool:
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return bool(str(value or "").strip())


def get_source_diagnostics(app_config: dict[str, Any]) -> list[SourceDiagnostic]:
    diagnostics = [
        SourceDiagnostic(
            name="Pexels",
            state="configured" if _has_key(app_config.get("pexels_api_keys")) else "missing",
            detail="API key configured" if _has_key(app_config.get("pexels_api_keys")) else "Missing API key",
        ),
        SourceDiagnostic(
            name="Pixabay",
            state="configured" if _has_key(app_config.get("pixabay_api_keys")) else "missing",
            detail="API key configured" if _has_key(app_config.get("pixabay_api_keys")) else "Missing API key",
        ),
    ]

    provider = (app_config.get("tiktok_search_provider") or "serpapi").strip().lower()
    if provider == "openai_web_search":
        tiktok_configured = _has_key(app_config.get("openai_api_key"))
        detail = "OpenAI key configured" if tiktok_configured else "Missing OpenAI key"
    else:
        tiktok_configured = _has_key(app_config.get("tiktok_search_api_key"))
        detail = "SerpAPI key configured" if tiktok_configured else "Missing SerpAPI key"
    diagnostics.append(
        SourceDiagnostic(
            name="TikTok Search",
            state="configured" if tiktok_configured else "missing",
            detail=detail,
        )
    )

    cookie_file = str(app_config.get("tiktok_cookie_file") or "").strip()
    if cookie_file and os.path.exists(cookie_file):
        cookie_state = "configured"
        cookie_detail = cookie_file
    elif cookie_file:
        cookie_state = "optional"
        cookie_detail = f"Configured path does not exist: {cookie_file}"
    else:
        cookie_state = "optional"
        cookie_detail = "Optional; only needed when TikTok blocks downloads"
    diagnostics.append(
        SourceDiagnostic(name="TikTok Cookie", state=cookie_state, detail=cookie_detail)
    )

    return diagnostics

