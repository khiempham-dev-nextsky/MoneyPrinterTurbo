
import unittest
import os
import shutil
import sys
import tempfile
import types
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from moviepy import (
    VideoFileClip,
)
# add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.config import config
from app.controllers.manager.base_manager import TaskQueueFullError
from app.controllers.manager.memory_manager import InMemoryTaskManager
from app.controllers.v1 import video as video_controller
from app.models import const
from app.models.schema import MaterialInfo, TranslateVideoParams, VideoConcatMode
from app.services import state as sm
from app.services import video as vd
from app.utils import utils

resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")


class _FakeRequest:
    def __init__(self):
        self.headers = {"x-task-id": "test-request"}


class TestSecurityControls(unittest.TestCase):
    def setUp(self):
        self.original_app_config = dict(config.app)

    def tearDown(self):
        config.app.clear()
        config.app.update(self.original_app_config)

    def test_task_query_returns_relative_task_url_without_mutating_state(self):
        """
        endpoint 未显式配置时，任务查询接口不能使用 Host 派生绝对 URL，
        也不能把展示 URL 回写到任务状态里，否则不同 Host 查询会污染结果。
        """
        task_id = "security-task-url"
        task_dir = utils.task_dir(task_id)
        video_path = os.path.join(task_dir, "final-1.mp4")
        Path(video_path).write_bytes(b"fake-video")
        config.app["endpoint"] = ""

        try:
            sm.state.update_task(
                task_id,
                state=const.TASK_STATE_COMPLETE,
                videos=[video_path],
                combined_videos=[video_path],
            )

            response = video_controller.get_task(_FakeRequest(), task_id=task_id)

            self.assertEqual(response["data"]["videos"], [f"/tasks/{task_id}/final-1.mp4"])
            self.assertEqual(sm.state.get_task(task_id)["videos"], [video_path])
        finally:
            sm.state.delete_task(task_id)
            shutil.rmtree(task_dir, ignore_errors=True)

    def test_in_memory_task_manager_rejects_when_queue_is_full(self):
        """
        并发数用尽后，等待队列必须有硬上限。这里用 max_concurrent_tasks=0
        强制任务进入队列，验证超过 max_queued_tasks 时会拒绝继续入队。
        """
        manager = InMemoryTaskManager(max_concurrent_tasks=0, max_queued_tasks=1)

        manager.add_task(lambda: None)

        with self.assertRaises(TaskQueueFullError):
            manager.add_task(lambda: None)

class TestVideoService(unittest.TestCase):
    def setUp(self):
        self.test_img_path = os.path.join(resources_dir, "1.png")
    
    def tearDown(self):
        pass
    
    def test_preprocess_video(self):
        if not os.path.exists(self.test_img_path):
            self.fail(f"test image not found: {self.test_img_path}")

        local_videos_dir = utils.storage_dir("local_videos", create=True)
        safe_img_path = os.path.join(local_videos_dir, "test-preprocess-1.png")
        shutil.copy2(self.test_img_path, safe_img_path)

        # test preprocess_video function
        m = MaterialInfo()
        m.url = os.path.basename(safe_img_path)
        m.provider = "local"
        print(m)

        try:
            materials = vd.preprocess_video([m], clip_duration=4)
            print(materials)

            # verify result
            self.assertIsNotNone(materials)
            self.assertEqual(len(materials), 1)
            self.assertTrue(materials[0].url.endswith(".mp4"))

            # moviepy get video info
            clip = VideoFileClip(materials[0].url)
            print(clip)

            # clean generated test video file
            if os.path.exists(materials[0].url):
                os.remove(materials[0].url)
        finally:
            if os.path.exists(safe_img_path):
                os.remove(safe_img_path)

    def test_preprocess_video_rejects_material_outside_local_videos(self):
        """
        local 素材路径来自 API 参数，不能允许任意绝对路径进入 MoviePy。
        这里验证非 local_videos 白名单目录内的路径会被跳过，避免任意文件读取。
        """
        m = MaterialInfo(provider="local", url=self.test_img_path)

        materials = vd.preprocess_video([m], clip_duration=4)

        self.assertEqual(materials, [])

    def test_get_bgm_file_accepts_song_directory_filename(self):
        """
        BGM 列表接口现在只暴露文件名；生成视频时应能把文件名安全解析回
        resource/songs 白名单目录，保持正常使用路径可用。
        """
        song_dir = utils.song_dir()
        bgm_path = os.path.join(song_dir, "test-safe-bgm.mp3")
        Path(bgm_path).write_bytes(b"fake-mp3")

        try:
            self.assertEqual(vd.get_bgm_file(bgm_file="test-safe-bgm.mp3"), bgm_path)
        finally:
            if os.path.exists(bgm_path):
                os.remove(bgm_path)

    def test_get_bgm_file_rejects_path_outside_song_directory(self):
        """
        用户传入的 bgm_file 不能直接作为本地路径打开，否则可能读取系统文件。
        即使外部文件存在，也必须因为不在 songs 目录内被拒绝。
        """
        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_bgm:
            self.assertEqual(vd.get_bgm_file(bgm_file=temp_bgm.name), "")

    def test_get_ffmpeg_binary_uses_configured_env_path(self):
        """配置中显式指定 ffmpeg 时，应优先使用该路径。"""
        with patch.dict(os.environ, {"IMAGEIO_FFMPEG_EXE": "/tmp/custom-ffmpeg"}, clear=True):
            self.assertEqual(vd.get_ffmpeg_binary(), "/tmp/custom-ffmpeg")

    def test_get_ffmpeg_binary_falls_back_to_imageio_ffmpeg(self):
        """
        Windows 便携包里系统 PATH 可能没有 ffmpeg，但 moviepy 依赖的
        imageio-ffmpeg 通常会提供可执行文件。这里验证该兜底路径可用。
        """
        fake_imageio_ffmpeg = types.SimpleNamespace(
            get_ffmpeg_exe=lambda: "/tmp/bundled-ffmpeg"
        )

        with patch.dict(os.environ, {}, clear=True), patch.object(
            vd.shutil, "which", return_value=None
        ), patch.dict(sys.modules, {"imageio_ffmpeg": fake_imageio_ffmpeg}):
            self.assertEqual(vd.get_ffmpeg_binary(), "/tmp/bundled-ffmpeg")

    def test_open_video_clip_quietly_suppresses_moviepy_stdout(self):
        """
        MoviePy 2.1.x 的 FFMPEG_VideoReader 会直接向 stdout 打印 metadata
        和 ffmpeg 命令。项目服务层应屏蔽这类依赖库噪声，避免用户把
        `audio_found: False` 误判为最终视频没有音频。
        """
        video_path = os.path.join(resources_dir, "1.png.mp4")
        if not os.path.exists(video_path):
            self.fail(f"test video not found: {video_path}")

        stdout = StringIO()
        with redirect_stdout(stdout):
            clip = vd._open_video_clip_quietly(video_path)

        try:
            self.assertEqual(stdout.getvalue(), "")
            self.assertIsNone(clip.audio)
            self.assertGreater(clip.duration, 0)
        finally:
            vd.close_clip(clip)

    def test_combine_videos_closes_audio_clip_when_duration_read_fails(self):
        """
        `combine_videos()` 只需要读取旁白音频时长。即使读取 duration
        时发生异常，也必须关闭 AudioFileClip，避免文件句柄泄漏。
        """

        class _FakeAudioReader:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        class _BrokenAudioClip:
            def __init__(self):
                self.reader = _FakeAudioReader()

            @property
            def duration(self):
                raise RuntimeError("failed to read duration")

        fake_audio_clip = _BrokenAudioClip()

        with patch.object(vd, "AudioFileClip", return_value=fake_audio_clip):
            with self.assertRaises(RuntimeError):
                vd.combine_videos(
                    combined_video_path="/tmp/unused-combined.mp4",
                    video_paths=[],
                    audio_file="/tmp/unused-audio.mp3",
                )

        self.assertTrue(fake_audio_clip.reader.closed)

    def test_combine_videos_skips_sub_frame_tail_clips(self):
        """
        Pexels 素材时长经常会比 max_clip_duration 多出 0.01s 这类尾巴。
        这种短于一帧的片段会被 MoviePy 写成无视频流的 mp4，随后导致
        ffmpeg concat 报 "Output file does not contain any stream"。
        """
        written_durations = []
        concat_inputs = []

        class _FakeReader:
            def close(self):
                pass

        class _FakeClip:
            def __init__(self, duration):
                self.duration = duration
                self.size = (1080, 1920)
                self.w = 1080
                self.h = 1920
                self.reader = _FakeReader()
                self.audio = None
                self.mask = None
                self.clips = []

            def subclipped(self, start, end):
                return _FakeClip(end - start)

            def write_videofile(self, file_path, logger=None, fps=None, codec=None):
                written_durations.append(self.duration)
                Path(file_path).write_bytes(b"fake-video")

        class _FakeAudioClip(_FakeClip):
            def __init__(self):
                super().__init__(10.5)

        def _fake_concat(clip_files, output_file, threads, output_dir):
            concat_inputs.extend(clip_files)
            Path(output_file).write_bytes(b"fake-combined")

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            vd, "AudioFileClip", return_value=_FakeAudioClip()
        ), patch.object(
            vd, "VideoFileClip", return_value=_FakeClip(10.01)
        ), patch.object(
            vd, "concat_video_clips_with_ffmpeg", side_effect=_fake_concat
        ):
            output_path = os.path.join(temp_dir, "combined.mp4")

            vd.combine_videos(
                combined_video_path=output_path,
                video_paths=["source.mp4"],
                audio_file="audio.mp3",
                video_concat_mode=VideoConcatMode.random,
                max_clip_duration=10,
            )

        self.assertEqual(written_durations, [10])
        self.assertEqual(len(concat_inputs), 2)

    def test_resolve_existing_video_canvas_size_uses_source_dimensions(self):
        self.assertEqual(
            vd._resolve_existing_video_canvas_size((720, 1280), "source"),
            (720, 1280),
        )
        self.assertEqual(
            vd._resolve_existing_video_canvas_size((720, 1280), "9:16"),
            (1080, 1920),
        )

    def test_render_existing_video_preserves_source_canvas(self):
        written = {}

        class _FakeAudioReader:
            def close(self):
                pass

        class _FakeSourceAudio:
            duration = 2
            fps = 44100

            def with_effects(self, effects):
                written["source_audio_effects"] = effects
                return self

        class _FakeAudioClip:
            duration = 3
            fps = 24000
            reader = _FakeAudioReader()

            def with_effects(self, effects):
                return self

            def subclipped(self, start, end):
                written["audio_subclip"] = (start, end)
                return self

        class _FakeCompositeAudioClip:
            duration = 2
            fps = 24000

            def __init__(self, clips):
                written["mixed_audio_clips"] = clips

        class _FakeVideoClip:
            duration = 2
            size = (720, 1280)
            w = 720
            h = 1280
            audio = _FakeSourceAudio()
            mask = None
            clips = []
            reader = _FakeAudioReader()

            def with_audio(self, audio):
                self.audio = audio
                written["audio"] = audio
                return self

            def with_duration(self, duration):
                written["video_duration"] = duration
                self.duration = duration
                return self

            def write_videofile(self, output_file, **kwargs):
                written["output_file"] = output_file
                written["kwargs"] = kwargs
                Path(output_file).write_bytes(b"video")

        params = TranslateVideoParams(
            source_video_path="/tmp/source.mp4",
            voice_name="vi-VN-HoaiMyNeural-Female",
            video_aspect="source",
            bgm_type="",
            subtitle_enabled=False,
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            vd,
            "_open_video_clip_quietly",
            return_value=_FakeVideoClip(),
        ), patch.object(vd, "AudioFileClip", return_value=_FakeAudioClip()), patch.object(
            vd, "CompositeAudioClip", _FakeCompositeAudioClip
        ):
            output_file = os.path.join(temp_dir, "final.mp4")

            vd.render_existing_video(
                source_video_path="/tmp/source.mp4",
                audio_path="/tmp/audio.mp3",
                subtitle_path="",
                output_file=output_file,
                params=params,
            )

        self.assertEqual(written["output_file"], output_file)
        self.assertEqual(written["kwargs"]["audio_fps"], 24000)
        self.assertEqual(written["audio_subclip"], (0, 2))
        self.assertIn("source_audio_effects", written)
        self.assertEqual(len(written["mixed_audio_clips"]), 2)

    def test_render_existing_video_opens_source_with_audio(self):
        class _FakeReader:
            def close(self):
                pass

        class _FakeSourceAudio:
            duration = 2
            fps = 44100

            def with_effects(self, effects):
                return self

        class _FakeVideoClip:
            duration = 2
            size = (720, 1280)
            w = 720
            h = 1280
            audio = _FakeSourceAudio()
            mask = None
            clips = []
            reader = _FakeReader()

            def with_audio(self, audio):
                self.audio = audio
                return self

            def with_duration(self, duration):
                return self

            def write_videofile(self, output_file, **kwargs):
                Path(output_file).write_bytes(b"video")

        params = TranslateVideoParams(
            source_video_path="/tmp/source.mp4",
            voice_name="",
            video_aspect="source",
            bgm_type="",
            subtitle_enabled=False,
            voice_enabled=False,
            source_audio_enabled=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            vd,
            "_open_video_clip_quietly",
            return_value=_FakeVideoClip(),
        ) as open_video:
            vd.render_existing_video(
                source_video_path="/tmp/source.mp4",
                audio_path="",
                subtitle_path="",
                output_file=os.path.join(temp_dir, "final.mp4"),
                params=params,
            )

        open_video.assert_called_once_with("/tmp/source.mp4", audio=True)

    def test_render_existing_video_can_disable_voice_and_keep_source_audio(self):
        written = {}

        class _FakeReader:
            def close(self):
                pass

        class _FakeSourceAudio:
            duration = 2
            fps = 44100

            def with_effects(self, effects):
                written["source_audio_effects"] = effects
                return self

        class _FakeVideoClip:
            duration = 2
            size = (720, 1280)
            w = 720
            h = 1280
            audio = _FakeSourceAudio()
            mask = None
            clips = []
            reader = _FakeReader()

            def with_audio(self, audio):
                self.audio = audio
                written["audio"] = audio
                return self

            def with_duration(self, duration):
                return self

            def write_videofile(self, output_file, **kwargs):
                written["kwargs"] = kwargs
                Path(output_file).write_bytes(b"video")

        params = TranslateVideoParams(
            source_video_path="/tmp/source.mp4",
            voice_name="",
            video_aspect="source",
            bgm_type="",
            subtitle_enabled=False,
            voice_enabled=False,
            source_audio_enabled=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            vd,
            "_open_video_clip_quietly",
            return_value=_FakeVideoClip(),
        ), patch.object(vd, "AudioFileClip") as audio_file_clip:
            vd.render_existing_video(
                source_video_path="/tmp/source.mp4",
                audio_path="",
                subtitle_path="",
                output_file=os.path.join(temp_dir, "final.mp4"),
                params=params,
            )

        audio_file_clip.assert_not_called()
        self.assertIn("source_audio_effects", written)
        self.assertEqual(written["audio"], _FakeVideoClip.audio)
        self.assertEqual(written["kwargs"]["audio_fps"], 44100)

    def test_render_existing_video_preserves_source_duration_after_subtitles(self):
        written = {}

        class _FakeReader:
            def close(self):
                pass

        class _FakeTextClip:
            h = 24
            reader = _FakeReader()
            audio = None
            mask = None
            clips = []

            def with_start(self, start):
                return self

            def with_end(self, end):
                return self

            def with_duration(self, duration):
                return self

            def with_position(self, position):
                return self

        class _FakeAudioClip:
            duration = 5
            fps = 24000
            reader = _FakeReader()

            def with_effects(self, effects):
                return self

            def subclipped(self, start, end):
                written["audio_subclip"] = (start, end)
                return self

        class _FakeVideoClip:
            duration = 2
            size = (720, 1280)
            w = 720
            h = 1280
            audio = None
            mask = None
            clips = []
            reader = _FakeReader()

            def with_audio(self, audio):
                return self

            def with_duration(self, duration):
                written["video_duration"] = duration
                self.duration = duration
                return self

            def write_videofile(self, output_file, **kwargs):
                Path(output_file).write_bytes(b"video")

        class _FakeCompositeClip(_FakeVideoClip):
            duration = 4

        class _FakeSubtitlesClip:
            subtitles = [((0, 4), "subtitle kéo dài hơn video")]

        params = TranslateVideoParams(
            source_video_path="/tmp/source.mp4",
            voice_name="vi-VN-HoaiMyNeural-Female",
            video_aspect="source",
            bgm_type="",
            subtitle_enabled=True,
            font_name="BeVietnamPro-Bold.ttf",
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            vd,
            "_open_video_clip_quietly",
            return_value=_FakeVideoClip(),
        ), patch.object(vd, "AudioFileClip", return_value=_FakeAudioClip()), patch.object(
            vd, "SubtitlesClip", return_value=_FakeSubtitlesClip()
        ), patch.object(vd, "TextClip", return_value=_FakeTextClip()), patch.object(
            vd, "wrap_text", return_value=("subtitle", 20)
        ), patch.object(vd, "CompositeVideoClip", return_value=_FakeCompositeClip()):
            vd.render_existing_video(
                source_video_path="/tmp/source.mp4",
                audio_path="/tmp/audio.mp3",
                subtitle_path="/tmp/subtitle.srt",
                output_file=os.path.join(temp_dir, "final.mp4"),
                params=params,
            )

        self.assertEqual(written["video_duration"], 2)
        self.assertEqual(written["audio_subclip"], (0, 2))
    
    def test_wrap_text(self):
        """test text wrapping function"""
        try:
            font_path = os.path.join(utils.font_dir(), "STHeitiMedium.ttc")
            if not os.path.exists(font_path):
                self.fail(f"font file not found: {font_path}")
                
            # test english text wrapping
            test_text_en = "This is a test text for wrapping long sentences in english language"
            
            wrapped_text_en, text_height_en = vd.wrap_text(
                text=test_text_en,
                max_width=300,
                font=font_path,
                fontsize=30
            )
            print(wrapped_text_en, text_height_en)
            # verify text is wrapped
            self.assertIn("\n", wrapped_text_en)
            
            # test chinese text wrapping
            test_text_zh = "这是一段用来测试中文长句换行的文本内容，应该会根据宽度限制进行换行处理"
            wrapped_text_zh, text_height_zh = vd.wrap_text(
                text=test_text_zh,
                max_width=300,
                font=font_path,
                fontsize=30
            )   
            print(wrapped_text_zh, text_height_zh)
            # verify chinese text is wrapped
            self.assertIn("\n", wrapped_text_zh)
        except Exception as e:
            self.fail(f"test wrap_text failed: {str(e)}")

if __name__ == "__main__":
    unittest.main() 
