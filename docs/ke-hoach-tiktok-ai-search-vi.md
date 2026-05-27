# Ke hoach trien khai Nguon Video TikTok bang AI Search

## 1. Muc tieu

Them logic de `Nguon Video = TikTok` hoat dong tu dong nhu cac nguon video hien tai:

1. Nguoi dung nhap `Video Subject` / `Video Script` nhu binh thuong.
2. Ung dung dung LLM provider dang cau hinh trong phan `Cai Dat LLM` de sinh truy van TikTok phu hop.
3. Ung dung tim cac URL TikTok public bang search provider.
4. Ung dung tai video TikTok public ve local bang `yt-dlp`.
5. Ung dung validate video da tai, bo qua file loi/qua ngan/khong co video stream.
6. Cac file hop le duoc dua vao pipeline hien tai de ghep video, audio, subtitle va tao output cuoi.

Khong yeu cau nguoi dung paste link TikTok thu cong trong MVP.

## 2. Hien trang trong codebase

### 2.1. WebUI

File chinh: `webui/Main.py`

Hien tai dropdown `Video Source` co cac option:

```python
video_sources = [
    (tr("Pexels"), "pexels"),
    (tr("Pixabay"), "pixabay"),
    (tr("Local file"), "local"),
    (tr("TikTok"), "douyin"),
    (tr("Bilibili"), "bilibili"),
    (tr("Xiaohongshu"), "xiaohongshu"),
]
```

Nhung khi bam tao video, WebUI chi cho phep:

```python
if params.video_source not in ["pexels", "pixabay", "local"]:
    st.error(tr("Please Select a Valid Video Source"))
    st.stop()
```

Ket luan:

- TikTok dang hien trong UI nhung value la `douyin`.
- TikTok bi chan tai validation khi tao video.
- `Bilibili` va `Xiaohongshu` cung hien trong UI nhung chua co backend.

### 2.2. Backend material

File chinh:

- `app/services/task.py`
- `app/services/material.py`
- `app/services/video.py`

Luồng hiện tại:

- `video_source == "local"`: goi `video.preprocess_video()`.
- Cac source khac: goi `material.download_videos()`.
- `material.download_videos()` mac dinh dung Pexels, chi doi sang Pixabay neu `source == "pixabay"`.

Rui ro hien tai:

- Neu API client gui `video_source = "tiktok"` truc tiep, backend co the di vao duong `material.download_videos()` va fallback sang Pexels.
- Can validation source ro rang de tranh hanh vi sai.

### 2.3. LLM

File chinh: `app/services/llm.py`

Hien co:

- `_generate_response(prompt)` dung provider hien tai trong `config.app["llm_provider"]`.
- `generate_script()`.
- `generate_terms()` sinh stock-video search terms bang LLM.

Cho TikTok, khong nen dung lai `generate_terms()` y nguyen vi prompt hien tai toi uu cho stock footage bang tieng Anh. Can them prompt rieng de sinh TikTok search queries.

## 3. Kien truc de xuat

### 3.1. Tong quan data flow

```text
WebUI
  -> params.video_source = "tiktok"
  -> tm.start()
  -> task.generate_script()
  -> tiktok.discover_and_download_videos()
      -> LLM sinh TikTok search queries
      -> Search provider tim TikTok URLs
      -> LLM rank URLs theo subject/script
      -> yt-dlp download video public
      -> ffprobe/MoviePy validate file
      -> tra list local mp4 paths
  -> video.combine_videos()
  -> video.generate_video()
  -> storage/tasks/<task_id>/final-1.mp4
```

### 3.2. Nguyen tac

- LLM khong tu browse TikTok. LLM chi sinh query va rank ket qua.
- Search provider co nhiem vu lay URL TikTok public.
- `yt-dlp` co nhiem vu download video tu URL public.
- TikTok material sau khi download phai duoc xu ly nhu local material/cache material.
- Khong fallback sang Pexels khi TikTok fail. Neu TikTok fail thi fail ro rang.
- Khong mac dinh remove watermark.
- Chi tai noi dung public; can canh bao nguoi dung chi dung noi dung co quyen su dung.

## 4. Public config / interface

### 4.1. `config.example.toml`

Them cac key vao section `[app]`:

```toml
# TikTok AI Search Settings
# Use current LLM provider to generate/rank TikTok search queries.
# Search provider finds public TikTok URLs; yt-dlp downloads them.
tiktok_search_provider = "openai_web_search" # "openai_web_search" hoac "serpapi"
tiktok_search_api_key = ""
tiktok_max_search_results = 20
tiktok_max_downloads = 5
tiktok_min_duration = 3
tiktok_openai_web_search_timeout = 300
tiktok_cookie_file = ""
```

Provider `openai_web_search` dung lai setting OpenAI trong phan `Cai Dat LLM`: `openai_api_key`, `openai_base_url`, `openai_model_name`. Provider nay khong can SerpAPI. Read timeout cua request web search duoc cau hinh bang `tiktok_openai_web_search_timeout`, mac dinh `300` giay.

Provider `serpapi` can `tiktok_search_api_key`. Runtime co the doc SerpAPI key tu bien moi truong neu `tiktok_search_api_key` trong `config.toml` de trong:

```bash
export SERPAPI_API_KEY="..."
```

Ten bien moi truong duoc chap nhan: `SERPAPI_API_KEY`, `SERPAPI_KEY`, `TIKTOK_SEARCH_API_KEY`.

Cap nhat comment `video_source`:

```toml
video_source = "pexels" # "pexels", "pixabay", "local", or "tiktok"
```

### 4.2. WebUI

Trong `webui/Main.py`, dropdown source nen thanh:

```python
video_sources = [
    (tr("Pexels"), "pexels"),
    (tr("Pixabay"), "pixabay"),
    (tr("Local file"), "local"),
    (tr("TikTok"), "tiktok"),
]
```

Tam thoi an `Bilibili` va `Xiaohongshu` cho den khi co backend that.

Khi user chon TikTok, hien them setting:

- `TikTok Search Provider`: selectbox voi `openai_web_search` va `serpapi`.
- `TikTok Search API Key`: password input, chi hien/can khi provider la `serpapi`.
- `TikTok Max Search Results`: number input, default `20`, min `5`, max `50`.
- `TikTok Max Downloads`: number input, default `5`, min `1`, max `10`.
- `TikTok Min Duration`: number input, default `3`, min `1`, max `30`.
- `TikTok Cookie File`: text input optional.

Validation khi bam tao video:

```python
allowed_sources = ["pexels", "pixabay", "local", "tiktok"]
if params.video_source not in allowed_sources:
    st.error(tr("Please Select a Valid Video Source"))
    st.stop()

if params.video_source == "tiktok" and provider == "serpapi" and not config.app.get("tiktok_search_api_key", ""):
    st.error(tr("Please Enter the TikTok Search API Key"))
    st.stop()

if params.video_source == "tiktok" and provider == "openai_web_search" and not config.app.get("openai_api_key", ""):
    st.error(tr("Please Enter the OpenAI API Key"))
    st.stop()
```

### 4.3. API

`TaskVideoRequest.video_source` co the giu la string de tranh refactor lon.

Nhung backend phai validate:

```python
VALID_VIDEO_SOURCES = {"pexels", "pixabay", "local", "tiktok"}
```

Neu source khong hop le:

- WebUI: hien loi va stop.
- API: tra `400` voi message ro, vi du `unsupported video_source: <value>`.

## 5. Cac thay doi code can lam

### Task 1: Them dependency `yt-dlp`

Muc tieu:

- Cho phep tai video TikTok public tu URL.

Thay doi:

- Chay:

```bash
uv add yt-dlp
```

- Commit thay doi trong:
  - `pyproject.toml`
  - `uv.lock`

Khong dung shell command `yt-dlp` trong code. Dung Python API:

```python
from yt_dlp import YoutubeDL
```

Ly do:

- De test bang mock de hon.
- Tranh loi quote path/URL tren Windows/macOS/Linux.
- Kiem soat output path va options tot hon.

### Task 2: Tao service TikTok moi

Tao file:

```text
app/services/tiktok.py
```

Trach nhiem:

- Sinh query TikTok bang LLM hien tai.
- Goi search provider de lay URL TikTok.
- Rank candidates bang LLM hien tai.
- Download video bang `yt-dlp`.
- Validate file da download.
- Tra list local mp4 paths cho pipeline.

Interface de xuat:

```python
def discover_and_download_videos(
    task_id: str,
    video_subject: str,
    video_script: str,
    video_language: str,
    search_terms: list[str] | str | None,
    audio_duration: float,
    max_clip_duration: int,
) -> list[str]:
    ...
```

Cac helper nen co:

```python
def generate_tiktok_search_queries(
    video_subject: str,
    video_script: str,
    video_language: str = "",
    amount: int = 8,
) -> list[str]:
    ...

def search_tiktok_urls(queries: list[str], max_results: int) -> list[dict]:
    ...

def rank_tiktok_candidates(
    video_subject: str,
    video_script: str,
    candidates: list[dict],
    max_downloads: int,
) -> list[str]:
    ...

def download_tiktok_video(url: str, task_id: str) -> str:
    ...

def validate_tiktok_video(path: str, min_duration: float) -> float:
    ...

def canonicalize_tiktok_url(url: str) -> str:
    ...
```

Cap nhat sau khi test voi `openai_web_search`:

- TikTok uu tien dung `Video Keywords` giong Pexels/Pixabay.
- Moi keyword duoc build thanh query `"https://www.tiktok.com/@" "/video/" "<keyword>"`.
- Chi fallback sang `generate_tiktok_search_queries()` khi khong co `Video Keywords`.
- Ly do: query dai theo cau tieng Viet de gay `no TikTok candidates found`; keyword ngan/English search terms on dinh hon voi OpenAI web search.
- Cap nhat them: OpenAI web search khong gioi han domain `tiktok.com`, vi search truc tiep tren domain nay hay tra channel/tag/shop thay vi video. App search rong tren web de tim trang/snippet co nhung URL TikTok video that, sau do parser van chi nhan URL `/@creator/video/<numeric_id>`.

### Task 3: LLM prompt cho TikTok query

Prompt cho `generate_tiktok_search_queries()`:

```text
# Role: TikTok Search Query Generator

Generate search queries for finding public TikTok videos that can visually support a short video.

Return only a JSON array of strings.
Each query must be suitable for a web search engine.
Each query should target TikTok video pages.
Prefer concrete visual situations, creator style, product-use context, actions, and hashtags.
Do not include markdown.
Do not include explanations.

Context:
Video subject: ...
Video script: ...
Language: ...

Output example:
[
  "\"https://www.tiktok.com/@\" \"/video/\" \"authentic buyer review skincare\"",
  "\"https://www.tiktok.com/@\" \"/video/\" \"#tiktokmademebuyit honest review\"",
  "\"https://www.tiktok.com/@\" \"/video/\" \"vietnamese creator product review\""
]
```

Parse policy:

- Neu response la JSON array hop le: dung truc tiep.
- Neu response co text bao quanh JSON: dung regex lay array dau tien.
- Neu van loi: retry toi da 5 lan, tuong tu `generate_terms()`.
- Neu fail sau retries: raise `ValueError`.

### Task 4: Search providers

V1 implement 2 provider:

- `openai_web_search`: dung OpenAI Responses API voi tool `web_search`, doc key/model/base URL tu setting OpenAI trong `Cai Dat LLM`.
- `serpapi`: dung SerpAPI Google search.

#### 4.1. OpenAI Web Search

Endpoint:

```text
{openai_base_url_or_default}/responses
```

Payload chinh:

```python
{
    "model": config.app["openai_model_name"],
    "tools": [{"type": "web_search"}],
    "tool_choice": "auto",
    "include": ["web_search_call.action.sources"],
    "input": prompt,
}
```

Ghi chu:

- Khong set `allowed_domains=["tiktok.com"]`, de OpenAI co the tim ca bai viet/snippet ben thu ba co nhung URL TikTok video that.
- Moi query duoc goi rieng. Khi du `max_results` thi dung som, tranh batch lon bi timeout lau.

Parse:

- Lay URL tu `message.content[].annotations[].url`.
- Lay URL tu `web_search_call.action.sources[].url`.
- Lay them URL trong `output_text` neu co.
- Canonicalize va chi giu URL TikTok video hop le.

Validation:

- Provider `openai_web_search` can `openai_api_key` trong `Cai Dat LLM` hoac bien moi truong `OPENAI_API_KEY`.
- Khong can `tiktok_search_api_key`.

#### 4.2. SerpAPI

Endpoint de xuat:

```text
https://serpapi.com/search.json
```

Params:

```python
{
    "engine": "google",
    "q": query,
    "api_key": config.app["tiktok_search_api_key"],
    "num": min(max_results, 20),
}
```

Parse:

- Doc `organic_results`.
- Lay `link`, `title`, `snippet`.
- Lay ca URL TikTok video nam trong `title`/`snippet` cua trang ben thu ba.
- Chi giu URL thoa:
  - host chua `tiktok.com`
  - path co `/video/`
  - video ID la so
  - khong phai `/tag/`, `/music/`, `/discover/`
- Deduplicate bang canonical URL.

Candidate object:

```python
{
    "url": "https://www.tiktok.com/@creator/video/123",
    "title": "...",
    "snippet": "...",
    "query": "..."
}
```

Fallback:

- Neu SerpAPI loi HTTP/network: log error va tiep tuc query ke tiep.
- Neu tat ca query deu loi/khong co candidate: raise `ValueError("no TikTok candidates found")`.

### Task 5: LLM rank candidates

Muc tieu:

- Dung LLM de chon video co kha nang phu hop voi script nhat.

Prompt:

```text
# Role: TikTok Candidate Ranker

You will receive a video subject, video script, and a list of TikTok search results.
Select the URLs that are most likely to provide useful visual material for the final short video.

Return only a JSON array of URL strings.
Do not invent URLs.
Only use URLs from the candidate list.
Prefer videos whose title/snippet match the actual visual scene or creator behavior.
Avoid unrelated celebrity, meme, dance-only, or music-only results unless directly relevant.

Max URLs: ...

Context:
Video subject: ...
Video script: ...

Candidates:
[
  {"url": "...", "title": "...", "snippet": "..."},
  ...
]
```

Fallback:

- Neu LLM rank fail: dung thu tu candidate sau dedupe.
- Neu LLM tra URL khong nam trong candidate: bo qua URL do.

### Task 6: Download bang `yt-dlp`

Output dir:

```text
storage/cache_videos/tiktok/
```

Output filename:

```text
tiktok-<md5(canonical_url)>.mp4
```

Options:

```python
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
```

Neu `tiktok_cookie_file` co gia tri:

```python
ydl_opts["cookiefile"] = tiktok_cookie_file
```

Sau download:

- Tim file output `.mp4`.
- Neu da ton tai va valid thi dung cache, khong download lai.
- Neu download fail thi log va tiep tuc URL ke tiep.

### Task 7: Validate video

Validation toi thieu:

- File ton tai.
- Size > 0.
- MoviePy/ffprobe doc duoc.
- Co video stream.
- Duration >= `max(tiktok_min_duration, max_clip_duration)` neu co du candidate.

Thuc te nen linh hoat:

- Neu video ngan hon `max_clip_duration` nhung >= `tiktok_min_duration`, co the van chap nhan de pipeline loop clip.
- Neu duration < `tiktok_min_duration`: reject.

Tra duration hop le de tinh tong duration da co.

### Task 8: Tich hop vao `task.py`

Thay doi trong `start()`:

Logic terms:

```python
video_terms = ""
if params.video_source in ("pexels", "pixabay"):
    video_terms = generate_terms(task_id, params, video_script)
elif params.video_source == "tiktok":
    video_terms = []
elif params.video_source == "local":
    video_terms = ""
else:
    raise ValueError(...)
```

Logic materials:

```python
if params.video_source == "local":
    ...
elif params.video_source == "tiktok":
    downloaded_videos = tiktok.discover_and_download_videos(...)
elif params.video_source in ("pexels", "pixabay"):
    downloaded_videos = material.download_videos(...)
else:
    raise ValueError(...)
```

Cap nhat task state:

- Neu TikTok khong co candidate/download duoc video: task failed.
- Log message can ro: `failed to discover/download TikTok videos`.

### Task 9: Chan fallback source sai trong `material.py`

Them validation dau `download_videos()`:

```python
if source not in ("pexels", "pixabay"):
    raise ValueError(f"unsupported stock video source: {source}")
```

Ly do:

- Dam bao source la `tiktok`, `douyin`, `bilibili`, `xiaohongshu` khong bi fallback sang Pexels.

### Task 10: Cap nhat WebUI

Thay doi:

- TikTok value thanh `"tiktok"`.
- Remove/an `Bilibili`, `Xiaohongshu` trong dropdown MVP.
- Allowed sources gom `tiktok`.
- Them UI config TikTok khi chon source TikTok.
- Save config bang `config.save_config()` nhu cac setting khac.

Can them i18n keys neu muon:

- `TikTok Search API Key`
- `TikTok Max Search Results`
- `TikTok Max Downloads`
- `TikTok Cookie File`
- `Please Enter the TikTok Search API Key`

### Task 11: Cap nhat docs tieng Viet

Cap nhat file:

```text
docs/huong-dan-su-dung-local-vi.md
```

Noi dung them:

- Cach chon `Nguon Video = TikTok`.
- Cach cau hinh `tiktok_search_api_key`.
- Giai thich LLM sinh query/rank ket qua.
- Giai thich SerpAPI tim link.
- Giai thich `yt-dlp` tai video public.
- Canh bao chi dung video co quyen su dung.
- Cac loi thuong gap:
  - khong co search result
  - `yt-dlp` download fail
  - TikTok chan request/can cookie
  - video qua ngan/khong co stream

## 6. Test plan

### 6.1. Unit tests cho TikTok service

Tao file:

```text
test/services/test_tiktok.py
```

Test cases:

1. `canonicalize_tiktok_url()` normalize URL TikTok video va bo query params.
2. `canonicalize_tiktok_url()` reject URL khong phai TikTok video.
3. Parser SerpAPI chi lay `organic_results` co URL TikTok video hop le.
4. Parser SerpAPI dedupe URL trung.
5. LLM query parser doc JSON array hop le.
6. LLM query parser recover JSON array nam trong text.
7. LLM ranker chi giu URL nam trong candidate list.
8. Ranker fallback ve thu tu candidate neu LLM loi.
9. `download_tiktok_video()` goi `yt_dlp.YoutubeDL` voi options dung.
10. `download_tiktok_video()` dung `cookiefile` khi config co `tiktok_cookie_file`.
11. `validate_tiktok_video()` reject file khong ton tai.
12. `validate_tiktok_video()` reject file co size 0.
13. `validate_tiktok_video()` reject video duration < `tiktok_min_duration`.
14. `discover_and_download_videos()` tiep tuc URL ke tiep neu mot URL download fail.
15. `discover_and_download_videos()` dung khi du `tiktok_max_downloads`.

### 6.2. Unit tests cho task/material

Cap nhat:

```text
test/services/test_task.py
test/services/test_material.py
```

Test cases:

- `video_source="tiktok"` goi `tiktok.discover_and_download_videos()`.
- `video_source="tiktok"` khong goi `material.download_videos()`.
- `video_source="local"` giu behavior hien tai.
- `video_source="pexels"` va `"pixabay"` giu behavior hien tai.
- Source khong hop le raise/fail ro rang.
- `material.download_videos(source="tiktok")` raise `ValueError`.

### 6.3. WebUI validation tests/manual checks

Manual:

1. Chon `Pexels`: neu thieu Pexels key thi bao loi Pexels key nhu hien tai.
2. Chon `Pixabay`: neu thieu Pixabay key thi bao loi Pixabay key nhu hien tai.
3. Chon `Local file`: upload file local va tao video nhu hien tai.
4. Chon `TikTok`: neu thieu `tiktok_search_api_key` thi bao loi TikTok Search API Key.
5. Chon `TikTok`: co API key thi app khong bi chan boi validation source.

### 6.4. Verification commands

Chay:

```bash
uv sync --frozen
uv run python -m unittest test.services.test_tiktok
uv run python -m unittest test.services.test_task
uv run python -m unittest test.services.test_material
uv run python -m unittest test.services.test_video.TestVideoService
uv run python -m compileall app webui main.py
```

Manual acceptance voi API/WebUI:

```bash
uv run python main.py
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false uv run streamlit run ./webui/Main.py \
  --server.headless=true \
  --browser.serverAddress="0.0.0.0" \
  --server.enableCORS=true \
  --browser.gatherUsageStats=false
```

Sau do:

- Mo `http://127.0.0.1:8501`.
- Chon `Nguon Video = TikTok`.
- Nhap `Video Subject` va/hoac `Video Script`.
- Cau hinh TikTok Search API key.
- Tao video.
- Xac nhan log co cac buoc:
  - generate TikTok queries
  - search TikTok URLs
  - rank TikTok candidates
  - download TikTok video
  - validate material
  - combine video
  - generate final video
- Xac nhan final output mo duoc:

```text
http://127.0.0.1:8080/tasks/<task_id>/final-1.mp4
```

## 7. Acceptance criteria

Tinh nang dat yeu cau khi:

1. WebUI co `Nguon Video = TikTok` va khong bi validation chan sai.
2. User khong can paste URL TikTok thu cong.
3. LLM provider hien tai duoc dung de sinh query va rank candidate.
4. Search provider lay duoc TikTok public video URLs.
5. `yt-dlp` tai duoc it nhat mot video public hop le.
6. Video TikTok hop le duoc dua vao pipeline hien tai va tao duoc `final-1.mp4`.
7. Neu TikTok search/download fail, app bao loi ro rang va khong fallback sang Pexels.
8. Existing flows `pexels`, `pixabay`, `local` khong bi regression.
9. Unit tests moi va cac test lien quan pass.

## 8. Pham vi khong lam trong MVP

- Khong implement TikTok Research API.
- Khong implement Content Posting API de dang video len TikTok.
- Khong remove watermark.
- Khong download private/restricted content.
- Khong crawl TikTok profile/feed hang loat.
- Khong implement Bilibili/Xiaohongshu/Douyin.
- Khong tu dong xin/cap quyen TikTok developer.

## 9. Rui ro va giam thieu

### 9.1. TikTok thay doi anti-bot / HTML

Rui ro:

- `yt-dlp` co the loi khi TikTok thay doi behavior.

Giam thieu:

- Log ro URL fail.
- Cho cau hinh `tiktok_cookie_file`.
- Cache file da tai thanh cong.
- Khong lam task fail ngay khi mot URL fail; thu URL tiep theo.

### 9.2. Search result khong lien quan

Rui ro:

- Search provider tra ve video khong phu hop.

Giam thieu:

- LLM sinh query cu the hon.
- LLM rank candidates dua tren title/snippet.
- Deduplicate va gioi han so download.

### 9.3. Ban quyen / dieu khoan nen tang

Rui ro:

- Video TikTok public khong mac dinh duoc phep tai/su dung lai.

Giam thieu:

- Docs canh bao chi dung noi dung co quyen su dung.
- Khong remove watermark.
- Khong bypass private/restricted content.

### 9.4. LLM output sai format

Rui ro:

- LLM tra markdown/text thay vi JSON.

Giam thieu:

- Parse JSON array truc tiep.
- Fallback regex lay JSON array.
- Retry toi da 5 lan.
- Fail ro rang neu khong parse duoc.

## 10. Thu tu trien khai de xuat

1. Them dependency `yt-dlp`.
2. Viet unit tests cho TikTok URL canonicalizer va SerpAPI parser.
3. Implement `app/services/tiktok.py` phan URL/search parser.
4. Viet tests cho LLM query parser/ranker.
5. Implement LLM query/ranker logic.
6. Viet tests cho download wrapper bang mock `yt_dlp.YoutubeDL`.
7. Implement download/cache/validate.
8. Viet tests cho `task.py` routing theo `video_source`.
9. Tich hop TikTok vao `task.py`.
10. Them validation source trong `material.py`.
11. Sua WebUI dropdown/validation/config input.
12. Cap nhat docs tieng Viet.
13. Chay full verification commands.
14. Manual test tao video TikTok tren WebUI.
