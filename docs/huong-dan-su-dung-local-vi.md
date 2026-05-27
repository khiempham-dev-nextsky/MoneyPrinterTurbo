# Huong dan cai dat va su dung MoneyPrinterTurbo local

Tai lieu nay duoc viet cho ban clone hien tai tai:

```bash
/Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
```

Phien ban da kiem tra:

- Repository: https://github.com/harry0703/MoneyPrinterTurbo
- Commit local: `9c96d53`
- MoneyPrinterTurbo: `1.2.7`
- Python runtime: `3.11.14` qua `uv`
- WebUI: http://127.0.0.1:8501
- API docs: http://127.0.0.1:8080/docs
- ReDoc: http://127.0.0.1:8080/redoc

## 1. Yeu cau moi truong

Toi thieu:

- macOS 11+ / Windows 10+ / Linux pho bien.
- CPU 4 nhan, RAM 4 GB tro len.
- GPU khong bat buoc. GPU chi huu ich neu dung Whisper local hoac xu ly nhieu video.
- Internet tot de goi LLM, TTS, Pexels/Pixabay va tai media.
- ImageMagick. Tren may nay da co: `/opt/homebrew/bin/magick`.
- `uv` de quan ly Python/dependency.

Kiem tra nhanh:

```bash
git --version
uv --version
magick -version
```

## 2. Cai dat local

Di vao thu muc project:

```bash
cd /Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
```

Cai Python 3.11 va dependency theo lockfile:

```bash
uv python install 3.11
uv sync --frozen
```

Tao file cau hinh rieng:

```bash
cp config.example.toml config.toml
```

Luu y:

- Khong commit `config.toml` neu co API key that.
- `pyproject.toml` yeu cau Python `>=3.11,<3.13`; khong dung Python 3.13 truc tiep.
- `requirements.txt` chi la cach cai cu. Nen uu tien `uv sync --frozen`.

## 3. Chay ung dung

Chay API:

```bash
cd /Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
uv run python main.py
```

Mo API docs:

```text
http://127.0.0.1:8080/docs
```

Chay WebUI o terminal khac:

```bash
cd /Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false uv run streamlit run ./webui/Main.py \
  --server.headless=true \
  --browser.serverAddress="0.0.0.0" \
  --server.enableCORS=true \
  --browser.gatherUsageStats=false
```

Mo WebUI:

```text
http://127.0.0.1:8501
```

Kiem tra port dang chay:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
lsof -nP -iTCP:8501 -sTCP:LISTEN
```

Dung service:

```bash
lsof -ti tcp:8080 | xargs kill
lsof -ti tcp:8501 | xargs kill
```

## 4. Cau hinh API key trong `config.toml`

Mo file:

```bash
open config.toml
```

Hoac sua truc tiep trong WebUI, phan cau hinh ben trai. WebUI se ghi lai vao `config.toml`.

### 4.1. Nguon video

```toml
[app]
video_source = "pexels" # "pexels", "pixabay", "local", hoac "tiktok"
pexels_api_keys = ["PEXELS_API_KEY_CUA_BAN"]
pixabay_api_keys = ["PIXABAY_API_KEY_CUA_BAN"]
```

Khuyen nghi:

- Dung `pexels` neu co Pexels API key.
- Dung `pixabay` neu Pexels bi gioi han hoac khong co ket qua.
- Dung `local` neu muon upload file `mp4`, `mov`, `avi`, `flv`, `mkv`, `jpg`, `jpeg`, `png` tu may local.
- Dung `tiktok` neu muon app dung LLM hien tai de sinh/rank keyword, tim URL TikTok public qua search provider, tai video bang `yt-dlp`, roi dua vao pipeline ghep video nhu cac nguon khac.

TikTok AI Search:

```toml
[app]
video_source = "tiktok"
tiktok_search_provider = "openai_web_search" # "openai_web_search" hoac "serpapi"
tiktok_search_api_key = "" # chi can khi dung provider "serpapi"
tiktok_max_search_results = 20
tiktok_max_downloads = 5
tiktok_min_duration = 3
tiktok_openai_web_search_timeout = 300
tiktok_cookie_file = ""
```

Giai thich:

- LLM provider trong phan `Cai Dat LLM` sinh/rank keyword theo `Video Subject` / `Video Script`.
- Neu chon `openai_web_search`, app dung chinh setting OpenAI trong `Cai Dat LLM`: `openai_api_key`, `openai_base_url`, `openai_model_name`. Khong can SerpAPI. App search rong tren web bang pattern `"https://www.tiktok.com/@" "/video/" "<keyword>"`, sau do chi nhan URL TikTok video that co dang `https://www.tiktok.com/@creator/video/<numeric_id>`.
- `tiktok_openai_web_search_timeout` la read timeout tinh bang giay cho OpenAI web search. Mac dinh `300` giay de tranh cat request som khi search TikTok lau qua proxy.
- Neu chon `serpapi`, SerpAPI tim cac trang public co URL TikTok video trong link/snippet.
- `yt-dlp` tai video public ve `storage/cache_videos/tiktok/`.
- App se validate file tai ve: ton tai, size > 0, co video stream, duration >= `tiktok_min_duration`.
- App khong remove watermark va khong bypass private/restricted content.
- Chi nen dung video TikTok ban co quyen su dung lai.

Vi du khong dung SerpAPI, dung OpenAI Web Search:

```toml
[app]
llm_provider = "openai"
openai_api_key = "OPENAI_API_KEY_CUA_BAN"
openai_base_url = ""
openai_model_name = "gpt-4o-mini"
video_source = "tiktok"
tiktok_search_provider = "openai_web_search"
```

Neu dung SerpAPI:

```toml
[app]
video_source = "tiktok"
tiktok_search_provider = "serpapi"
tiktok_search_api_key = "SERPAPI_KEY_CUA_BAN"
```

Neu khong muon luu SerpAPI key trong `config.toml`, co the dung bien moi truong:

```bash
export SERPAPI_API_KEY="SERPAPI_KEY_CUA_BAN"
```

App cung chap nhan `SERPAPI_KEY` hoac `TIKTOK_SEARCH_API_KEY`.

Neu TikTok hay chan request tai moi truong cua ban, export cookie tu trinh duyet va gan:

```toml
[app]
tiktok_cookie_file = "/duong/dan/cookies.txt"
```

### 4.2. LLM provider

Provider duoc chon bang:

```toml
[app]
llm_provider = "openai"
```

Mot so cau hinh thuong dung:

OpenAI hoac provider tuong thich OpenAI:

```toml
[app]
llm_provider = "openai"
openai_api_key = "OPENAI_API_KEY_CUA_BAN"
openai_base_url = "" # de trong neu dung OpenAI chinh thuc
openai_model_name = "gpt-4o-mini"
```

DeepSeek:

```toml
[app]
llm_provider = "deepseek"
deepseek_api_key = "DEEPSEEK_API_KEY_CUA_BAN"
deepseek_base_url = "https://api.deepseek.com"
deepseek_model_name = "deepseek-chat"
```

Gemini:

```toml
[app]
llm_provider = "gemini"
gemini_api_key = "GEMINI_API_KEY_CUA_BAN"
gemini_model_name = "gemini-2.5-flash"
```

Ollama local:

```toml
[app]
llm_provider = "ollama"
ollama_base_url = "http://localhost:11434/v1"
ollama_model_name = "qwen:7b"
```

LiteLLM gateway:

```toml
[app]
llm_provider = "litellm"
litellm_model_name = "openai/gpt-4o-mini"
```

Voi LiteLLM, key thuong lay tu bien moi truong, vi du:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
```

### 4.3. Subtitle

Mac dinh:

```toml
[app]
subtitle_provider = "edge"
```

Lua chon:

- `edge`: nhanh, khong can GPU, nen dung mac dinh.
- `whisper`: chat luong on dinh hon nhung cham, co the tai model HuggingFace lon khoang vai GB.
- `""`: tat tao subtitle.

Whisper CPU:

```toml
[whisper]
model_size = "large-v3"
device = "CPU"
compute_type = "int8"
```

Neu khong tai duoc HuggingFace, co the chay:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 4.4. TTS

WebUI ho tro:

- Azure TTS V1 qua `edge-tts`: co the dung nhanh, khong can key rieng trong nhieu truong hop.
- Azure TTS V2: can Azure Speech key.
- SiliconFlow TTS: can `siliconflow.api_key`.
- Gemini TTS: dung `gemini_api_key`.

Azure Speech:

```toml
[azure]
speech_key = "AZURE_SPEECH_KEY_CUA_BAN"
speech_region = "eastus"
```

SiliconFlow:

```toml
[siliconflow]
api_key = "SILICONFLOW_API_KEY_CUA_BAN"
```

### 4.5. Proxy, TLS, Redis va endpoint public

Proxy neu mang can:

```toml
[proxy]
http = "http://user:pass@proxy:1234"
https = "http://user:pass@proxy:1234"
```

Khong nen tat TLS tru khi bat buoc:

```toml
[app]
tls_verify = true
```

Redis cho queue/task state:

```toml
[app]
enable_redis = false
redis_host = "localhost"
redis_port = 6379
redis_db = 0
redis_password = ""
```

Neu expose API sau domain/reverse proxy, sua endpoint de link video tra ve la URL public:

```toml
[app]
endpoint = "https://video.example.com"
```

## 5. Su dung WebUI

Quy trinh co ban:

1. Mo http://127.0.0.1:8501.
2. Trong phan cau hinh, chon LLM provider va nhap API key/model.
3. Nhap Pexels/Pixabay API key neu dung stock video, hoac TikTok Search API key neu dung TikTok.
4. Nhap `Video Subject`, chon ngon ngu script.
5. Bam `Generate Video Script and Keywords`, hoac tu nhap `Video Script` va `Video Keywords`.
6. Chon `Video Source`: Pexels, Pixabay, Local file hoac TikTok.
7. Chon ti le `Portrait 9:16` hoac `Landscape 16:9`.
8. Chon voice, BGM, subtitle style.
9. Tao video va doi task hoan tat.

Phông chữ phụ đề tiếng Việt:

- WebUI tự liệt kê font trong `resource/fonts`; ô `Phông Chữ Phụ Đề` có thể gõ để tìm nhanh theo tên font.
- App đã bundle `BeVietnamPro-Bold.ttf` và `BeVietnamPro-Regular.ttf`, nguồn từ Google Fonts/Be Vietnam Pro, license OFL.
- Với giao diện hoặc video language tiếng Việt, nếu chưa lưu lựa chọn font cũ, WebUI ưu tiên `BeVietnamPro-Bold.ttf`.
- Nếu tự thêm font khác, copy file `.ttf`, `.ttc` hoặc `.otf` vào `resource/fonts`, restart WebUI rồi tìm trong dropdown.

Meo dung khong can LLM:

- Tu nhap `Video Script`.
- Tu nhap `Video Keywords`.
- Dung `video_source = "local"` va upload file local.
- Khi do app khong can sinh script/keyword bang LLM.

Luu y rieng voi TikTok:

- TikTok van can LLM de sinh `Video Keywords` va rank candidate, nen phai cau hinh LLM provider hop le.
- `Video Keywords` duoc dung cho TikTok giong Pexels/Pixabay. App se bien tung keyword thanh query dang `"https://www.tiktok.com/@" "/video/" "<keyword>"` de tim URL video that thay vi channel/tag.
- Neu tu nhap `Video Keywords`, nen dung keyword ngan bang tieng Anh hoac hashtag pho bien de OpenAI web search de tim URL TikTok hon.
- Neu chon `serpapi` ma thieu `tiktok_search_api_key`, WebUI se bao loi truoc khi tao task.
- Neu chon `openai_web_search` ma thieu `openai_api_key`, WebUI se bao loi truoc khi tao task.

## 6. Su dung API

Base URL:

```text
http://127.0.0.1:8080/api/v1
```

### 6.1. Tao video

Vi du dung script va keyword co san:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "5 thoi quen giup lam viec tap trung hon",
    "video_script": "Tap trung khong den tu viec lam nhieu hon, ma den tu viec loai bo nhung thu gay nhieu. Hay bat dau bang mot muc tieu ro rang, tat thong bao, chia cong viec thanh khoang 25 phut, nghi ngan va tong ket cuoi ngay.",
    "video_terms": ["workspace", "focus", "productivity", "planning"],
    "video_aspect": "9:16",
    "video_source": "pexels",
    "video_concat_mode": "random",
    "video_clip_duration": 3,
    "video_count": 1,
    "voice_name": "vi-VN-HoaiMyNeural-Female",
    "subtitle_enabled": true,
    "font_size": 60
  }'
```

Vi du dung TikTok AI Search:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "review kem chong nang cho da dau",
    "video_script": "Kem chong nang tot cho da dau nen mong nhe, khong gay bong dau va de apply lai trong ngay. Hay quan sat texture, do tiệp da va cam giac sau vai gio su dung.",
    "video_aspect": "9:16",
    "video_source": "tiktok",
    "video_concat_mode": "random",
    "video_clip_duration": 3,
    "video_count": 1,
    "voice_name": "vi-VN-HoaiMyNeural-Female",
    "subtitle_enabled": true,
    "font_size": 60
  }'
```

Dieu kien de request TikTok chay duoc:

- `llm_provider` va key/model tuong ung da cau hinh.
- `tiktok_search_provider = "openai_web_search"` va OpenAI API key/model da cau hinh trong `Cai Dat LLM`; hoac `tiktok_search_provider = "serpapi"` va `tiktok_search_api_key` da cau hinh.
- May co Internet de goi LLM, search provider va tai TikTok public video.

Ket qua tra ve dang:

```json
{
  "status": 200,
  "message": "success",
  "data": {
    "task_id": "..."
  }
}
```

### 6.2. Kiem tra task

```bash
curl "http://127.0.0.1:8080/api/v1/tasks/TASK_ID"
```

Khi xong, response co the co:

```json
{
  "state": 1,
  "progress": 100,
  "videos": ["/tasks/TASK_ID/final-1.mp4"],
  "combined_videos": ["/tasks/TASK_ID/combined-1.mp4"]
}
```

Mo video bang URL tra ve hoac vao thu muc:

```bash
open storage/tasks/TASK_ID
```

### 6.3. Tao audio only

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/audio" \
  -H "Content-Type: application/json" \
  -d '{
    "video_script": "Day la noi dung can doc thanh giong noi.",
    "video_language": "vi-VN",
    "voice_name": "vi-VN-HoaiMyNeural-Female",
    "voice_rate": 1.0,
    "voice_volume": 1.0
  }'
```

### 6.4. Tao subtitle only

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/subtitle" \
  -H "Content-Type: application/json" \
  -d '{
    "video_script": "Noi dung can tao phu de.",
    "video_language": "vi-VN",
    "voice_name": "vi-VN-HoaiMyNeural-Female",
    "subtitle_position": "bottom",
    "font_size": 60
  }'
```

### 6.5. Sinh script va keyword bang LLM

Sinh script:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/scripts" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "loi ich cua viec di bo moi ngay",
    "video_language": "vi-VN",
    "paragraph_number": 1
  }'
```

Sinh keyword:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/terms" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "loi ich cua viec di bo moi ngay",
    "video_script": "Di bo moi ngay giup cai thien suc khoe tim mach, giam cang thang va tang nang luong.",
    "amount": 5
  }'
```

### 6.6. Upload BGM va video local

Upload BGM MP3:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/musics" \
  -F "file=@/duong/dan/nhac-nen.mp3"
```

Upload video/image local:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/video_materials" \
  -F "file=@/duong/dan/video.mp4"
```

Lay danh sach:

```bash
curl "http://127.0.0.1:8080/api/v1/musics"
curl "http://127.0.0.1:8080/api/v1/video_materials"
```

## 7. Thu muc dau ra

Du lieu sinh ra nam trong:

```bash
storage/tasks/
```

Cache video tai ve:

```bash
storage/cache_videos/
```

Video/image local upload:

```bash
storage/local_videos/
```

BGM co san va BGM upload:

```bash
resource/songs/
```

## 8. Loi thuong gap

`Couldn't connect to server`

- API/WebUI chua chay hoac port khac dang chiem.
- Kiem tra bang `lsof -nP -iTCP:8080 -sTCP:LISTEN`.

Streamlit hoi email lan dau chay

- Chay voi `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` va `--server.headless=true`.

Loi Python version

- Dung `uv run ...`, khong dung `python` he thong.
- Project can Python `>=3.11,<3.13`.

Khong tai duoc video online

- Kiem tra `pexels_api_keys` / `pixabay_api_keys`.
- Kiem tra proxy/VPN.
- Doi `video_source` sang `local` de test offline voi file co san.

Khong tao duoc video tu TikTok

- Neu dung `openai_web_search`, kiem tra `openai_api_key`, `openai_base_url`, `openai_model_name` trong phan `Cai Dat LLM`.
- Neu dung `serpapi`, kiem tra `tiktok_search_api_key`.
- Kiem tra LLM provider, API key, base URL va model name vi TikTok AI Search can LLM de sinh query/rank ket qua.
- Neu log bao `no TikTok candidates found`, hay doi `Video Keywords` ngan/cu the hon, uu tien tieng Anh hoac hashtag pho bien. TikTok/search provider khong dam bao moi keyword deu co URL video public index duoc.
- Neu log bao `yt-dlp` download fail, thu cau hinh `tiktok_cookie_file`.
- Neu video bi bo qua, file co the qua ngan, rong, hoac khong co video stream.
- App se fail ro rang khi TikTok loi va khong fallback sang Pexels.

Khong sinh script/keyword

- Kiem tra `llm_provider`, API key, base URL, model name.
- Neu dung Ollama, kiem tra `ollama list` va service Ollama dang chay.

Subtitle cham hoac tai model lon

- Dung `subtitle_provider = "edge"` neu khong can Whisper.
- Neu dung Whisper, dam bao mang tai duoc model va co du dung luong dia.

ImageMagick/ffmpeg loi

- macOS: `brew install imagemagick ffmpeg`.
- Neu tu dong detect khong duoc, them vao `config.toml`:

```toml
[app]
imagemagick_path = "/opt/homebrew/bin/magick"
ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
```

## 9. Checklist setup nhanh

```bash
cd /Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
uv python install 3.11
uv sync --frozen
cp config.example.toml config.toml
uv run python main.py
```

Terminal khac:

```bash
cd /Users/khiempham/Documents/Codex/2026-05-27/goal-c-i-t-harry0703-moneyprinterturbo/MoneyPrinterTurbo
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false uv run streamlit run ./webui/Main.py \
  --server.headless=true \
  --browser.serverAddress="0.0.0.0" \
  --server.enableCORS=true \
  --browser.gatherUsageStats=false
```

Sau do mo:

- WebUI: http://127.0.0.1:8501
- API docs: http://127.0.0.1:8080/docs
