import glob
import ipaddress
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests
from loguru import logger
from moviepy import VideoFileClip
from yt_dlp import YoutubeDL

from app.config import config
from app.services import material
from app.services import video as video_service
from app.utils import utils

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
DIRECT_DOWNLOAD_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS


def _task_dir(task_id: str) -> Path:
    task_dir = Path(utils.task_dir(task_id))
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def _safe_video_extension(filename: str) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"unsupported source video extension: {extension or '<empty>'}"
        )
    return extension


def _validate_public_http_url(url: str) -> str:
    cleaned = (url or "").strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("source video URL must be http(s)")

    host = (parsed.hostname or "").strip().lower()
    if host in {"localhost", "0.0.0.0"}:
        raise ValueError("source video URL must not target a private host")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip and (ip.is_private or ip.is_loopback or ip.is_link_local):
        raise ValueError("source video URL must not target a private host")

    return cleaned


def validate_source_video(path: str) -> dict:
    video_path = Path(path)
    if not video_path.exists():
        raise ValueError(f"source video does not exist: {path}")
    if video_path.stat().st_size <= 0:
        raise ValueError(f"source video is empty: {path}")

    clip = None
    try:
        clip = VideoFileClip(str(video_path))
        duration = float(getattr(clip, "duration", 0) or 0)
        fps = float(getattr(clip, "fps", 0) or 0)
        width, height = clip.size
        if duration <= 0 or fps <= 0:
            raise ValueError(f"source video has no valid video stream: {path}")
        if getattr(clip, "audio", None) is None:
            raise ValueError(f"source video has no audio track: {path}")
        return {
            "duration": duration,
            "fps": fps,
            "width": int(width),
            "height": int(height),
        }
    finally:
        if clip is not None:
            try:
                clip.close()
            except Exception as exc:
                logger.warning(f"failed to close source video clip: {path}, error: {exc}")


def persist_uploaded_source_video(task_id: str, uploaded_file) -> str:
    extension = _safe_video_extension(getattr(uploaded_file, "name", ""))
    source_path = _task_dir(task_id) / f"source{extension}"
    with source_path.open("wb") as output:
        output.write(uploaded_file.getbuffer())
    validate_source_video(str(source_path))
    return str(source_path)


def _direct_download(task_id: str, url: str) -> str:
    extension = _safe_video_extension(urlparse(url).path)
    output_path = _task_dir(task_id) / f"source-download{extension}"
    response = requests.get(
        url,
        stream=True,
        proxies=config.proxy,
        verify=material._get_tls_verify(),
        timeout=(30, 240),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    with output_path.open("wb") as output:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                output.write(chunk)
    validate_source_video(str(output_path))
    return str(output_path)


def _download_with_ytdlp(task_id: str, url: str) -> str:
    task_dir = _task_dir(task_id)
    output_template = str(task_dir / "source-download.%(ext)s")
    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 2,
        "socket_timeout": 30,
    }
    cookie_file = (config.app.get("tiktok_cookie_file") or "").strip()
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    candidates = [
        item
        for item in glob.glob(str(task_dir / "source-download.*"))
        if Path(item).suffix.lower() in ALLOWED_VIDEO_EXTENSIONS
    ]
    if not candidates:
        raise ValueError(f"failed to download source video: {url}")
    source_path = candidates[0]
    validate_source_video(source_path)
    return source_path


def download_source_video_url(task_id: str, url: str) -> str:
    cleaned_url = _validate_public_http_url(url)
    extension = Path(urlparse(cleaned_url).path).suffix.lower()
    if extension in DIRECT_DOWNLOAD_EXTENSIONS:
        try:
            return _direct_download(task_id, cleaned_url)
        except Exception as exc:
            logger.warning(f"direct source video download failed, trying yt-dlp: {exc}")
    return _download_with_ytdlp(task_id, cleaned_url)


def extract_audio(video_path: str, output_audio_path: str) -> str:
    command = [
        video_service.get_ffmpeg_binary(),
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        output_audio_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        error_message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(error_message or "failed to extract source audio")
    return output_audio_path
