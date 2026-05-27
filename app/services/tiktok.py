import glob
import json
import os
import re
from urllib.parse import urlparse, urlunparse

import requests
from loguru import logger
from moviepy.video.io.VideoFileClip import VideoFileClip
from yt_dlp import YoutubeDL

from app.config import config
from app.services import llm, material
from app.utils import utils

_MAX_LLM_RETRIES = 5
_SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
_SEARCH_API_KEY_ENV_NAMES = (
    "SERPAPI_API_KEY",
    "SERPAPI_KEY",
    "TIKTOK_SEARCH_API_KEY",
)
_OPENAI_API_KEY_ENV_NAMES = ("OPENAI_API_KEY",)
_OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_OPENAI_WEB_SEARCH_PROVIDER = "openai_web_search"
_SERPAPI_PROVIDER = "serpapi"
_SUPPORTED_SEARCH_PROVIDERS = {_SERPAPI_PROVIDER, _OPENAI_WEB_SEARCH_PROVIDER}


def _as_int(value, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default

    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def _as_float(value, default: float, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default

    if minimum is not None:
        result = max(minimum, result)
    return result


def _tiktok_cache_dir() -> str:
    cache_dir = utils.storage_dir(os.path.join("cache_videos", "tiktok"))
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_tiktok_search_api_key() -> str:
    api_key = (config.app.get("tiktok_search_api_key") or "").strip()
    if api_key:
        return api_key

    for env_name in _SEARCH_API_KEY_ENV_NAMES:
        api_key = (os.environ.get(env_name) or "").strip()
        if api_key:
            return api_key

    return ""


def get_openai_api_key() -> str:
    api_key = (config.app.get("openai_api_key") or "").strip()
    if api_key:
        return api_key

    for env_name in _OPENAI_API_KEY_ENV_NAMES:
        api_key = (os.environ.get(env_name) or "").strip()
        if api_key:
            return api_key

    return ""


def get_tiktok_search_provider() -> str:
    provider = (config.app.get("tiktok_search_provider", _SERPAPI_PROVIDER) or "").strip()
    return provider or _SERPAPI_PROVIDER


def validate_tiktok_search_config() -> None:
    provider = get_tiktok_search_provider()
    if provider not in _SUPPORTED_SEARCH_PROVIDERS:
        raise ValueError(f"unsupported TikTok search provider: {provider}")
    if provider == _SERPAPI_PROVIDER and not get_tiktok_search_api_key():
        raise ValueError("tiktok_search_api_key is not set")
    if provider == _OPENAI_WEB_SEARCH_PROVIDER and not get_openai_api_key():
        raise ValueError("openai_api_key is not set")


def _is_tiktok_host(hostname: str) -> bool:
    hostname = (hostname or "").lower()
    return hostname == "tiktok.com" or hostname.endswith(".tiktok.com")


def canonicalize_tiktok_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid TikTok URL: {url}")

    hostname = parsed.hostname or ""
    path = re.sub(r"/+", "/", parsed.path or "").rstrip("/")
    if not _is_tiktok_host(hostname) or "/video/" not in path:
        raise ValueError(f"not a TikTok video URL: {url}")

    lowered_path = path.lower()
    if any(blocked in lowered_path for blocked in ("/tag/", "/music/", "/discover/")):
        raise ValueError(f"not a TikTok video URL: {url}")

    video_id_match = re.search(r"/@[^/]+/video/([^/]+)$", path)
    if not video_id_match or not video_id_match.group(1).isdigit():
        raise ValueError(f"not a TikTok video URL: {url}")

    return urlunparse(("https", parsed.netloc.lower(), path, "", "", ""))


def extract_json_string_array(response: str) -> list[str]:
    if not isinstance(response, str):
        raise ValueError("response is not text")

    candidates = [response.strip()]
    match = re.search(r"\[[\s\S]*\]", response)
    if match:
        candidates.append(match.group())

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return [item.strip() for item in value if item.strip()]

    raise ValueError("response does not contain a JSON string array")


def generate_tiktok_search_queries(
    video_subject: str,
    video_script: str,
    video_language: str = "",
    amount: int = 8,
) -> list[str]:
    prompt = f"""
# Role: TikTok Search Query Generator

Generate search queries for finding public TikTok videos that can visually support a short video.

Return only a JSON array of strings.
Each query must be suitable for a web search engine.
Each query should target TikTok video pages.
Prefer concrete visual situations, creator style, product-use context, actions, and hashtags.
Do not include markdown.
Do not include explanations.
Return at most {amount} queries.

Context:
Video subject: {video_subject}
Video script: {video_script}
Language: {video_language}

Output example:
[
  "\"https://www.tiktok.com/@\" \"/video/\" \"authentic buyer review skincare\"",
  "\"https://www.tiktok.com/@\" \"/video/\" \"#tiktokmademebuyit honest review\"",
  "\"https://www.tiktok.com/@\" \"/video/\" \"vietnamese creator product review\""
]
""".strip()

    last_error = None
    for attempt in range(_MAX_LLM_RETRIES):
        response = llm._generate_response(prompt)
        if response.startswith("Error:"):
            last_error = response
        else:
            try:
                queries = extract_json_string_array(response)
                if queries:
                    logger.info(f"generated TikTok search queries: {queries}")
                    return queries[:amount]
            except ValueError as exc:
                last_error = str(exc)

        if attempt < _MAX_LLM_RETRIES - 1:
            logger.warning(
                f"failed to generate TikTok search queries, trying again... {attempt + 1}"
            )

    raise ValueError(f"failed to generate TikTok search queries: {last_error}")


def build_tiktok_search_queries_from_terms(
    search_terms: list[str] | str | None,
    amount: int = 8,
) -> list[str]:
    if not search_terms:
        return []

    if isinstance(search_terms, str):
        terms = [term.strip() for term in re.split(r"[,，]", search_terms)]
    else:
        terms = [str(term).strip() for term in search_terms]

    queries = []
    seen_queries = set()
    for term in terms:
        if not term:
            continue
        if "site:tiktok.com" in term or "tiktok.com" in term:
            query = term
        else:
            query = _build_openai_tiktok_video_search_query(term)
        if query in seen_queries:
            continue
        seen_queries.add(query)
        queries.append(query)
        if len(queries) >= amount:
            break

    return queries


def parse_serpapi_results(payload: dict, query: str) -> list[dict]:
    candidates = []
    seen_urls = set()

    def append_candidate(url: str, title: str = "", snippet: str = "") -> None:
        try:
            canonical_url = canonicalize_tiktok_url(url)
        except ValueError:
            return

        if canonical_url in seen_urls:
            return

        seen_urls.add(canonical_url)
        candidates.append(
            {
                "url": canonical_url,
                "title": title or "",
                "snippet": snippet or "",
                "query": query,
            }
        )

    for result in (payload or {}).get("organic_results", []):
        link = result.get("link", "")
        title = result.get("title", "") or ""
        snippet = result.get("snippet", "") or ""
        append_candidate(link, title=title, snippet=snippet)
        for embedded_url in _extract_tiktok_candidates_from_text(
            f"{title}\n{snippet}"
        ):
            append_candidate(embedded_url, title=title, snippet=snippet)

    return candidates


def _extract_tiktok_candidates_from_text(text: str) -> list[str]:
    if not isinstance(text, str) or not text:
        return []

    urls = []
    for match in re.finditer(r"https?://[^\s<>\]\)\"']+", text):
        raw_url = match.group(0).rstrip(".,;:")
        try:
            urls.append(canonicalize_tiktok_url(raw_url))
        except ValueError:
            continue
    return urls


def parse_openai_web_search_response(payload: dict, query: str) -> list[dict]:
    candidates = []
    seen_urls = set()

    def append_candidate(url: str, title: str = "", snippet: str = "") -> None:
        try:
            canonical_url = canonicalize_tiktok_url(url)
        except ValueError:
            return
        if canonical_url in seen_urls:
            return
        seen_urls.add(canonical_url)
        candidates.append(
            {
                "url": canonical_url,
                "title": title or "",
                "snippet": snippet or "",
                "query": query,
                "provider": _OPENAI_WEB_SEARCH_PROVIDER,
            }
        )

    output_items = (payload or {}).get("output", [])
    if isinstance(output_items, list):
        for item in output_items:
            if not isinstance(item, dict):
                continue

            action = item.get("action") or {}
            sources = action.get("sources") if isinstance(action, dict) else None
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict):
                        append_candidate(
                            source.get("url", ""),
                            title=source.get("title", ""),
                            snippet=source.get("snippet", ""),
                        )

            content_items = item.get("content", [])
            if isinstance(content_items, list):
                for content in content_items:
                    if not isinstance(content, dict):
                        continue
                    text = content.get("text", "")
                    annotations = content.get("annotations", [])
                    if isinstance(annotations, list):
                        for annotation in annotations:
                            if isinstance(annotation, dict):
                                append_candidate(
                                    annotation.get("url", ""),
                                    title=annotation.get("title", ""),
                                )
                    for url in _extract_tiktok_candidates_from_text(text):
                        append_candidate(url, snippet=text)

    output_text = (payload or {}).get("output_text", "")
    for url in _extract_tiktok_candidates_from_text(output_text):
        append_candidate(url, snippet=output_text)

    return candidates


def _search_tiktok_urls_with_serpapi(queries: list[str], max_results: int) -> list[dict]:
    api_key = get_tiktok_search_api_key()
    if not api_key:
        raise ValueError("tiktok_search_api_key is not set")

    per_query_results = max(1, min(_as_int(max_results, 20), 20))
    candidates = []
    seen_urls = set()
    for query in queries:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": per_query_results,
        }
        logger.info(f"searching TikTok URLs via SerpAPI: {query}")
        try:
            response = requests.get(
                _SERPAPI_ENDPOINT,
                params=params,
                proxies=config.proxy,
                verify=material._get_tls_verify(),
                timeout=(30, 60),
            )
            response.raise_for_status()
            parsed_results = parse_serpapi_results(response.json(), query=query)
        except Exception as exc:
            logger.error(f"failed to search TikTok URLs for query '{query}': {str(exc)}")
            continue

        for candidate in parsed_results:
            if candidate["url"] in seen_urls:
                continue
            seen_urls.add(candidate["url"])
            candidates.append(candidate)
            if len(candidates) >= max_results:
                logger.info(f"found TikTok candidates: {len(candidates)}")
                return candidates

    if not candidates:
        raise ValueError("no TikTok candidates found")

    logger.info(f"found TikTok candidates: {len(candidates)}")
    return candidates


def _openai_responses_endpoint() -> str:
    base_url = (config.app.get("openai_base_url") or "").strip() or _OPENAI_DEFAULT_BASE_URL
    return f"{base_url.rstrip('/')}/responses"


def _build_openai_tiktok_video_search_query(query: str) -> str:
    query = (query or "").strip()
    if not query:
        return ""
    if '"https://www.tiktok.com/@"' in query and '"/video/"' in query:
        return query

    cleaned_query = re.sub(r"(?i)site:tiktok\.com/?@?", " ", query)
    cleaned_query = re.sub(r"(?i)inurl:/video", " ", cleaned_query)
    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
    quoted_query = (cleaned_query or query).replace('"', '\\"')
    return f'"https://www.tiktok.com/@" "/video/" "{quoted_query}"'


def _build_openai_tiktok_search_prompt(query: str, max_results: int) -> str:
    search_query = _build_openai_tiktok_video_search_query(query)
    return f"""
Search the web broadly for pages that mention actual TikTok video URLs relevant to this query.

Query:
{search_query}

Return only actual TikTok video URLs in this format:
https://www.tiktok.com/@creator/video/1234567890123456789

Requirements:
- Return public TikTok video pages only.
- Every returned URL must be an actual web result with a numeric video ID.
- If a result page contains a TikTok video URL in the snippet or page text, return that TikTok video URL.
- Do not return TikTok channel, tag, search, music, shop, live, PDF, or profile pages.
- Do not invent URLs.
- Prefer visually useful short-video material.
- Return at most {max_results} relevant URLs.
""".strip()


def _search_tiktok_urls_with_openai_web_search(
    queries: list[str],
    max_results: int,
) -> list[dict]:
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("openai_api_key is not set")

    model_name = config.app.get("openai_model_name") or "gpt-4o-mini"
    max_results = _as_int(max_results, 20, minimum=1, maximum=50)
    candidates = []
    seen_urls = set()
    clean_queries = [query for query in queries if query]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    read_timeout = _as_int(
        config.app.get("tiktok_openai_web_search_timeout", 300),
        default=300,
        minimum=60,
        maximum=900,
    )
    logger.info(f"searching TikTok URLs via OpenAI web search: {clean_queries}")

    for query in clean_queries:
        per_query_limit = min(max_results - len(candidates), 5)
        payload = {
            "model": model_name,
            "tools": [{"type": "web_search"}],
            "tool_choice": "auto",
            "include": ["web_search_call.action.sources"],
            "input": _build_openai_tiktok_search_prompt(
                query=query,
                max_results=per_query_limit,
            ),
        }
        try:
            response = requests.post(
                _openai_responses_endpoint(),
                headers=headers,
                json=payload,
                proxies=config.proxy,
                verify=material._get_tls_verify(),
                timeout=(30, read_timeout),
            )
            response.raise_for_status()
            parsed_results = parse_openai_web_search_response(response.json(), query=query)
        except Exception as exc:
            logger.error(f"failed to search TikTok URLs with OpenAI: {str(exc)}")
            parsed_results = []

        for candidate in parsed_results:
            if candidate["url"] in seen_urls:
                continue
            seen_urls.add(candidate["url"])
            candidates.append(candidate)
            if len(candidates) >= max_results:
                logger.info(f"found TikTok candidates: {len(candidates)}")
                return candidates

        logger.info(
            "TikTok OpenAI web search query returned "
            f"{len(parsed_results)} candidates: {query}"
        )

    if not candidates:
        raise ValueError("no TikTok candidates found")

    logger.info(f"found TikTok candidates: {len(candidates)}")
    return candidates


def search_tiktok_urls(queries: list[str], max_results: int) -> list[dict]:
    provider = get_tiktok_search_provider()
    if provider == _SERPAPI_PROVIDER:
        return _search_tiktok_urls_with_serpapi(queries=queries, max_results=max_results)
    if provider == _OPENAI_WEB_SEARCH_PROVIDER:
        return _search_tiktok_urls_with_openai_web_search(
            queries=queries,
            max_results=max_results,
        )

    raise ValueError(f"unsupported TikTok search provider: {provider}")


def rank_tiktok_candidates(
    video_subject: str,
    video_script: str,
    candidates: list[dict],
    max_downloads: int,
) -> list[str]:
    if not candidates:
        return []

    canonical_candidates = [candidate["url"] for candidate in candidates]
    allowed_urls = set(canonical_candidates)
    prompt_candidates = [
        {
            "url": candidate.get("url", ""),
            "title": candidate.get("title", ""),
            "snippet": candidate.get("snippet", ""),
        }
        for candidate in candidates
    ]
    prompt = f"""
# Role: TikTok Candidate Ranker

You will receive a video subject, video script, and a list of TikTok search results.
Select the URLs that are most likely to provide useful visual material for the final short video.

Return only a JSON array of URL strings.
Do not invent URLs.
Only use URLs from the candidate list.
Prefer videos whose title/snippet match the actual visual scene or creator behavior.
Avoid unrelated celebrity, meme, dance-only, or music-only results unless directly relevant.

Max URLs: {max_downloads}

Context:
Video subject: {video_subject}
Video script: {video_script}

Candidates:
{json.dumps(prompt_candidates, ensure_ascii=False, indent=2)}
""".strip()

    try:
        response = llm._generate_response(prompt)
        ranked_urls = extract_json_string_array(response)
        filtered = []
        for url in ranked_urls:
            try:
                canonical_url = canonicalize_tiktok_url(url)
            except ValueError:
                continue
            if canonical_url in allowed_urls and canonical_url not in filtered:
                filtered.append(canonical_url)
            if len(filtered) >= max_downloads:
                break
        if filtered:
            logger.info(f"ranked TikTok candidates: {filtered}")
            return filtered
    except Exception as exc:
        logger.warning(f"failed to rank TikTok candidates with LLM: {str(exc)}")

    return canonical_candidates[:max_downloads]


def download_tiktok_video(url: str, task_id: str) -> str:
    canonical_url = canonicalize_tiktok_url(url)
    cache_dir = _tiktok_cache_dir()
    file_stem = f"tiktok-{utils.md5(canonical_url)}"
    expected_path = os.path.join(cache_dir, f"{file_stem}.mp4")

    if os.path.exists(expected_path) and os.path.getsize(expected_path) > 0:
        logger.info(f"TikTok video already exists: {expected_path}")
        return expected_path

    output_template = os.path.join(cache_dir, f"{file_stem}.%(ext)s")
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

    logger.info(f"downloading TikTok video: {canonical_url}")
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([canonical_url])

    downloaded_files = glob.glob(os.path.join(cache_dir, f"{file_stem}.*"))
    mp4_files = [file for file in downloaded_files if file.lower().endswith(".mp4")]
    if mp4_files:
        return mp4_files[0]

    raise ValueError(f"failed to find downloaded TikTok video: {canonical_url}")


def validate_tiktok_video(path: str, min_duration: float) -> float:
    if not os.path.exists(path):
        raise ValueError(f"TikTok video does not exist: {path}")
    if os.path.getsize(path) <= 0:
        raise ValueError(f"TikTok video is empty: {path}")

    clip = None
    try:
        clip = VideoFileClip(path)
        duration = float(getattr(clip, "duration", 0) or 0)
        fps = float(getattr(clip, "fps", 0) or 0)
        if duration <= 0 or fps <= 0:
            raise ValueError(f"TikTok video has no valid video stream: {path}")
        if duration < min_duration:
            raise ValueError(
                f"TikTok video is too short: {duration:.2f}s < {min_duration:.2f}s"
            )
        return duration
    finally:
        if clip is not None:
            try:
                clip.close()
            except Exception as exc:
                logger.warning(f"failed to close TikTok video clip: {path}, error: {str(exc)}")


def discover_and_download_videos(
    task_id: str,
    video_subject: str,
    video_script: str,
    video_language: str,
    search_terms: list[str] | str | None,
    audio_duration: float,
    max_clip_duration: int,
) -> list[str]:
    logger.info("\n\n## discovering TikTok videos with AI search")
    max_search_results = _as_int(
        config.app.get("tiktok_max_search_results", 20),
        default=20,
        minimum=5,
        maximum=50,
    )
    max_downloads = _as_int(
        config.app.get("tiktok_max_downloads", 5),
        default=5,
        minimum=1,
        maximum=10,
    )
    min_duration = _as_float(
        config.app.get("tiktok_min_duration", 3),
        default=3,
        minimum=1,
    )

    queries = build_tiktok_search_queries_from_terms(search_terms=search_terms, amount=8)
    if queries:
        logger.info(f"generated TikTok search queries from video terms: {queries}")
    else:
        queries = generate_tiktok_search_queries(
            video_subject=video_subject,
            video_script=video_script,
            video_language=video_language,
            amount=8,
        )
    candidates = search_tiktok_urls(queries=queries, max_results=max_search_results)
    ranked_urls = rank_tiktok_candidates(
        video_subject=video_subject,
        video_script=video_script,
        candidates=candidates,
        max_downloads=max_downloads,
    )

    downloaded_paths = []
    downloaded_duration = 0.0
    for url in ranked_urls:
        if len(downloaded_paths) >= max_downloads:
            break
        try:
            video_path = download_tiktok_video(url=url, task_id=task_id)
            duration = validate_tiktok_video(video_path, min_duration=min_duration)
        except Exception as exc:
            logger.error(f"failed to download/validate TikTok video: {url}, error: {str(exc)}")
            continue

        downloaded_paths.append(video_path)
        downloaded_duration += min(duration, max_clip_duration)
        if downloaded_duration >= audio_duration:
            break

    if not downloaded_paths:
        raise ValueError("failed to discover/download TikTok videos")

    logger.success(f"downloaded TikTok videos: {len(downloaded_paths)}")
    return downloaded_paths
