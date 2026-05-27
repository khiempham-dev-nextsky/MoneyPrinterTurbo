# Create Video Single Page UX And Render Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thay Create Video tu layout 6 tabs sang mot trang duy nhat gon, ro, thao tac nhanh; dong thoi giu duoc video task dang tao, progress, log va output khi user chuyen sang page khac roi quay lai.

**Architecture:** Create page se thanh single-page studio console gom main editor column va render rail. Render khong con chay dong bo trong UI container cua page; thay vao do tao background render job co task id on dinh, log file rieng, in-memory registry va state adapter de page nao cung co the doc lai trang thai.

**Tech Stack:** Streamlit 1.45, Python 3.11, Loguru, current `VideoParams`/`app.services.task.start` pipeline, `app.services.state`, unittest, Streamlit AppTest.

---

## 1. Pham vi thay doi

Plan nay thay the rieng phan Create Video hien tai cua `docs/ke-hoach-uiux-video-studio-vi.md`, dac biet la cac muc:

- Create workflow dang chia 6 step bang tabs.
- Render status/log dang gan vao page hien tai.
- Projects page chi doc task da co output, chua giup user theo doi active render khi quay lai Create.

Khong doi backend generate video core trong phase nay:

- Khong doi `VideoParams` schema.
- Khong refactor `app/services/task.py` pipeline, tru khi can hook nho de log/progress tot hon.
- Khong them database.
- Khong bat buoc API server phai chay, vi WebUI local van phai tao video duoc nhu hien tai.

## 2. Van de hien tai

### 2.1. UX Create Video bi phan manh

Hien tai `webui/studio/pages/create.py` dung:

```python
tabs = st.tabs(
    [
        "1. Brief",
        "2. Script & Keywords",
        "3. Source & Materials",
        "4. Voice & Audio",
        "5. Subtitles & Brand",
        "6. Review & Render",
    ]
)
```

Bat tien chinh:

- Muon sua subject, script, source, voice, subtitle phai click qua lai nhieu tab.
- Review/render nam rieng tab cuoi nen user khong thay readiness trong luc sua.
- Field co lien quan nhau bi tach xa nhau, vi du script/keywords va source search.
- Tab trong Streamlit khong phai wizard that, nen khong giup luu flow tot hon.

### 2.2. Task dang tao bi mat khi doi page

Hien tai `webui/studio/components/actions.py` chay render dong bo:

```python
log_records = []
with st.status("Rendering video", expanded=True) as status:
    log_container = st.empty()
    logger.add(log_received)
    result = tm.start(task_id=task_id, params=params)
```

Root cause:

- `log_records` la bien local, mat khi Streamlit rerun hoac page khac duoc render.
- `st.status` va `log_container` chi ton tai trong lan render cua Create page.
- `task_id` khong duoc luu vao `st.session_state`, nen khi quay lai Create khong biet task nao dang chay.
- Logger sink duoc add trong page render, khong gan voi lifecycle cua task.
- Render chay trong UI script thread; user navigation lam UI context moi khong con noi de hien lai log cu.

## 3. UX target

### 3.1. Single-page studio console

Create Video moi se gom 2 cot:

```text
Create Video
+-- Main editor column, width ~70%
|   +-- Brief & Script
|   |   +-- Video Subject
|   |   +-- Script Language
|   |   +-- Generate Script / Generate Keywords
|   |   +-- Video Script
|   |   +-- Video Keywords
|   +-- Source & Materials
|   |   +-- Video Source segmented control
|   |   +-- Source-specific essentials
|   |   +-- Advanced video options expander
|   +-- Voice & Audio
|   |   +-- TTS Server
|   |   +-- Voice
|   |   +-- Play Voice
|   |   +-- Advanced audio/BGM expander
|   +-- Subtitles & Brand
|       +-- Subtitle preset
|       +-- Enable subtitles
|       +-- Font/color/position essentials
|       +-- Subtitle fine tuning expander
+-- Render rail, width ~30%
    +-- Readiness/validation
    +-- Compact config summary
    +-- Generate Video button
    +-- Active task status
    +-- Render log
    +-- Output preview
```

### 3.2. Giao dien gon nhung du thong tin

Mac dinh hien:

- Subject, language, script, keywords.
- Source select va field can thiet cua source dang chon.
- TTS server, voice, voice preview.
- Subtitle preset, font, color, position.
- Render button va validation summary.

An trong expander:

- `Advanced video options`: aspect, concat mode, transition, clip duration, video count, threads.
- `TikTok advanced`: provider, max search results, max downloads, min duration, cookie file.
- `Audio advanced`: volume, rate, custom audio, BGM type/file/volume, provider API key fields.
- `Subtitle fine tuning`: font size, stroke color, stroke width, custom position.

### 3.3. Render rail luon hien

Render rail la diem khac chinh so voi layout tabs:

- User sua script/source/voice ben trai va thay validation ben phai ngay lap tuc.
- Nut `Generate Video` khong nam o tab rieng.
- Khi co active task, rail hien task id, progress, state, log gan nhat va output neu xong.
- Khi user quay lai Create, rail tu khoi phuc active task/log.

## 4. Render persistence design

### 4.1. Model trang thai moi

Them vao `webui/studio/state.py`:

```python
@dataclass
class StudioRenderSnapshot:
    task_id: str
    state: int | None = None
    progress: int = 0
    status_label: str = "Idle"
    log_lines: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    task_dir: str = ""
    error: str = ""
```

Them session keys:

```text
studio_active_render_task_id
studio_last_render_task_id
studio_render_autorefresh
studio_create_state
```

`studio_create_state` nen luu day du cac field quan trong, khong chi subject/script/terms:

- video source/options
- voice/audio settings
- subtitle settings
- persisted local materials
- persisted custom audio path

### 4.2. Render job module

Tao file moi `webui/studio/render_jobs.py`.

Trach nhiem:

- Tao task id.
- Persist uploaded materials/audio truoc khi enqueue.
- Validate params.
- Start background thread.
- Luu active task id vao session.
- Ghi log vao `storage/tasks/<task_id>/studio-render.log`.
- Luu log gan nhat vao in-memory registry.
- Doc snapshot tu `app.services.state.sm.state` va task folder.

Public API de xuat:

- `start_render_job(state, uploaded_files, uploaded_audio_file) -> StudioRenderSnapshot`: validate params, persist uploads, create task id, save session keys, start background thread, return initial snapshot.
- `get_render_snapshot(task_id: str) -> StudioRenderSnapshot`: read `sm.state`, registry, `studio-render.log`, task folder outputs, and return one normalized snapshot.
- `get_active_render_snapshot() -> StudioRenderSnapshot | None`: read `studio_active_render_task_id` from session and delegate to `get_render_snapshot`.
- `clear_active_render_task() -> None`: remove `studio_active_render_task_id` but keep `studio_last_render_task_id` for history.

### 4.3. Background execution

Khong goi `tm.start()` truc tiep trong page render nua.

Flow moi:

```text
User click Generate Video
-> validate params
-> task_id = uuid4()
-> sm.state.update_task(task_id, PROCESSING, progress=0)
-> st.session_state["studio_active_render_task_id"] = task_id
-> start background thread
-> thread calls tm.start(task_id, params)
-> thread writes task status via sm.state, log file, registry
-> Create page render rail polls snapshot
```

Thread khong duoc goi bat ky `st.*` nao.

Loguru context:

```python
with logger.contextualize(studio_task_id=task_id):
    sink_id = logger.add(
        sink,
        filter=lambda record: record["extra"].get("studio_task_id") == task_id,
    )
    try:
        result = tm.start(task_id=task_id, params=params)
    finally:
        logger.remove(sink_id)
```

Ly do:

- Log cua task tiep tuc ghi du user dang o page nao.
- Create page chi doc log, khong so huu log lifecycle.
- Neu user quay lai, log da co trong registry/file.

### 4.4. Recovery khi app rerun hoac restart

Trong cung Streamlit process:

- In-memory registry giu recent log lines va result/error.
- `sm.state` giu progress/state.
- Task folder giu file output.

Sau app restart:

- Background task dang chay se mat neu process bi kill, day la gioi han chap nhan trong local WebUI phase nay.
- Nhung task da tao co folder/log/output thi Create co the hien lai "Recovered task".
- Neu `studio_active_render_task_id` khong con trong session, Projects van doc output tu `storage/tasks`.

### 4.5. Auto refresh

Streamlit 1.45 co `st.fragment`, da verify trong local env.

Plan:

- Dung `@st.fragment(run_every="2s")` cho render rail khi active task state la processing.
- Fallback neu fragment khong hoat dong: hien nut `Refresh status`.
- Khong dung loop blocking trong UI thread.

## 5. File-level implementation plan

### Task 1: Create page layout khong tabs

**Files:**

- Modify: `webui/studio/pages/create.py`
- Modify: `webui/studio/theme.py`
- Test: `test/webui/test_studio_app_smoke.py`

Steps:

- [ ] Them regression test assert Create page khong con old tab labels `"1. Brief"`, `"2. Script & Keywords"`.
- [ ] Refactor `render_page()` thanh:
  - `main_col, render_col = st.columns([7, 3], gap="large")`
  - main col render all sections top-to-bottom
  - render col render review/status panel
- [ ] Doi title description thanh "Create, tune, render, and monitor one video from a single page."
- [ ] Them section helpers:
  - `_render_brief_and_script_section`
  - `_render_source_section`
  - `_render_audio_section`
  - `_render_subtitle_section`
  - `_render_render_rail`
- [ ] Chay `uv run python -m unittest test.webui.test_studio_app_smoke`.

### Task 2: Progressive disclosure cho sections

**Files:**

- Modify: `webui/studio/components/source_settings.py`
- Modify: `webui/studio/components/audio_settings.py`
- Modify: `webui/studio/components/subtitle_settings.py`
- Test: `test/webui/test_studio_app_smoke.py`

Steps:

- [ ] Split essential fields va advanced fields trong source settings:
  - essential: source select, local upload, TikTok provider status.
  - advanced: aspect, concat, transition, clip duration, count, threads, TikTok limits/cookie.
- [ ] Split audio:
  - essential: server, voice, preview.
  - advanced: provider keys, voice volume/rate, custom audio, BGM.
- [ ] Split subtitle:
  - essential: preset, enable, font, color, position.
  - advanced: custom position, font size, stroke color/width.
- [ ] Test labels essential xuat hien tren Create page.

### Task 3: Persist complete Create state

**Files:**

- Modify: `webui/studio/state.py`
- Test: `test/webui/test_studio_state.py`

Steps:

- [ ] Them serialize/deserialize cho `StudioCreateState`.
- [ ] `save_create_state` ghi vao `st.session_state["studio_create_state"]`.
- [ ] `load_create_state` uu tien `studio_create_state`, fallback config/session legacy keys.
- [ ] Persist cac field:
  - subject/script/terms/language
  - source/options/materials
  - voice/audio/bgm/custom audio path
  - subtitle/font/colors/stroke
- [ ] Test round-trip state giu du cac field.

### Task 4: Durable render jobs

**Files:**

- Create: `webui/studio/render_jobs.py`
- Modify: `webui/studio/components/actions.py`
- Modify: `webui/studio/state.py`
- Test: `test/webui/test_render_jobs.py`

Steps:

- [ ] Viet failing test `start_render_job` luu active task id va goi background executor.
- [ ] Viet failing test log append vao `studio-render.log`.
- [ ] Viet failing test `get_render_snapshot` doc state tu `sm.state` va output tu task folder.
- [ ] Implement `StudioRenderSnapshot`.
- [ ] Implement in-memory registry co lock:
  - `task_id -> log_lines`
  - `task_id -> result`
  - `task_id -> error`
- [ ] Implement background thread runner khong goi Streamlit API.
- [ ] Move upload persistence ra khoi UI synchronous render.
- [ ] Doi `actions.render_video_generation` thanh wrapper compatibility hoac remove neu khong con dung.

### Task 5: Active render rail

**Files:**

- Modify: `webui/studio/components/status.py`
- Modify: `webui/studio/pages/create.py`
- Test: `test/webui/test_studio_app_smoke.py`

Steps:

- [ ] Them `render_active_render_panel(snapshot)`.
- [ ] Hien state mapping:
  - processing: "Rendering"
  - complete: "Completed"
  - failed: "Failed"
  - missing: "Task not found"
- [ ] Hien progress bar tu `snapshot.progress`.
- [ ] Hien log trong expander `Render log`, mac dinh expanded khi processing.
- [ ] Hien output video preview khi complete.
- [ ] Them button:
  - `Open Project Folder`
  - `Clear active task`
  - `Refresh status`
- [ ] Dung `st.fragment(run_every="2s")` cho active processing task.

### Task 6: Projects integration

**Files:**

- Modify: `webui/studio/pages/projects.py`
- Modify: `webui/studio/components/status.py`
- Test: `test/webui/test_studio_projects.py`

Steps:

- [ ] `list_task_outputs` doc them `studio-render.log` neu co.
- [ ] Projects hien task dang co log nhung chua co `final-*.mp4`.
- [ ] Projects table them status/progress neu task con trong `sm.state`.
- [ ] "Reuse in Create" giu nguyen, nhung them "Continue in Create" de set active task id va huong dan user quay lai Create.

### Task 7: Runtime verification va cleanup

**Files:**

- Modify only files changed by Task 1-6 when a verification command exposes a defect.
- Do not edit backend generation files for cosmetic cleanup in this task.

Commands:

```bash
uv run python -m unittest discover -s test/webui
uv run python -m unittest test.services.test_tiktok test.services.test_task test.controllers.test_video
uv run python -m compileall app webui main.py
uv run streamlit run ./webui/Main.py --server.headless true --server.port 8502
curl -sSf http://127.0.0.1:8502/_stcore/health
```

Manual QA:

- Open Create page.
- Confirm no tab UI.
- Fill subject/script/source/voice/subtitle on same page.
- Start render.
- Switch to Projects.
- Return to Create.
- Confirm active task id, progress/log still visible.
- Wait render done.
- Confirm output video preview appears.
- Restart WebUI.
- Confirm completed task output/log still visible in Projects.

## 6. Acceptance criteria

Plan/implementation duoc xem la xong khi co bang chung sau:

1. Create Video khong con dung 6 tabs.
   - Evidence: UI smoke test va code `create.py` khong con `st.tabs`.

2. Tat ca input chinh nam tren cung mot page.
   - Evidence: AppTest thay labels subject/script/keywords/source/voice/subtitle/render tren Create page default.

3. Advanced config duoc gom gon.
   - Evidence: source/audio/subtitle advanced fields nam trong expanders.

4. User dang render video co the chuyen page va quay lai Create van thay task.
   - Evidence: test active task id persistence va manual QA.

5. Render log khong mat khi quay lai Create.
   - Evidence: `studio-render.log` ton tai trong task dir va active render panel doc lai duoc.

6. Task complete hien output preview/path.
   - Evidence: `get_render_snapshot` test doc `final-*.mp4`; manual QA preview.

7. Existing backend generate behavior khong bi doi.
   - Evidence: targeted backend tests pass.

## 7. Rui ro va cach giam rui ro

1. Background thread trong Streamlit
   - Giam rui ro bang cach thread khong goi `st.*`, chi goi backend service va ghi state/log.

2. Logger sink leak
   - Moi job add sink trong thread va remove trong `finally`.
   - Test registry/log append khong can Streamlit context.

3. User upload file bi mat khi chuyen page
   - Persist uploaded local material/audio ngay khi file uploader co file.
   - Store persisted path trong `StudioCreateState`.

4. Process restart lam mat in-memory processing task
   - Phase nay chap nhan khong resume task dang chay sau process kill.
   - Van recover completed task/log/output tu task folder.

5. Auto-refresh gay rerun qua nhieu
   - Chi auto-refresh render rail khi task processing.
   - Co fallback manual refresh.

## 8. Recommended commit sequence

1. `test: cover create single-page layout`
2. `feat: refactor create page into single-page studio console`
3. `feat: persist full create state`
4. `feat: add durable studio render jobs`
5. `feat: show active render status and logs`
6. `feat: surface in-progress tasks in projects`
7. `test: add create video render persistence coverage`

## 9. Implementation order recommendation

Nen lam theo thu tu:

1. Layout single-page truoc, vi day la UX user thay ngay.
2. Persist complete create state, vi no la nen cho render persistence.
3. Durable render jobs, vi day la thay doi behavior rui ro nhat.
4. Active render rail va Projects integration.
5. Manual QA voi video render ngan.

Khong nen lam render background truoc layout, vi se kho review UX va de bi tron bug UI voi bug task lifecycle.
