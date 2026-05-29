import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services import source_video


class _FakeUpload:
    name = "../../clip.MP4"

    def getbuffer(self):
        return b"fake-video"


class _FakeResponse:
    headers = {"content-length": "10"}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=1024):
        yield b"fake-video"


class TestSourceVideoService(unittest.TestCase):
    def test_download_rejects_non_http_and_private_hosts(self):
        with self.assertRaises(ValueError):
            source_video.download_source_video_url("task", "file:///tmp/a.mp4")

        with self.assertRaises(ValueError):
            source_video.download_source_video_url("task", "http://127.0.0.1/a.mp4")

    def test_persist_uploaded_source_video_uses_safe_task_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch.object(
            source_video.utils,
            "task_dir",
            return_value=tmp_dir,
        ), patch.object(source_video, "validate_source_video", return_value={"duration": 5}):
            result = source_video.persist_uploaded_source_video("task-id", _FakeUpload())

        self.assertEqual(Path(result).name, "source.mp4")
        self.assertTrue(Path(result).is_absolute())

    def test_direct_video_url_downloads_into_task_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch.object(
            source_video.utils,
            "task_dir",
            return_value=tmp_dir,
        ), patch.object(
            source_video.requests,
            "get",
            return_value=_FakeResponse(),
        ) as get, patch.object(source_video, "validate_source_video", return_value={"duration": 5}):
            result = source_video.download_source_video_url(
                "task-id",
                "https://example.com/video.mp4",
            )

        self.assertEqual(Path(result).name, "source-download.mp4")
        self.assertTrue(Path(result).is_absolute())
        get.assert_called_once()

    def test_download_uses_youtube_dl_for_player_url(self):
        created = {}

        class FakeYoutubeDL:
            def __init__(self, opts):
                created["opts"] = opts

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def download(self, urls):
                created["urls"] = urls
                output = created["opts"]["outtmpl"].replace("%(ext)s", "mp4")
                Path(output).write_bytes(b"fake-video")

        with tempfile.TemporaryDirectory() as tmp_dir, patch.object(
            source_video.utils,
            "task_dir",
            return_value=tmp_dir,
        ), patch.object(
            source_video,
            "YoutubeDL",
            FakeYoutubeDL,
        ), patch.object(source_video, "validate_source_video", return_value={"duration": 5}):
            result = source_video.download_source_video_url(
                "task-id",
                "https://www.tiktok.com/@creator/video/1234567890",
            )

        self.assertEqual(Path(result).suffix, ".mp4")
        self.assertEqual(created["urls"], ["https://www.tiktok.com/@creator/video/1234567890"])
        self.assertTrue(created["opts"]["outtmpl"].startswith(tmp_dir))

    def test_validate_source_video_rejects_video_without_audio(self):
        fake_clip = SimpleNamespace(
            duration=3,
            fps=30,
            size=(720, 1280),
            audio=None,
            close=lambda: None,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp4") as video_file, patch.object(
            source_video,
            "VideoFileClip",
            return_value=fake_clip,
        ):
            video_file.write(b"video")
            video_file.flush()
            with self.assertRaises(ValueError) as cm:
                source_video.validate_source_video(video_file.name)

        self.assertIn("no audio", str(cm.exception))

    def test_extract_audio_runs_ffmpeg_into_task_wav(self):
        with patch.object(
            source_video.video_service,
            "get_ffmpeg_binary",
            return_value="/usr/bin/ffmpeg",
        ), patch.object(source_video.subprocess, "run") as run:
            run.return_value = SimpleNamespace(returncode=0, stderr="", stdout="")

            result = source_video.extract_audio("/tmp/source.mp4", "/tmp/source-audio.wav")

        self.assertEqual(result, "/tmp/source-audio.wav")
        self.assertEqual(
            run.call_args.args[0],
            [
                "/usr/bin/ffmpeg",
                "-y",
                "-i",
                "/tmp/source.mp4",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "/tmp/source-audio.wav",
            ],
        )


if __name__ == "__main__":
    unittest.main()
