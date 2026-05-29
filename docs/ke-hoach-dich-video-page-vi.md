# Ke Hoach Trien Khai Page Dich Video Rieng

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Them mot page rieng trong Studio de dich/lồng tiếng video co san: user upload video hoac dan link de tai, he thong transcribe audio goc, dich noi dung, tao voice moi, render video voi phu de va style thuong hieu.

**Architecture:** Khong nhet flow dich video vao `Create`; tao workflow rieng gom page Streamlit moi, state rieng, background job rieng va service backend rieng. Tai su dung cac component da co cho `Giong doc & am thanh`, `Phu de & thuong hieu`, `render_jobs` pattern, `voice.tts`, `subtitle.create`, `video.generate_video` style rendering, nhung them service moi de transcribe/dich/source-video/render existing video.

**Tech Stack:** Streamlit 1.45, Python 3.11, MoviePy 2.1.2, ffmpeg, yt-dlp 2026.3.17, faster-whisper 1.1.0, Loguru, current LLM provider trong `config.app`, unittest, Streamlit AppTest.

---

## 1. Yeu cau san pham

### 1.1. Flow mong muon

User can co mot page moi, tach khoi flow `Create video`.

Flow page moi:

```text
Dich video
  1. Video goc
     - Upload file video local
     - Hoac dan URL public de he thong tu tai video
  2. Dich noi dung
     - Chon ngon ngu goc: Auto Detect hoac ngon ngu cu the
     - Chon ngon ngu dich/voice target
     - Transcribe audio goc bang Whisper
     - Dich transcript bang LLM dang cau hinh
  3. Giong doc & am thanh
     - Dung lai flow TTS server, voice, voice preview, volume/rate, BGM
  4. Phu de & thuong hieu
     - Dung lai subtitle preset, font, mau, vi tri, stroke
  5. Xuat ban dich
     - Tao audio dich bang TTS
     - Gan audio dich vao video goc, tat audio goc
     - Chen phu de dich
     - Xuat final mp4
```

### 1.2. Pham vi MVP

MVP nen lam dung va gon:

- Tao page `Translate` / `Dich video` rieng trong Studio navigation.
- Input video bang upload file hoac public URL.
- URL downloader dung `yt-dlp` cho cac site video public; fallback direct download cho URL file video truc tiep `.mp4/.mov/.mkv/.webm`.
- Transcribe audio goc bang `app.services.subtitle.create()` / faster-whisper.
- Dich transcript sang target language bang current LLM provider trong `app.services.llm`.
- Tao voice dich bang `app.services.voice.tts()`.
- Tao subtitle dich dong bo theo TTS subtitle maker neu co; fallback dung timing transcript goc voi text da dich.
- Render video goc voi audio dich va subtitle style da chon.
- Task chay background, co progress/log/output giong Create page.
- Projects page nhan dien duoc task workflow `translate_video`.

Khong dua vao MVP:

- Lip sync.
- Tach vocal/music rieng khoi video goc.
- Giu timing tung cau voi TTS per-segment chat luong cao.
- Chinh sua transcript bang UI phuc tap truoc render.
- Multi-video batch.
- Auto remove watermark.
- Dich subtitle tu file SRT upload rieng.

## 2. Hien trang codebase

### 2.1. WebUI Studio

Entrypoint:

- `webui/Main.py`: boot Studio, apply theme, render navigation.
- `webui/studio/navigation.py`: khai bao cac page `Create`, `Projects`, `Assets`, `Brand`, `Settings`.
- `webui/studio/pages/create.py`: flow tao video hien tai.
- `webui/studio/state.py`: `StudioCreateState`, `StudioRenderSnapshot`, `build_video_params()`.
- `webui/studio/render_jobs.py`: background render job cho Create page, active task persistence, log file `studio-render.log`.
- `webui/studio/components/audio_settings.py`: TTS server, voice, play voice, audio advanced.
- `webui/studio/components/subtitle_settings.py`: subtitle preset, enable subtitle, font/color/position, advanced subtitle.
- `webui/studio/components/source_settings.py`: source Pexels/Pixabay/Local/TikTok va advanced source.
- `webui/studio/validators.py`: validate render request cho Create.

Create page hien tai da co single-page layout:

```text
Nội dung
Nguồn video
Nâng cao
Giọng đọc & âm thanh
Phụ đề & thương hiệu
Xuất video sticky rail
```

Page dich video nen reuse pattern nay, nhung khong reuse `build_video_params()` vi create pipeline tao video moi tu subject/script/source footage, con translate pipeline can bat dau tu mot source video co san.

### 2.2. Backend create pipeline hien tai

`webui/studio/render_jobs.start_render_job()`:

```text
persist uploaded local materials/audio
-> build_video_params(state)
-> validate_render_request()
-> save_create_state()
-> set studio_active_render_task_id
-> background thread _run_render_job()
-> tm.start(task_id, params)
```

`app/services/task.py:start()`:

```text
1. generate_script()
2. generate_terms()
3. generate_audio()
4. generate_subtitle()
5. get_video_materials()
6. generate_final_videos()
7. optional cross-post
```

`task.py` phu hop voi tao video moi, khong phu hop voi dich video vi no luon xem `video_script` la noi dung de tao voice va dung `video_source` de lay footage moi.

### 2.3. Cac building blocks co the tai su dung

- `app.services.subtitle.create(audio_file, subtitle_file)`: transcribe audio bang faster-whisper va ghi SRT.
- `app.services.subtitle.file_to_subtitles(filename)`: doc SRT thanh list `(index, times, text)`.
- `app.services.voice.tts(...)`: tao TTS audio va subtitle maker.
- `app.services.voice.create_subtitle(...)`: tao SRT tu TTS subtitle maker.
- `app.services.video.generate_video(...)`: gan audio/subtitle/BGM vao video va xuat final mp4.
- `app.services.video.get_ffmpeg_binary()`: resolve ffmpeg.
- `app.services.tiktok.download_tiktok_video(...)`: dung `yt-dlp` cho TikTok URL.
- `app.services.material.save_video(...)`: direct download URL file video, nhung hien chi validate bang MoviePy va khong phu hop cho generic URL co playlist/player page.
- `app.services.state.sm.state`: task store in-memory/Redis.
- `webui/studio/render_jobs.py`: pattern log/progress/background cho Streamlit.

## 3. Kien truc de xuat

### 3.1. File moi / file can sua

**Tao moi:**

- `app/services/source_video.py`
  - Persist uploaded source video.
  - Download public video URL.
  - Validate source video.
  - Extract audio track tu video goc.

- `app/services/translate_video.py`
  - Orchestrate pipeline dich video.
  - Transcribe source audio.
  - Translate transcript segments bang LLM.
  - Generate translated voice/subtitle.
  - Render final translated video.

- `webui/studio/pages/translate.py`
  - Page UI rieng cho flow dich video.

- `webui/studio/translate_jobs.py`
  - Background job/persistent snapshot rieng cho page Translate.
  - Co the copy pattern tu `render_jobs.py`, nhung dung session keys rieng.

- `test/services/test_source_video.py`
- `test/services/test_translate_video.py`
- `test/webui/test_studio_translate_page.py`

**Sua:**

- `app/models/schema.py`
  - Them `TranslateVideoParams`.

- `app/services/video.py`
  - Them helper render existing video an toan, co resize/crop/pad theo aspect neu can.

- `app/services/llm.py`
  - Them ham translate transcript segments.

- `webui/studio/state.py`
  - Them `StudioTranslateState`, serialize/deserialize/load/save/build params.

- `webui/studio/navigation.py`
  - Them page `Translate`.

- `webui/studio/components/audio_settings.py`
  - Giam coupling voi `StudioCreateState`; doi type hint sang protocol/base state hoac duck typing.

- `webui/studio/components/subtitle_settings.py`
  - Giam coupling voi `StudioCreateState`; cho phep dung voi `StudioTranslateState`.

- `webui/studio/pages/projects.py`
  - Hien workflow translate trong task list/detail.

- `webui/studio/theme.py`
  - Them marker/style rieng neu page Translate can rail sticky va preview frame rieng.

### 3.2. Ly do khong chen vao `app/services/task.py`

Khong nen mo rong `task.start()` thanh pipeline da muc dich, vi:

- Create pipeline can `video_subject`, `video_terms`, footage source, concat mode.
- Translate pipeline can source video, transcribe, translate, dub, preserve/render existing video.
- Dung chung `task.start()` se tao nhieu branch `if workflow == ...`, lam tang rui ro regression cho Create.
- Tach `translate_video.py` giup test call order va loi tung buoc ro hon.

## 4. Data model

### 4.1. `TranslateVideoParams`

Them vao `app/models/schema.py`:

```python
class TranslateVideoParams(BaseModel):
    source_video_path: Optional[str] = None
    source_video_url: Optional[str] = None
    source_language: Optional[str] = ""
    target_language: str = "vi-VN"
    translated_script: Optional[str] = ""

    video_aspect: Optional[str] = "source"  # "source", "9:16", "16:9", "1:1"
    video_fit_mode: Optional[str] = "contain"  # "contain" or "cover"
    duration_mode: Optional[str] = "preserve_video"  # MVP default

    voice_name: Optional[str] = ""
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.0
    bgm_type: Optional[str] = ""
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2

    subtitle_enabled: Optional[bool] = True
    subtitle_position: Optional[str] = config.ui.get("subtitle_position", "bottom")
    custom_position: float = config.ui.get("custom_position", 70.0)
    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Union[bool, str] = True
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5
    n_threads: Optional[int] = 2
```

Ghi chu:

- `source_video_path` chi duoc set sau khi upload/download ve local task dir.
- `source_video_url` chi la input; service se validate va download.
- `translated_script` cho phep user paste ban dich san trong tuong lai, MVP co the de rong va auto translate.
- `duration_mode = "preserve_video"` nghia la final video giu duration video goc; audio dich co the bi trim/fade neu dai hon. Neu audio ngan hon, video van giu duration goc voi audio het som.

### 4.2. `StudioTranslateState`

Them vao `webui/studio/state.py`:

```python
@dataclass
class StudioTranslateState:
    source_video_url: str = ""
    source_video_path: str = ""
    source_language: str = ""
    target_language: str = "vi-VN"
    translated_script: str = ""

    video_aspect: str = "source"
    video_fit_mode: str = "contain"
    duration_mode: str = "preserve_video"
    n_threads: int = 2

    voice_name: str = ""
    voice_volume: float = 1.0
    voice_rate: float = 1.0
    bgm_type: str = ""
    bgm_file: str = ""
    bgm_volume: float = 0.2

    subtitle_enabled: bool = True
    subtitle_position: str = "bottom"
    custom_position: float = 70.0
    font_name: str = "STHeitiMedium.ttc"
    text_fore_color: str = "#FFFFFF"
    text_background_color: bool | str = True
    font_size: int = 60
    stroke_color: str = "#000000"
    stroke_width: float = 1.5
```

Them helpers:

- `serialize_translate_state(state)`.
- `deserialize_translate_state(payload)`.
- `load_translate_state()`.
- `save_translate_state(state)`.
- `build_translate_params(state) -> TranslateVideoParams`.

Session keys:

- `studio_translate_state`
- `studio_active_translate_task_id`
- `studio_last_translate_task_id`
- `studio_translate_autorefresh`

## 5. Source video service

### 5.1. `app/services/source_video.py`

Public API:

```python
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}

def persist_uploaded_source_video(task_id: str, uploaded_file) -> str:
    ...

def download_source_video_url(task_id: str, url: str) -> str:
    ...

def validate_source_video(path: str) -> dict:
    ...

def extract_audio(video_path: str, output_audio_path: str) -> str:
    ...
```

### 5.2. Upload behavior

- Luu upload vao `storage/tasks/<task_id>/source.<ext>`.
- Chi chap nhan `.mp4`, `.mov`, `.mkv`, `.webm`.
- File name upload khong duoc dung truc tiep de tao path; chi lay extension.
- Sau khi ghi file, goi `validate_source_video()`.

### 5.3. URL behavior

Validation URL:

- Chi chap nhan `http://` va `https://`.
- Reject `file://`, path local, empty URL.
- Reject host private/localhost neu sau nay expose API ra ngoai. MVP WebUI local van nen implement de tranh SSRF khi app chay server.

Download strategy:

1. Neu URL path ket thuc bang video extension, thu direct download bang `requests.get(..., stream=True, timeout=(30, 240))`.
2. Neu direct download fail hoac URL khong phai file truc tiep, dung `yt_dlp.YoutubeDL`.
3. Output luon nam trong `storage/tasks/<task_id>/source-download.%(ext)s`.
4. Convert/remux ve `.mp4` neu can bang yt-dlp `merge_output_format = "mp4"`.
5. Validate file bang MoviePy.

### 5.4. Extract audio

Dung ffmpeg binary hien co:

```bash
ffmpeg -y -i source.mp4 -vn -ac 1 -ar 16000 source-audio.wav
```

Ly do:

- Whisper chay tot voi mono 16k WAV.
- MoviePy audio extract co the cham/ton RAM hon voi file lon.
- Da co `video.get_ffmpeg_binary()` de resolve ffmpeg.

Neu video khong co audio track:

- MVP fail ro rang: "Video goc khong co audio de dich".
- Future: cho user upload transcript hoac subtitle rieng.

## 6. LLM translation service

### 6.1. Them ham vao `app/services/llm.py`

Them:

```python
def translate_subtitle_segments(
    segments: list[dict],
    target_language: str,
    source_language: str = "",
) -> list[str]:
    ...
```

Input segments:

```python
[
    {"index": 1, "start": "00:00:00,000", "end": "00:00:02,000", "text": "Hello"},
    {"index": 2, "start": "00:00:02,000", "end": "00:00:04,000", "text": "Welcome"},
]
```

Prompt output bat buoc:

```json
["Xin chao", "Chao mung"]
```

Can parse robust:

- Goi `_generate_response(prompt)`.
- Neu response co `Error: ` thi return/raise error ro.
- `json.loads(response)`.
- Neu model chen text thua, recover bang regex `\[.*\]`.
- Bat buoc list length bang input length.
- Bat buoc moi item la string non-empty.

Khong dung output multiline vi `_normalize_text_response()` hien remove newline. JSON array van an toan.

### 6.2. Nguyen tac dich

Prompt nen yeu cau:

- Dich tu nhien sang `target_language`.
- Giu y nghia, khong them markdown, khong them chu thich.
- Giu so phan tu va thu tu.
- Moi phan tu nen ngan gon de hop voi subtitle/TTS.
- Khong dich brand names, URL, hashtag neu khong can.

## 7. Translate video pipeline

### 7.1. `app/services/translate_video.py`

Public API:

```python
def start(task_id: str, params: TranslateVideoParams) -> dict:
    ...
```

Flow:

```text
0. update task PROCESSING progress=5, workflow="translate_video"
1. resolve source video
   - use params.source_video_path if exists
   - else download params.source_video_url
2. validate source video
3. extract source audio
4. transcribe source audio to source.srt
5. parse source.srt to segments
6. translate segments with LLM
7. write translated-script.txt and translated-source-timing.srt
8. generate translated audio with TTS
9. generate subtitle.srt from TTS sub_maker; fallback to translated-source-timing.srt
10. render final translated video
11. update task COMPLETE progress=100 with videos/output metadata
```

Suggested progress:

- 5: queued/start.
- 10: source resolved.
- 20: audio extracted.
- 35: transcribed.
- 50: translated.
- 65: TTS audio generated.
- 75: subtitle generated.
- 95: video rendered.
- 100: complete.

Final result:

```python
{
    "workflow": "translate_video",
    "videos": [final_video_path],
    "source_video": source_video_path,
    "source_audio": source_audio_path,
    "source_subtitle": source_subtitle_path,
    "translated_subtitle": subtitle_path,
    "translated_script": translated_script,
    "audio_file": translated_audio_path,
    "audio_duration": audio_duration,
}
```

### 7.2. Subtitle generation strategy

Preferred:

- `voice.tts()` returns `sub_maker`.
- `voice.create_subtitle(sub_maker, translated_script, subtitle_file)` tao subtitle theo timing TTS.
- Render subtitle nay vi no sync voi voice dich.

Fallback:

- Neu `sub_maker is None`, dung `translated-source-timing.srt`.
- Neu user tat subtitle, output `subtitle_path = ""`.

### 7.3. Duration strategy MVP

MVP default `duration_mode = "preserve_video"`:

- Final video duration theo source video.
- Original audio bi mute/replace.
- Translated audio duoc gan vao video.
- Neu translated audio dai hon video:
  - Trim audio theo video duration va log warning.
  - Them fade out 0.5-1.0s de tranh cat dot ngot.
- Neu translated audio ngan hon video:
  - Cho audio ket thuc som; BGM neu co van loop theo video duration.

Future phase:

- `duration_mode = "match_audio"`: loop/freeze visual de match audio dich.
- Segment-level TTS: tao audio tung cau va stretch theo timing goc.

## 8. Video render helper

### 8.1. Van de voi `video.generate_video()`

`app/services/video.generate_video()` hien:

- Mo `video_path`.
- Mo `audio_path`.
- Overlay subtitle.
- Add BGM.
- `video_clip.with_audio(audio_clip)`.
- Xuat final.

Nhung no khong normalize/crop/pad video theo aspect; create pipeline da lam resize trong `combine_videos()`.

### 8.2. Them helper moi trong `app/services/video.py`

Them:

```python
def render_existing_video(
    source_video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_file: str,
    params: TranslateVideoParams,
) -> str:
    ...
```

Hoac neu muon giam duplicate:

- Tach phan overlay subtitle/audio/BGM tu `generate_video()` thanh private helper `_render_with_audio_and_subtitles(video_clip, audio_clip, subtitle_path, output_file, params)`.
- `generate_video()` va `render_existing_video()` cung goi helper nay.

MVP nen uu tien tach helper nho, vi copy nguyen `generate_video()` se de drift ve sau.

### 8.3. Aspect behavior

`params.video_aspect == "source"`:

- Giu kich thuoc video goc.

`params.video_aspect in {"9:16", "16:9", "1:1"}`:

- Dung `VideoAspect(...).to_resolution()`.
- `video_fit_mode == "contain"`: pad black background, khong crop.
- `video_fit_mode == "cover"`: crop center sau resize, lap day frame.

MVP UI default nen la `source` de tranh bat ngo cat mat video.

## 9. WebUI Translate page

### 9.1. Navigation

Sua `webui/studio/navigation.py`:

```python
from webui.studio.pages import assets, brand, create, projects, settings, translate

pages = [
    st.Page(create.render_page, title="Create", url_path="create"),
    st.Page(translate.render_page, title="Translate", url_path="translate"),
    ...
]
```

Sidebar label co the la `Translate` de plain text nhat quan voi yeu cau UI hien tai.

### 9.2. Layout page

`webui/studio/pages/translate.py`:

```text
Dich video
  description: Dich/lồng tiếng video co san bang AI, TTS va subtitle style cua Studio.

Main column:
  Video goc
    - Source method segmented: Upload / Link
    - Upload file uploader
    - URL text input
    - Caption ve public URL va ban quyen

  Dich noi dung
    - Source language select: Auto Detect + support_locales
    - Target language select: vi-VN default + support_locales
    - Optional translated script textarea readonly/editable after job in future

  Giong doc & am thanh
    - Reuse audio_settings.render_audio_settings(state)
    - Reuse audio_settings.render_audio_advanced_settings(state)

  Phu de & thuong hieu
    - Reuse subtitle_settings.render_subtitle_settings(state)
    - Reuse subtitle_settings.render_subtitle_advanced_settings(state)

  Nang cao
    - Video aspect: source / 9:16 / 16:9 / 1:1
    - Fit mode: contain / cover
    - Duration mode: preserve video
    - Threads

Right rail:
  Xuat ban dich
    - Validation summary
    - Summary: input type, target language, voice, subtitle, aspect
    - Preview frame
    - Button: Dich video
    - Progress/log/output
```

### 9.3. Reuse audio/subtitle components

Hien `audio_settings.py` va `subtitle_settings.py` type hint `StudioCreateState`, nhung runtime chi can object co cac field:

- `video_subject` / `video_script` chi dung trong voice preview fallback.
- `voice_name`, `voice_volume`, `voice_rate`, `bgm_type`, `bgm_file`, `bgm_volume`.
- `subtitle_enabled`, `subtitle_position`, `custom_position`, `font_name`, `text_fore_color`, `font_size`, `stroke_color`, `stroke_width`.
- `video_language` dung de chon font default.

Plan:

- Them `video_language` property vao `StudioTranslateState`, map ve `target_language` khi build state hoac component.
- Doi type hint sang protocol:

```python
class AudioSettingsState(Protocol):
    voice_name: str
    voice_volume: float
    voice_rate: float
    bgm_type: str
    bgm_file: str
    bgm_volume: float
    video_subject: str
    video_script: str
```

Hoac don gian hon:

- Bo type hint cu the `StudioCreateState` o component signatures.
- Dung duck typing de tranh refactor lon.

Khuyen nghi: dung Protocol de ro contract va test de hon.

### 9.4. Validation

Tao `validate_translate_request(params, app_config)`.

Rules:

- Phai co upload file hoac URL, khong duoc ca hai cung rong.
- Neu co ca upload va URL: upload uu tien, UI nen warning "Upload se duoc dung, link bi bo qua".
- Target language bat buoc.
- Voice name bat buoc neu khong co custom translated audio. MVP khong can custom translated audio.
- Neu LLM provider can key/model thi validation co the goi helper nhe de check config; it nhat check provider OpenAI key khi provider la `openai`.
- Neu subtitle enabled thi font file nen ton tai trong `resource/fonts`.
- URL phai la http(s).

## 10. Background job cho Translate

### 10.1. `webui/studio/translate_jobs.py`

Pattern giong `render_jobs.py`, nhung tach session key:

- `studio_active_translate_task_id`
- `studio_last_translate_task_id`
- `studio_translate_autorefresh`

Public API:

```python
def start_translate_job(
    state: StudioTranslateState,
    uploaded_video_file,
    background_runner=_start_background_thread,
) -> StudioRenderSnapshot:
    ...

def get_translate_snapshot(task_id: str, task_dir: str | None = None) -> StudioRenderSnapshot:
    ...

def get_active_translate_snapshot() -> StudioRenderSnapshot | None:
    ...

def clear_active_translate_task() -> None:
    ...
```

Log file:

- `storage/tasks/<task_id>/studio-translate.log`

Logger context:

- `studio_translate_task_id`

### 10.2. Co nen refactor common job registry?

Co 2 lua chon:

1. **Copy pattern tu `render_jobs.py` sang `translate_jobs.py`**  
   Nhanh, it rui ro cho Create, phu hop MVP.

2. **Tach common module `webui/studio/jobs.py`**  
   Dep hon, nhung co rui ro regression voi active render persistence vua lam.

Khuyen nghi: MVP dung lua chon 1. Sau khi Translate on dinh moi refactor common.

## 11. Projects page

`webui/studio/pages/projects.py` hien suy luan source tu:

```python
item.get("source") or item.get("params", {}).get("video_source", "")
```

Plan:

- Khi translate job update state, set:

```python
workflow="translate_video"
source="translate"
params=params.model_dump()
```

- Sua `source_label()`:

```python
if item.get("workflow") == "translate_video":
    return "Translate"
```

- Detail modal hien them:
  - Source video.
  - Source language.
  - Target language.
  - Translated script.
  - Source subtitle / translated subtitle path.

Khong can tach Projects page rieng cho translate trong MVP.

## 12. Thu tu trien khai

### Task 1: Them model/state/validation cho Translate

**Files:**

- Modify: `app/models/schema.py`
- Modify: `webui/studio/state.py`
- Create: `test/webui/test_studio_translate_state.py`

Steps:

- [ ] Viet test `StudioTranslateState` load/save/build params.
- [ ] Them `TranslateVideoParams`.
- [ ] Them `StudioTranslateState` va helpers.
- [ ] Them `validate_translate_request()`.
- [ ] Run:

```bash
uv run python -m unittest test.webui.test_studio_translate_state
uv run python -m compileall app/models/schema.py webui/studio/state.py
```

### Task 2: Source video upload/download service

**Files:**

- Create: `app/services/source_video.py`
- Create: `test/services/test_source_video.py`

Steps:

- [ ] Test reject empty/non-http/file/private URL.
- [ ] Test upload persist chi dung extension an toan.
- [ ] Test direct URL download path nam trong task dir.
- [ ] Test yt-dlp fallback duoc goi voi `outtmpl` trong task dir.
- [ ] Test `extract_audio()` goi ffmpeg command dung tham so.
- [ ] Implement service.
- [ ] Run:

```bash
uv run python -m unittest test.services.test_source_video
uv run python -m compileall app/services/source_video.py
```

### Task 3: LLM translate segments

**Files:**

- Modify: `app/services/llm.py`
- Create/modify: `test/services/test_llm.py`

Steps:

- [ ] Test parse JSON array dung length.
- [ ] Test recover JSON array embedded trong text.
- [ ] Test fail khi length khac input.
- [ ] Test `Error: ...` propagate ro.
- [ ] Implement `translate_subtitle_segments()`.
- [ ] Run:

```bash
uv run python -m unittest test.services.test_llm
uv run python -m compileall app/services/llm.py
```

### Task 4: Render existing video helper

**Files:**

- Modify: `app/services/video.py`
- Modify: `test/services/test_video.py`

Steps:

- [ ] Test `render_existing_video()` opens source video without original audio.
- [ ] Test aspect `source` giu size goc.
- [ ] Test aspect `9:16` contain tao frame portrait co padding.
- [ ] Test audio longer than video duoc trim/fade hoac log warning theo design.
- [ ] Implement helper bang cach tach phan overlay subtitle/audio/BGM tu `generate_video()`.
- [ ] Run:

```bash
uv run python -m unittest test.services.test_video
uv run python -m compileall app/services/video.py
```

### Task 5: Backend translate pipeline

**Files:**

- Create: `app/services/translate_video.py`
- Create: `test/services/test_translate_video.py`

Steps:

- [ ] Test pipeline call order bang mock:
  - resolve source video
  - extract audio
  - subtitle.create
  - llm.translate_subtitle_segments
  - voice.tts
  - voice.create_subtitle
  - video.render_existing_video
  - state COMPLETE voi output metadata
- [ ] Test fail khi source video khong co audio.
- [ ] Test fallback subtitle timing khi `sub_maker is None`.
- [ ] Test output files `translated-script.txt`, `translated-source-timing.srt`.
- [ ] Implement `start(task_id, params)`.
- [ ] Run:

```bash
uv run python -m unittest test.services.test_translate_video
uv run python -m compileall app/services/translate_video.py
```

### Task 6: Background translate jobs

**Files:**

- Create: `webui/studio/translate_jobs.py`
- Create: `test/webui/test_translate_jobs.py`

Steps:

- [ ] Test start job set `studio_active_translate_task_id`.
- [ ] Test snapshot doc state/log/output tu task dir.
- [ ] Test log ghi vao `studio-translate.log`.
- [ ] Test clear active task khong anh huong create render keys.
- [ ] Implement module theo pattern `render_jobs.py`.
- [ ] Run:

```bash
uv run python -m unittest test.webui.test_translate_jobs
uv run python -m compileall webui/studio/translate_jobs.py
```

### Task 7: Translate page UI

**Files:**

- Create: `webui/studio/pages/translate.py`
- Modify: `webui/studio/navigation.py`
- Modify: `webui/studio/components/audio_settings.py`
- Modify: `webui/studio/components/subtitle_settings.py`
- Modify: `webui/studio/theme.py`
- Create: `test/webui/test_studio_translate_page.py`

Steps:

- [ ] Test navigation co page `Translate`.
- [ ] Test page render cac section:
  - `Video gốc`
  - `Dịch nội dung`
  - `Giọng đọc & âm thanh`
  - `Phụ đề & thương hiệu`
  - `Nâng cao`
  - `Xuất bản dịch`
- [ ] Test page khong import/create state nham `StudioCreateState` cho translate-only fields.
- [ ] Implement page voi 2 columns + sticky rail.
- [ ] Reuse audio/subtitle components sau khi giam coupling.
- [ ] Run:

```bash
uv run python -m unittest test.webui.test_studio_translate_page
uv run python -m unittest test.webui.test_studio_app_smoke
```

### Task 8: Projects page support translate tasks

**Files:**

- Modify: `webui/studio/pages/projects.py`
- Modify: `test/webui/test_studio_projects.py`

Steps:

- [ ] Test `source_label()` tra `Translate` khi `workflow == "translate_video"`.
- [ ] Test detail modal hien target language va source video.
- [ ] Implement display logic.
- [ ] Run:

```bash
uv run python -m unittest test.webui.test_studio_projects
```

### Task 9: End-to-end verification

Run full safe suite:

```bash
uv run python -m unittest discover -s test/webui
uv run python -m unittest test.services.test_source_video test.services.test_translate_video test.services.test_llm test.services.test_video
uv run python -m compileall app/services webui/studio
git diff --check
```

Manual smoke:

- Start Streamlit:

```bash
uv run streamlit run webui/Main.py --server.port 8501
```

- Open `http://127.0.0.1:8501/`.
- Confirm sidebar co `Translate`.
- Open Translate page.
- Upload short mp4 co audio.
- Chon target `vi-VN`.
- Chon voice Vietnamese.
- Click `Dịch video`.
- Chuyen sang Projects roi quay lai Translate.
- Confirm progress/log khong mat.
- Confirm output final mp4 co:
  - Visual tu video goc.
  - Audio la voice dich.
  - Phu de theo style da chon.

## 13. Rủi ro và cách giảm

### 13.1. Whisper model nặng hoặc chưa tải

Rui ro:

- `faster-whisper` co san dependency, nhung model co the chua nam trong `models/`.
- Lan dau co the tai model tu internet hoac fail do network.

Giam rui ro:

- UI validation/log can noi ro "Whisper model not available".
- Docs can huong dan config `[whisper]`.
- MVP khong auto download ngoai y muon; de `subtitle.create()` xu ly nhu hien tai.

### 13.2. TTS duration khong khop video

Rui ro:

- Ban dich dai hon audio goc, final voice dai hon video.

Giam rui ro MVP:

- Default preserve video duration.
- Log warning khi audio dai hon video.
- Them future mode `match_audio`.

### 13.3. URL downloader va SSRF

Rui ro:

- Neu app expose ra LAN/public, URL input co the bi dung de request local network.

Giam rui ro:

- Reject non-http(s).
- Resolve host va reject private/loopback/link-local IP.
- Tat redirect sang private IP.
- Limit output path vao task dir.

### 13.4. Component audio/subtitle coupling voi Create

Rui ro:

- Reuse component truc tiep co the vo vi component dang type hint `StudioCreateState`.

Giam rui ro:

- Doi sang Protocol hoac remove concrete type hint.
- Them tests de Create page van render.

### 13.5. Redis state convert metadata

Rui ro:

- `RedisState` luu kwargs thanh string va parse bang `ast.literal_eval`; dict/list co the parse duoc, nhung object phuc tap khong.

Giam rui ro:

- Chi luu primitives/list/dict serializable.
- Params luu bang `params.model_dump()`.

## 14. Definition of Done

Tinh nang duoc xem la xong khi:

- Co page `Translate` rieng trong Studio navigation.
- User upload video hoac dan URL public de tai video.
- Task translate chay background va khong mat progress/log khi doi page.
- Pipeline tao duoc final mp4 tu video goc, audio dich, subtitle style.
- Reuse duoc flow `Giong doc & am thanh` va `Phu de & thuong hieu`.
- Projects page nhan dien va xem duoc task translate.
- Tests pass:

```bash
uv run python -m unittest discover -s test/webui
uv run python -m unittest test.services.test_source_video test.services.test_translate_video test.services.test_llm test.services.test_video
uv run python -m compileall app/services webui/studio
git diff --check
```

## 15. Khuyen nghi trien khai

Nen implement theo thu tu:

1. Backend source video + translate pipeline truoc.
2. Job persistence cho Translate.
3. UI page Translate.
4. Projects support.
5. Manual smoke voi video ngan 5-10s.

Khong nen bat dau bang UI truoc, vi rui ro lon nhat nam o pipeline: URL download, audio extract, Whisper transcript, LLM translate, TTS duration va render existing video.
