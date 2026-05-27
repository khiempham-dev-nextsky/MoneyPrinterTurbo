# Video Studio UI/UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Doi WebUI MoneyPrinterTurbo tu mot form tao video dai thanh mot studio tao video chuyen nghiep, de dung, de mo rong cho asset library, project management, brand kit, publish va cac tinh nang AI sau nay.

**Architecture:** Giu backend tao video hien tai, refactor Streamlit WebUI thanh studio shell nhieu page: Create, Projects, Assets, Brand, Settings. Tach `webui/Main.py` thanh entrypoint nho, page modules, reusable components, theme/style tokens va session-state adapter de giam rui ro regression.

**Tech Stack:** Streamlit 1.45, Python 3.11, FastAPI backend hien tai, `VideoParams`/`tm.start()` pipeline hien tai, unittest/pytest-compatible tests, Streamlit AppTest cho smoke test UI.

**Update 2026-05-27:** Phan Create Video khong tiep tuc theo layout 6 tabs. Plan thay the cho Create single-page UX va render/log persistence nam tai `docs/ke-hoach-create-video-single-page-render-persistence-vi.md`.

---

## 1. Tai sao can doi UI/UX

Hien trang WebUI tap trung tat ca vao `webui/Main.py`:

- File `webui/Main.py` dai khoang 1.221 dong.
- UI dung 3 cot co dinh: script, video/audio, subtitle/API key.
- `Basic Settings`, LLM settings, Pexels/Pixabay keys, video source, TikTok config, TTS, subtitle style va generate action nam gan nhau trong mot man hinh.
- Ket qua render chi hien sau khi bam `Generate Video`; task/project library chua co trai nghiem ro.
- Advanced config hien ngay trong luong tao video, lam nguoi moi bi qua tai.
- Cac source moi nhu TikTok da lam UI phinh ra, va sau nay neu them template, brand kit, publish, scheduling, asset management thi mot file/mot form se kho scale.

Muc tieu khong chi la lam dep. Muc tieu la doi mental model thanh:

```text
MoneyPrinterTurbo = Video Studio

Create video -> manage materials -> style brand/subtitle -> render -> review output -> publish/reuse
```

## 2. Nguon tham khao da dung

1. Streamlit multipage apps:
   - URL: https://docs.streamlit.io/develop/concepts/multipage-apps/overview
   - Diem ap dung: dung `st.Page` va `st.navigation` de tach app thanh nhieu page, entrypoint lam frame chung cho navigation va shared layout.

2. Streamlit forms:
   - URL: https://docs.streamlit.io/develop/api-reference/execution-flow/st.form
   - Diem ap dung: gom cac input lien quan vao form, chi submit khi user bam action de tranh rerun lung tung trong flow tao video.

3. Streamlit status container:
   - URL: https://docs.streamlit.io/develop/api-reference/status/st.status
   - Diem ap dung: hien tien trinh generate/search/download/render bang mot status panel co the collapse/expand, khong nest status containers.

4. Streamlit native app testing:
   - URL: https://docs.streamlit.io/develop/concepts/app-testing
   - Diem ap dung: them smoke tests bang `streamlit.testing.v1.AppTest` de verify navigation, labels, field defaults va cac route UI chinh.

5. IBM progressive disclosure:
   - URL: https://www.ibm.com/docs/en/technical-content?topic=practices-progressive-disclosure
   - Diem ap dung: chi hien option can thiet cho step hien tai; advanced config nam trong advanced drawer/expander; huong dan theo task, khong bien UI thanh noi di tim setting.

6. Microsoft wizard UX guidelines:
   - URL: https://learn.microsoft.com/en-us/windows/win32/uxguide/win-wizards
   - Diem ap dung: wizard khong co so step co dinh; moi page/step phai gom mot sub-task ro; nen ngan, it branch, co navigation guide neu nhieu step.

7. Material/Windows navigation patterns:
   - URLs:
     - https://m3.material.io/components/navigation-rail/overview
     - https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/navigationview
   - Diem ap dung: studio nen co navigation trai/top on dinh, page title/header ro, footer/settings rieng de sau nay them tinh nang khong lam roi flow tao video.

8. Tham khao san pham video editor/studio hien dai:
   - Adobe Express Video Maker: https://www.adobe.com/express/create/video
   - Canva Video Suite: https://www.canva.com/newsroom/news/introducing-canva-video-suite/
   - CapCut Desktop AI Video Editor: https://www.capcut.com/tools/desktop-ai-power/
   - Diem ap dung: template/source/media/audio/brand/render/publish la cac khu vuc rieng; flow nen giup nguoi moi tao nhanh nhung van co du quyen kiem soat cho nguoi dung nang cao.

## 3. Huong tiep can tong quat

### 3.1. Nguyen tac san pham

1. Studio-first, khong landing-page:
   - Man hinh dau tien la workspace tao video, khong phai trang gioi thieu.
   - Brand/product signal la `MoneyPrinterTurbo Studio`, nhung noi dung chinh la form lam viec.

2. Guided creation:
   - Nguoi moi di theo tung buoc: brief -> script -> source -> voice/audio -> subtitles/brand -> review/render.
   - Nguoi dung nang cao co the nhay giua step hoac dung quick presets.

3. Progressive disclosure:
   - Mac dinh chi hien input quan trong.
   - Advanced settings chi hien khi can: proxy, timeout TikTok, thread count, custom position, provider-specific keys.

4. Preview-driven:
   - Can co vung review ben phai hoac page review: script, keywords, source, voice, subtitle style, output.
   - Task dang chay can co status ro: generating script, generating terms, synthesizing audio, discovering materials, combining, finalizing.

5. Scale feature:
   - Them feature moi phai them page/section/module, khong chen tiep vao `Main.py`.
   - Moi source video co config rieng va validation rieng.
   - Brand/style preset la resource rieng, khong gan cung vao mot form render.

### 3.2. Khong lam trong phase dau

Khong nen doi backend tao video trong phase UI/UX dau tien, tru khi can adapter nho:

- Khong doi `VideoParams` schema trong phase 1.
- Khong doi `app/services/task.py` pipeline generate.
- Khong migrate sang React/Next.js ngay.
- Khong them database/project persistence phuc tap ngay neu storage task hien tai du dung.

Ly do: muc tieu phase dau la doi trai nghiem va cau truc UI, giam blast radius.

## 4. Information Architecture de xuat

### 4.1. Studio navigation

Navigation chinh:

```text
Create
Projects
Assets
Brand
Settings
```

Y nghia tung page:

- `Create`: tao video moi bang guided workflow.
- `Projects`: xem task/output da tao, mo folder, preview final video, reuse script/settings.
- `Assets`: quan ly local uploads, cached TikTok videos, Pexels/Pixabay/TikTok source diagnostics.
- `Brand`: subtitle presets, font, color, stroke, position, aspect presets, future template presets.
- `Settings`: LLM providers, TTS providers, video source API keys, runtime/path/advanced config.

### 4.2. Create workflow

Create page chia thanh 6 step:

1. Brief
   - `Video Subject`
   - `Script Language`
   - preset muc tieu: Shorts/Reels/TikTok, YouTube, Ads, Education
   - primary action: `Generate Script`

2. Script & Keywords
   - `Video Script`
   - `Video Keywords`
   - action: `Generate Keywords`
   - inline validation: subject/script khong duoc cung trong

3. Source & Materials
   - source segmented control: Pexels, Pixabay, Local, TikTok
   - Pexels/Pixabay: API health, keyword preview, aspect
   - Local: uploader + material list
   - TikTok: search provider, max results/downloads, cookie file status
   - future: uploaded library, favorite assets, negative keywords

4. Voice & Audio
   - TTS provider
   - voice select/search
   - speech rate/volume
   - custom audio upload
   - BGM mode and volume
   - action: `Preview Voice`

5. Subtitles & Brand
   - subtitle enabled
   - font select with readable labels
   - color, stroke, font size, position
   - brand preset select
   - preview block for sample subtitle style

6. Review & Render
   - compact summary of all decisions
   - warnings for missing API keys/source issues
   - output count, aspect, concat mode, transition
   - primary action: `Generate Video`
   - status/timeline of task

### 4.3. Studio shell layout

Desktop layout:

```text
+----------------------------------------------------------------+
| Top bar: MoneyPrinterTurbo Studio | active project | language   |
+------------+---------------------------------------+-----------+
| Navigation | Main workspace                        | Inspector |
| Create     | Step content                          | Summary   |
| Projects   | Form / lists / preview                | Warnings  |
| Assets     |                                       | Actions   |
| Brand      |                                       |           |
| Settings   |                                       |           |
+------------+---------------------------------------+-----------+
| Optional bottom task queue / recent render status               |
+----------------------------------------------------------------+
```

Mobile/narrow layout:

- Navigation dung sidebar/top tabs cua Streamlit.
- Inspector chuyen xuong duoi step content.
- Khong dung 3 cot co dinh tren man hinh nho.

## 5. Visual direction

### 5.1. Phong cach

Phong cach nen la "professional creator studio":

- Nen trung tinh, khong qua toi, khong qua mau me.
- Su dung mau nhan cho primary action/render status, khong phu toan app bang mot hue.
- Cards chi dung cho item lap lai: project cards, asset cards, preset cards, output cards.
- Khong long cards trong cards.
- Section chinh la full-width band hoac unframed layout.
- Border radius toi da 8px cho controls/cards de giu cam giac chuyen nghiep.
- Typography ro, dense vua phai, uu tien scan va thao tac lap lai.

### 5.2. Mau sac goi y

Khong bien UI thanh mot palette tim/xanh/den duy nhat. Goi y tokens:

```python
STUDIO_COLORS = {
    "page_bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "surface_alt": "#F1F3F5",
    "border": "#D8DEE6",
    "text": "#111827",
    "muted": "#5B6472",
    "primary": "#2563EB",
    "success": "#0F766E",
    "warning": "#B45309",
    "danger": "#B91C1C",
    "accent": "#7C3AED",
}
```

Ghi chu: `accent` chi dung cho highlight nho, khong dung lam nen chinh.

### 5.3. Component pattern

- Icons: Streamlit native icons/emoji co the dung tam thoi trong labels; neu sau nay doi frontend thi dung lucide icons.
- Buttons:
  - Primary: `Generate Video`, `Render`, `Use Preset`.
  - Secondary: `Generate Script`, `Generate Keywords`, `Preview Voice`.
  - Destructive: delete key, remove asset.
- Controls:
  - Source/aspect/preset: segmented control hoac radio horizontal.
  - Binary: toggle/checkbox.
  - Numeric: number input/slider.
  - Provider selection: selectbox + contextual fields.
  - Advanced: expander co label ro.
- Status:
  - Dung `st.status` cho long-running stage.
  - Dung inline `st.error`, `st.warning`, `st.info` sat field lien quan.

## 6. File structure de xuat

Tach WebUI thanh cac module sau:

```text
webui/
  Main.py
  studio/
    __init__.py
    bootstrap.py
    i18n.py
    theme.py
    state.py
    navigation.py
    validators.py
    components/
      __init__.py
      layout.py
      actions.py
      cards.py
      status.py
      fields.py
      source_settings.py
      audio_settings.py
      subtitle_settings.py
      llm_settings.py
    pages/
      __init__.py
      create.py
      projects.py
      assets.py
      brand.py
      settings.py
```

Responsibility:

- `Main.py`: entrypoint, `st.set_page_config`, init root path, load config, call `render_studio_app()`.
- `bootstrap.py`: init logger, path constants, locales, default session keys.
- `i18n.py`: `tr()`, locale choices, language selector helper.
- `theme.py`: CSS tokens, layout CSS, component class helpers.
- `state.py`: studio session model, convert UI state <-> `VideoParams`.
- `navigation.py`: Streamlit multipage nav setup.
- `validators.py`: pre-render validation, provider validation, source validation.
- `components/layout.py`: top bar, sidebar/rail, inspector, page header.
- `components/actions.py`: generate script/keywords/video button handlers.
- `components/status.py`: task status/result renderer.
- `components/source_settings.py`: Pexels/Pixabay/Local/TikTok UI.
- `components/audio_settings.py`: TTS/BGM/custom audio UI.
- `components/subtitle_settings.py`: font/subtitle UI.
- `components/llm_settings.py`: LLM provider form.
- `pages/create.py`: guided workflow.
- `pages/projects.py`: task/output browser from `storage/tasks`.
- `pages/assets.py`: local/cache material browser and diagnostics.
- `pages/brand.py`: subtitle/brand presets.
- `pages/settings.py`: API/provider/runtime settings.

## 7. Data flow giu tuong thich

### 7.1. Create state

Can co mot state object ro, vi hien tai gia tri nam rai trong `st.session_state`, `config` va `params`.

De xuat:

```python
@dataclass
class StudioCreateState:
    video_subject: str = ""
    video_script: str = ""
    video_terms: str = ""
    video_language: str = ""
    active_step: str = "brief"
    local_video_materials: list[dict] = field(default_factory=list)
    uploaded_audio_path: str | None = None
```

Adapter:

```python
def build_video_params(state: StudioCreateState, config) -> VideoParams:
    ...
```

Muc tieu:

- UI co state ro.
- `tm.start(task_id, params)` van nhan `VideoParams` nhu cu.
- Backend tests hien tai it bi anh huong.

### 7.2. Settings persistence

Nguyen tac:

- User thay doi settings trong `Settings` page thi `config.save_config()` tai submit.
- Trong `Create` page, chi save settings khi user bam action chinh hoac `Save as default`.
- Khong save config moi lan rerun neu chi dang preview mot field.

### 7.3. Projects page

Nguon du lieu ban dau:

```text
storage/tasks/<task_id>/
  script.json
  final-1.mp4
  combined-1.mp4
  subtitle.srt
```

MVP Projects page:

- List task folders theo modified time.
- Card/table hien: task id, subject, status neu doc duoc state, final videos, created/modified time.
- Actions: preview, open folder, copy output path, reuse script/settings.

Chua can database rieng trong phase 1-2.

## 8. Implementation roadmap

### Phase 0: Baseline audit va safety net

Muc tieu: co baseline truoc khi refactor.

**Files:**

- Read: `webui/Main.py`
- Create: `test/webui/test_studio_baseline.py`
- Optional create: `docs/uiux-baseline-2026-05-27.md`

**Steps:**

- [ ] Chup screenshot WebUI hien tai o desktop va mobile neu co browser automation.
- [ ] Liet ke cac label/flow chinh hien tai: Basic Settings, LLM Settings, Video Script Settings, Video Settings, Audio Settings, Subtitle Settings, Generate Video.
- [ ] Tao UI baseline test bang Streamlit AppTest neu tuong thich voi Streamlit 1.45; neu AppTest version trong 1.45 khong du dung, tao smoke test Python import cac helper sau khi tach module.
- [ ] Chay backend regression:

```bash
uv run python -m unittest test.services.test_fonts test.services.test_tiktok test.services.test_material test.services.test_task test.services.test_video.TestVideoService test.controllers.test_video
```

- [ ] Chay compile check:

```bash
uv run python -m compileall app webui main.py
```

**Acceptance:**

- Co baseline ro ve UI hien tai.
- Test/compile hien tai pass truoc khi refactor UI.

### Phase 1: Studio shell va navigation

Muc tieu: tao khung studio chuyen nghiep, chua doi logic generate.

**Files:**

- Modify: `webui/Main.py`
- Create: `webui/studio/bootstrap.py`
- Create: `webui/studio/i18n.py`
- Create: `webui/studio/theme.py`
- Create: `webui/studio/navigation.py`
- Create: `webui/studio/components/layout.py`
- Create: `webui/studio/pages/create.py`
- Create: `webui/studio/pages/projects.py`
- Create: `webui/studio/pages/assets.py`
- Create: `webui/studio/pages/brand.py`
- Create: `webui/studio/pages/settings.py`
- Test: `test/webui/test_studio_navigation.py`

**Steps:**

- [ ] Extract path/init/logger/locale setup tu `Main.py` sang `bootstrap.py`.
- [ ] Them `render_studio_app()` trong `navigation.py`.
- [ ] Dung `st.navigation` neu Streamlit 1.45 da ho tro du; neu gap incompatibility thi fallback sang `st.sidebar.radio` va tach page renderer bang function map.
- [ ] `Main.py` chi con entrypoint va call studio app.
- [ ] Tao top bar: `MoneyPrinterTurbo Studio`, language selector, quick links API docs/open storage neu can.
- [ ] Tao page shells co noi dung toi thieu de verify navigation.
- [ ] Them CSS tokens trong `theme.py`; khong override qua manh cac DOM selector Streamlit de tranh vo sau update.
- [ ] Test navigation labels va render default page.

**Acceptance:**

- `Main.py` giam ro rang ve responsibility.
- User mo WebUI thay khung studio co navigation Create/Projects/Assets/Brand/Settings.
- Chua co regression backend.

### Phase 2: Create page guided workflow

Muc tieu: doi form tao video thanh stepper/guided sections nhung van goi pipeline cu.

**Files:**

- Modify: `webui/studio/pages/create.py`
- Create: `webui/studio/state.py`
- Create: `webui/studio/validators.py`
- Create: `webui/studio/components/actions.py`
- Create: `webui/studio/components/fields.py`
- Create: `webui/studio/components/source_settings.py`
- Create: `webui/studio/components/audio_settings.py`
- Create: `webui/studio/components/subtitle_settings.py`
- Test: `test/webui/test_studio_state.py`
- Test: `test/webui/test_studio_validators.py`

**Steps:**

- [ ] Tao `StudioCreateState` va init defaults tu session/config.
- [ ] Tao `build_video_params()` mapping state/config -> `VideoParams`.
- [ ] Tach `Generate Script`, `Generate Keywords`, `Generate Video` thanh handler functions.
- [ ] Render 6 step bang tabs hoac segmented/radio state:
  - Brief
  - Script & Keywords
  - Source & Materials
  - Voice & Audio
  - Subtitles & Brand
  - Review & Render
- [ ] Moi step co page integrity: chi chua cac fields cung mot sub-task.
- [ ] Source config chi hien theo source dang chon.
- [ ] Advanced settings dat trong expander va co default hop ly.
- [ ] Review step hien summary + validation warnings truoc khi render.
- [ ] Generate video van goi `tm.start(task_id, params)`.
- [ ] Neu `uploaded_files`/`uploaded_audio_file`, giu logic secure filename nhu hien tai.

**Acceptance:**

- User tao video bang luong moi khong can nhin tat ca settings cung luc.
- Local/TikTok/Pexels/Pixabay van map dung `VideoParams`.
- Validation loi source/API key nam gan action render, khong chi log.

### Phase 3: Render status va output review

Muc tieu: lam qua trinh tao video co cam giac studio: dang lam gi, loi o dau, output xem lai duoc.

**Files:**

- Create: `webui/studio/components/status.py`
- Modify: `webui/studio/pages/create.py`
- Modify: `webui/studio/pages/projects.py`
- Test: `test/webui/test_studio_projects.py`

**Steps:**

- [ ] Dung `st.status` cho stages: script, terms, audio, subtitle, materials, combine, final.
- [ ] Chuyen log output vao collapsible "Render log".
- [ ] Sau render, hien output preview, path, open folder.
- [ ] Projects page doc `storage/tasks` va render recent outputs.
- [ ] Neu task co `script.json`, hien subject/script/terms trong detail view.
- [ ] Them action `Reuse in Create` de nap script/terms/materials ve Create state.

**Acceptance:**

- User biet task dang chay toi stage nao.
- User xem lai video da tao ma khong can mo folder bang tay.
- Render fail co message gan voi stage fail.

### Phase 4: Settings center

Muc tieu: dua API/provider/runtime config ra khoi flow tao video.

**Files:**

- Create: `webui/studio/components/llm_settings.py`
- Modify: `webui/studio/pages/settings.py`
- Modify: `webui/studio/components/source_settings.py`
- Test: `test/webui/test_studio_settings.py`

**Steps:**

- [ ] Settings page co sections:
  - LLM Providers
  - TTS Providers
  - Video Sources
  - TikTok Search
  - Runtime/Advanced
- [ ] Moi section dung `st.form` rieng de batch submit.
- [ ] Password inputs khong echo value cong khai trong API key management.
- [ ] Them provider status badges: Configured, Missing key, Optional.
- [ ] Trong Create page, neu missing config thi hien link/action den Settings.
- [ ] Loai bo duplicate Pexels/Pixabay API key management trong right panel cu.

**Acceptance:**

- Flow tao video sach hon.
- Config van ghi vao `config.toml` nhu cu.
- User co the biet provider nao thieu key truoc khi render.

### Phase 5: Brand va subtitle presets

Muc tieu: bien subtitle/font/color thanh preset co the tai su dung.

**Files:**

- Modify: `webui/studio/pages/brand.py`
- Modify: `webui/studio/components/subtitle_settings.py`
- Create: `webui/studio/brand_presets.py`
- Test: `test/webui/test_brand_presets.py`

**Steps:**

- [ ] Tao preset model don gian:

```python
@dataclass
class SubtitlePreset:
    name: str
    font_name: str
    font_size: int
    text_fore_color: str
    stroke_color: str
    stroke_width: float
    subtitle_position: str
    custom_position: float
```

- [ ] Luu presets vao `webui/.streamlit/brand_presets.json` hoac `storage/config/brand_presets.json`.
- [ ] Default presets:
  - Clean Vietnamese Shorts
  - Bold Caption
  - Minimal Lower Third
- [ ] Brand page cho preview sample subtitle.
- [ ] Create page cho chon preset va override tung field.

**Acceptance:**

- User khong phai set font/color moi lan.
- Font Be Vietnam Pro duoc uu tien cho UI ngon hon voi Vietnamese subtitles.

### Phase 6: Assets page

Muc tieu: quan ly nguon va material theo studio logic.

**Files:**

- Modify: `webui/studio/pages/assets.py`
- Create: `webui/studio/assets.py`
- Test: `test/webui/test_studio_assets.py`

**Steps:**

- [ ] List local uploads tu `storage/local_videos`.
- [ ] List TikTok cache tu `storage/cache_videos/tiktok`.
- [ ] Hien metadata co the doc: file name, size, modified time.
- [ ] Cho preview video/image neu Streamlit ho tro file.
- [ ] Them diagnostics cho Pexels/Pixabay/TikTok:
  - API key present/missing
  - provider selected
  - cookie file exists/missing
- [ ] Khong auto delete cache trong MVP; chi them action open folder/copy path.

**Acceptance:**

- User co noi xem material da tai/upload.
- TikTok cookie/config de debug hon.

### Phase 7: Polish, responsive, i18n

Muc tieu: lam UI nhat quan, Vietnamese-friendly, desktop/mobile on.

**Files:**

- Modify: `webui/i18n/vi.json`
- Modify: `webui/i18n/en.json`
- Modify: `webui/studio/theme.py`
- Modify: all `webui/studio/pages/*.py`
- Test: UI smoke plus manual browser pass.

**Steps:**

- [ ] Them translation keys moi cho studio pages.
- [ ] Kiem tra text dai tieng Viet khong tran controls.
- [ ] Kiem tra mobile/narrow layout: khong dung 3 cot co dinh.
- [ ] Dung headings compact trong panels, khong hero typography.
- [ ] Chuan hoa button labels:
  - `Generate Script`
  - `Generate Keywords`
  - `Preview Voice`
  - `Generate Video`
  - `Save Settings`
- [ ] Kiem tra color contrast bang visual inspection.

**Acceptance:**

- UI tieng Viet doc tu nhien.
- Desktop va mobile khong overlap.
- Giao dien co cam giac tool lam viec, khong phai landing page.

## 9. Test plan

### 9.1. Unit tests

Them tests:

```text
test/webui/test_studio_state.py
test/webui/test_studio_validators.py
test/webui/test_brand_presets.py
test/webui/test_studio_assets.py
```

Can cover:

- `build_video_params()` map dung subject/script/source/audio/subtitle.
- Source validation:
  - Pexels missing key -> warning/error dung.
  - Pixabay missing key -> warning/error dung.
  - TikTok SerpAPI missing key -> warning/error dung.
  - TikTok OpenAI provider missing OpenAI key -> warning/error dung.
  - Local source missing material -> warning/error dung.
- Brand preset read/write, invalid JSON fallback safe.
- Assets scanner khong crash khi folder chua ton tai.

### 9.2. Streamlit AppTest

Neu Streamlit 1.45 support du:

- Default app render co title `MoneyPrinterTurbo Studio`.
- Navigation co Create/Projects/Assets/Brand/Settings.
- Create page co 6 steps.
- Chon `TikTok` chi hien TikTok fields.
- Chon `Local` chi hien uploader/material hints.

Neu AppTest bi gioi han:

- Tach UI helpers thanh pure functions de unit test.
- Lam manual smoke voi Streamlit dev server.

### 9.3. Regression commands

Chay truoc khi merge:

```bash
uv run python -m unittest test.services.test_fonts test.services.test_tiktok test.services.test_material test.services.test_task test.services.test_video.TestVideoService test.controllers.test_video
uv run python -m compileall app webui main.py
```

Neu them `test/webui` bang unittest:

```bash
uv run python -m unittest discover -s test
```

### 9.4. Manual QA

Desktop:

- 1440x900
- 1280x720

Mobile/narrow:

- 390x844
- 768x1024

Flows:

- Create Pexels video.
- Create Local video with uploaded file.
- Create TikTok video config screen with OpenAI Web Search selected.
- Preview voice.
- Change font/subtitle preset.
- Open Projects and preview recent output.
- Open Settings and save LLM/API key fields without exposing keys in plain text.

## 10. UX acceptance criteria

Plan duoc coi la trien khai dung khi:

1. User moi co the tao video bang mot guided flow, khong can doc tat ca settings cung luc.
2. User nang cao van truy cap duoc advanced settings nhung khong lam roi flow mac dinh.
3. UI co navigation chinh ro: Create, Projects, Assets, Brand, Settings.
4. Source-specific config chi hien khi source do duoc chon.
5. LLM/TTS/API key settings nam trong Settings, khong chen lam day create flow.
6. Render status hien stage ro va co log collapse.
7. Video output co preview va co the xem lai trong Projects.
8. Subtitle style co preset de tai su dung.
9. UI tieng Viet khong bi tran/overlap trong desktop va mobile.
10. Backend tests hien tai van pass.

## 11. Rui ro va cach giam

### Rui ro 1: Streamlit khong linh hoat nhu React editor

Giam rui ro:

- Phase 1-3 giu Streamlit de nhanh va it rewrite.
- Chi tao studio shell, guided forms, status, projects browser.
- Neu sau nay can timeline/editor drag-drop thuc su, tao frontend rieng React/FastAPI nhung khong can ngay.

### Rui ro 2: `Main.py` refactor lam vo flow generate

Giam rui ro:

- Tach theo phase.
- Moi phase co tests/compile.
- Giu `VideoParams` va `tm.start()` khong doi trong phase dau.

### Rui ro 3: UI dep nhung workflow cham

Giam rui ro:

- Review step phai tom tat du.
- Advanced settings collapse.
- Frequent actions o gan context: generate script trong Script step, preview voice trong Audio step, render trong Review step.

### Rui ro 4: Settings bi save lung tung do Streamlit rerun

Giam rui ro:

- Settings dung `st.form`.
- Chi `config.save_config()` khi submit.
- Create page chi save khi render hoac bam save defaults.

### Rui ro 5: Them page nhung khong co du lieu Projects/Assets

Giam rui ro:

- MVP Projects doc tu `storage/tasks`.
- MVP Assets doc tu `storage/local_videos` va `storage/cache_videos`.
- Chua can database.

## 12. Thu tu uu tien de lam

Lam theo thu tu nay de moi commit deu co gia tri:

1. Phase 0: baseline audit va tests.
2. Phase 1: studio shell/navigation.
3. Phase 2: guided Create page.
4. Phase 3: render status/output review.
5. Phase 4: Settings center.
6. Phase 5: Brand/subtitle presets.
7. Phase 6: Assets page.
8. Phase 7: polish/i18n/responsive.

Neu can cat scope de co MVP nhanh:

- MVP bat buoc: Phase 0, 1, 2, 3, 4.
- MVP co the defer: Phase 5, 6, 7 polish sau.

## 13. Commit strategy

De tranh PR qua lon:

1. `test: add webui studio baseline checks`
2. `refactor: add studio shell navigation`
3. `refactor: split create video workflow`
4. `feat: add studio render status and projects view`
5. `refactor: move provider settings into studio settings`
6. `feat: add subtitle brand presets`
7. `feat: add assets browser`
8. `style: polish studio responsive layout`

Moi commit nen chay:

```bash
uv run python -m compileall app webui main.py
```

Voi commit co logic:

```bash
uv run python -m unittest discover -s test
```

## 14. Definition of Done

Hoan tat UI/UX studio khi co bang chung:

- File `webui/Main.py` khong con chua tat ca UI business logic.
- Cac page studio nam trong `webui/studio/pages`.
- Create flow co guided steps va review/render stage.
- Projects page doc va preview duoc output gan nhat.
- Settings page gom LLM/TTS/source settings.
- Brand page co subtitle presets hoac it nhat preset model/preview.
- Tests/compile pass.
- Manual QA desktop/mobile khong thay overlap hoac text tran nghiem trong.
