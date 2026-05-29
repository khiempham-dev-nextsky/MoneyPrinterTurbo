import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.schema import TranslateVideoParams
from app.services import subtitle, translate_video
from app.utils import utils


class TestTranslateVideoService(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(utils.task_dir("translate-test-task"), ignore_errors=True)

    def test_write_translated_srt_preserves_source_timing(self):
        task_dir = Path(utils.task_dir("translate-test-task"))
        output_file = task_dir / "translated.srt"
        source_items = [
            (1, "00:00:00,000 --> 00:00:01,500", "Hello"),
            (2, "00:00:01,500 --> 00:00:03,000", "Bye"),
        ]

        translate_video.write_translated_srt(
            source_items,
            ["Xin chào", "Tạm biệt"],
            str(output_file),
        )

        self.assertEqual(
            output_file.read_text(encoding="utf-8").strip(),
            "\n\n".join(
                [
                    "1\n00:00:00,000 --> 00:00:01,500\nXin chào",
                    "2\n00:00:01,500 --> 00:00:03,000\nTạm biệt",
                ]
            ),
        )
        self.assertEqual(len(subtitle.file_to_subtitles(str(output_file))), 2)

    def test_build_synced_dub_audio_places_segments_on_source_timeline(self):
        task_dir = Path(utils.task_dir("translate-test-task"))
        source_items = [
            (1, "00:00:00,000 --> 00:00:01,500", "Hello"),
            (2, "00:00:01,500 --> 00:00:03,000", "Bye"),
        ]
        commands = []

        def fake_tts(text, voice_name, voice_rate, voice_file, voice_volume=1.0):
            Path(voice_file).write_bytes(text.encode("utf-8"))
            return object()

        def fake_duration(path):
            if str(path).endswith("segment-001.mp3"):
                return 2.0
            return 1.0

        def fake_speed_adjust(input_file, output_file, speed):
            Path(output_file).write_bytes(Path(input_file).read_bytes())
            commands.append(("speed", input_file, output_file, round(speed, 2)))
            return output_file

        def fake_run_ffmpeg(command):
            commands.append(command)
            Path(command[-1]).write_bytes(b"mixed-audio")

        params = TranslateVideoParams(
            target_language="vi-VN",
            voice_name="vi-VN-HoaiMyNeural-Female",
            voice_rate=1.0,
            voice_volume=1.0,
        )

        with (
            patch.object(translate_video.voice, "tts", side_effect=fake_tts) as tts,
            patch.object(translate_video.voice, "get_audio_duration", side_effect=fake_duration),
            patch.object(translate_video, "_speed_adjust_audio", side_effect=fake_speed_adjust),
            patch.object(translate_video, "_run_ffmpeg", side_effect=fake_run_ffmpeg),
        ):
            audio_path = translate_video.build_synced_dub_audio(
                source_items=source_items,
                translated_segments=["Xin chào", "Tạm biệt"],
                params=params,
                task_dir=task_dir,
                source_duration=3.0,
            )

        self.assertEqual(audio_path, str(task_dir / "translated-audio.mp3"))
        self.assertEqual(tts.call_count, 2)
        self.assertIn(("speed", str(task_dir / "segment-001.mp3"), str(task_dir / "segment-001-sync.mp3"), 1.33), commands)
        mix_command = commands[-1]
        self.assertIn("-filter_complex", mix_command)
        filter_complex = mix_command[mix_command.index("-filter_complex") + 1]
        self.assertIn("adelay=0:all=1", filter_complex)
        self.assertIn("adelay=1500:all=1", filter_complex)
        self.assertIn("amix=inputs=3:duration=first:dropout_transition=0", filter_complex)
        self.assertTrue(os.path.exists(audio_path))

    def test_build_continuous_dub_audio_compacts_long_subtitle_gaps(self):
        task_dir = Path(utils.task_dir("translate-test-task"))
        source_items = [
            (1, "00:00:00,000 --> 00:00:01,000", "Hello"),
            (2, "00:00:05,000 --> 00:00:06,000", "Bye"),
        ]
        mixed_segments = []

        def fake_tts(text, voice_name, voice_rate, voice_file, voice_volume=1.0):
            Path(voice_file).write_bytes(text.encode("utf-8"))
            return object()

        def fake_duration(path):
            return 0.5

        def fake_mix(segment_inputs, output_file, source_duration):
            mixed_segments.extend(segment_inputs)
            Path(output_file).write_bytes(b"mixed-audio")
            return output_file

        params = TranslateVideoParams(
            target_language="vi-VN",
            voice_name="vi-VN-HoaiMyNeural-Female",
            voice_rate=1.0,
            voice_volume=1.0,
        )

        with (
            patch.object(translate_video.voice, "tts", side_effect=fake_tts),
            patch.object(translate_video.voice, "get_audio_duration", side_effect=fake_duration),
            patch.object(translate_video, "_mix_synced_segments", side_effect=fake_mix),
        ):
            audio_path, scheduled_segments = translate_video.build_continuous_dub_audio(
                source_items=source_items,
                translated_segments=["Xin chào", "Tạm biệt"],
                params=params,
                task_dir=task_dir,
                source_duration=6.0,
            )

        self.assertEqual(audio_path, str(task_dir / "translated-audio.mp3"))
        self.assertEqual([item[0] for item in mixed_segments], [0, 680])
        self.assertEqual(
            [(round(item["start"], 2), round(item["end"], 2)) for item in scheduled_segments],
            [(0.0, 0.5), (0.68, 1.18)],
        )

    def test_write_translated_srt_from_timeline_uses_scheduled_timing(self):
        task_dir = Path(utils.task_dir("translate-test-task"))
        output_file = task_dir / "translated-continuous.srt"

        translate_video.write_translated_srt_from_timeline(
            [
                {"start": 0.0, "end": 0.5, "text": "Xin chào"},
                {"start": 0.68, "end": 1.18, "text": "Tạm biệt"},
            ],
            str(output_file),
        )

        self.assertEqual(
            output_file.read_text(encoding="utf-8").strip(),
            "\n\n".join(
                [
                    "1\n00:00:00,000 --> 00:00:00,500\nXin chào",
                    "2\n00:00:00,680 --> 00:00:01,180\nTạm biệt",
                ]
            ),
        )

    def test_start_sync_mode_uses_segment_dubbing(self):
        task_id = "translate-test-task"
        task_dir = Path(utils.task_dir(task_id))
        source_video = str(task_dir / "source.mp4")
        source_audio = str(task_dir / "source-audio.wav")
        synced_audio = str(task_dir / "translated-audio.mp3")
        Path(source_video).write_bytes(b"video")

        def fake_transcribe(audio_file, subtitle_file):
            Path(subtitle_file).write_text(
                "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n",
                encoding="utf-8",
            )

        def fake_render(source_video_path, audio_path, subtitle_path, output_file, params):
            Path(output_file).write_bytes(b"final-video")

        params = TranslateVideoParams(
            source_video_url="https://www.tiktok.com/@demo/video/123",
            target_language="vi-VN",
            voice_name="vi-VN-HoaiMyNeural-Female",
            bgm_type="",
            dubbing_mode="sync",
        )

        with (
            patch.object(
                translate_video.source_video,
                "download_source_video_url",
                return_value=source_video,
            ),
            patch.object(
                translate_video.source_video,
                "validate_source_video",
                return_value={"duration": 3, "fps": 30, "width": 720, "height": 1280},
            ),
            patch.object(
                translate_video.source_video,
                "extract_audio",
                return_value=source_audio,
            ),
            patch.object(translate_video.subtitle, "create", side_effect=fake_transcribe),
            patch.object(
                translate_video.llm,
                "translate_segments",
                return_value=["Xin chào"],
            ),
            patch.object(
                translate_video,
                "build_synced_dub_audio",
                return_value=synced_audio,
            ) as build_synced_audio,
            patch.object(translate_video.voice, "tts") as tts,
            patch.object(translate_video.voice, "create_subtitle") as create_subtitle,
            patch.object(
                translate_video.video,
                "render_existing_video",
                side_effect=fake_render,
            ) as render_existing_video,
        ):
            result = translate_video.start(task_id=task_id, params=params)

        self.assertEqual(result["audio_file"], synced_audio)
        build_synced_audio.assert_called_once()
        tts.assert_not_called()
        create_subtitle.assert_not_called()
        render_existing_video.assert_called_once()

    def test_start_continuous_mode_uses_continuous_dubbing_and_scheduled_subtitle(self):
        task_id = "translate-test-task"
        task_dir = Path(utils.task_dir(task_id))
        source_video = str(task_dir / "source.mp4")
        source_audio = str(task_dir / "source-audio.wav")
        continuous_audio = str(task_dir / "translated-audio.mp3")
        Path(source_video).write_bytes(b"video")

        def fake_transcribe(audio_file, subtitle_file):
            Path(subtitle_file).write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nHello\n\n"
                "2\n00:00:05,000 --> 00:00:06,000\nBye\n\n",
                encoding="utf-8",
            )

        def fake_render(source_video_path, audio_path, subtitle_path, output_file, params):
            Path(output_file).write_bytes(b"final-video")

        params = TranslateVideoParams(
            source_video_url="https://www.tiktok.com/@demo/video/123",
            target_language="vi-VN",
            voice_name="vi-VN-HoaiMyNeural-Female",
            bgm_type="",
            dubbing_mode="continuous",
        )

        with (
            patch.object(
                translate_video.source_video,
                "download_source_video_url",
                return_value=source_video,
            ),
            patch.object(
                translate_video.source_video,
                "validate_source_video",
                return_value={"duration": 6, "fps": 30, "width": 720, "height": 1280},
            ),
            patch.object(
                translate_video.source_video,
                "extract_audio",
                return_value=source_audio,
            ),
            patch.object(translate_video.subtitle, "create", side_effect=fake_transcribe),
            patch.object(
                translate_video.llm,
                "translate_segments",
                return_value=["Xin chào", "Tạm biệt"],
            ),
            patch.object(
                translate_video,
                "build_continuous_dub_audio",
                return_value=(
                    continuous_audio,
                    [
                        {"start": 0.0, "end": 0.5, "text": "Xin chào"},
                        {"start": 0.68, "end": 1.18, "text": "Tạm biệt"},
                    ],
                ),
            ) as build_continuous_audio,
            patch.object(translate_video.voice, "tts") as tts,
            patch.object(translate_video.voice, "create_subtitle") as create_subtitle,
            patch.object(
                translate_video.video,
                "render_existing_video",
                side_effect=fake_render,
            ) as render_existing_video,
        ):
            result = translate_video.start(task_id=task_id, params=params)

        self.assertEqual(result["audio_file"], continuous_audio)
        self.assertEqual(result["subtitle_path"], str(task_dir / "translated-continuous-timing.srt"))
        self.assertTrue(os.path.exists(result["subtitle_path"]))
        build_continuous_audio.assert_called_once()
        tts.assert_not_called()
        create_subtitle.assert_not_called()
        render_existing_video.assert_called_once()


    def test_start_voice_disabled_skips_tts_and_keeps_source_audio_for_render(self):
        task_id = "translate-test-task"
        task_dir = Path(utils.task_dir(task_id))
        source_video = str(task_dir / "source.mp4")
        source_audio = str(task_dir / "source-audio.wav")
        Path(source_video).write_bytes(b"video")

        def fake_transcribe(audio_file, subtitle_file):
            Path(subtitle_file).write_text(
                "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n",
                encoding="utf-8",
            )

        def fake_render(source_video_path, audio_path, subtitle_path, output_file, params):
            Path(output_file).write_bytes(b"final-video")

        params = TranslateVideoParams(
            source_video_url="https://www.tiktok.com/@demo/video/123",
            target_language="vi-VN",
            voice_name="",
            bgm_type="",
            voice_enabled=False,
            source_audio_enabled=True,
        )

        with (
            patch.object(
                translate_video.source_video,
                "download_source_video_url",
                return_value=source_video,
            ),
            patch.object(
                translate_video.source_video,
                "validate_source_video",
                return_value={"duration": 3, "fps": 30, "width": 720, "height": 1280},
            ),
            patch.object(
                translate_video.source_video,
                "extract_audio",
                return_value=source_audio,
            ),
            patch.object(translate_video.subtitle, "create", side_effect=fake_transcribe),
            patch.object(
                translate_video.llm,
                "translate_segments",
                return_value=["Xin chào"],
            ),
            patch.object(translate_video, "build_synced_dub_audio") as build_synced_audio,
            patch.object(translate_video, "build_continuous_dub_audio") as build_continuous_audio,
            patch.object(translate_video.voice, "tts") as tts,
            patch.object(translate_video.voice, "create_subtitle") as create_subtitle,
            patch.object(
                translate_video.video,
                "render_existing_video",
                side_effect=fake_render,
            ) as render_existing_video,
        ):
            result = translate_video.start(task_id=task_id, params=params)

        self.assertEqual(result["audio_file"], "")
        build_synced_audio.assert_not_called()
        build_continuous_audio.assert_not_called()
        tts.assert_not_called()
        create_subtitle.assert_not_called()
        render_existing_video.assert_called_once()
        render_params = render_existing_video.call_args.kwargs["params"]
        self.assertFalse(render_params.voice_enabled)
        self.assertTrue(render_params.source_audio_enabled)

    def test_start_translates_source_url_and_renders_final_video(self):
        task_id = "translate-test-task"
        task_dir = Path(utils.task_dir(task_id))
        source_video = str(task_dir / "source.mp4")
        source_audio = str(task_dir / "source-audio.wav")
        Path(source_video).write_bytes(b"video")

        def fake_transcribe(audio_file, subtitle_file):
            Path(subtitle_file).write_text(
                "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n"
                "2\n00:00:01,500 --> 00:00:03,000\nBye\n\n",
                encoding="utf-8",
            )

        def fake_tts(text, voice_name, voice_rate, voice_file, voice_volume=1.0):
            Path(voice_file).write_bytes(b"audio")
            return object()

        def fake_render(source_video_path, audio_path, subtitle_path, output_file, params):
            Path(output_file).write_bytes(b"final-video")

        params = TranslateVideoParams(
            source_video_url="https://www.tiktok.com/@demo/video/123",
            target_language="vi-VN",
            voice_name="vi-VN-HoaiMyNeural-Female",
            bgm_type="",
            dubbing_mode="natural",
        )

        with (
            patch.object(
                translate_video.source_video,
                "download_source_video_url",
                return_value=source_video,
            ) as download_url,
            patch.object(
                translate_video.source_video,
                "validate_source_video",
                return_value={"duration": 3, "fps": 30, "width": 720, "height": 1280},
            ),
            patch.object(
                translate_video.source_video,
                "extract_audio",
                return_value=source_audio,
            ) as extract_audio,
            patch.object(translate_video.subtitle, "create", side_effect=fake_transcribe),
            patch.object(
                translate_video.llm,
                "translate_segments",
                return_value=["Xin chào", "Tạm biệt"],
            ) as translate_segments,
            patch.object(translate_video.voice, "tts", side_effect=fake_tts) as tts,
            patch.object(translate_video.voice, "create_subtitle") as create_subtitle,
            patch.object(
                translate_video.video,
                "render_existing_video",
                side_effect=fake_render,
            ) as render_existing_video,
        ):
            result = translate_video.start(task_id=task_id, params=params)

        final_video = str(task_dir / "final-1.mp4")
        self.assertEqual(result["videos"], [final_video])
        self.assertEqual(result["script"], "Xin chào\nTạm biệt")
        self.assertTrue(os.path.exists(final_video))
        download_url.assert_called_once_with(task_id, params.source_video_url)
        extract_audio.assert_called_once_with(source_video, source_audio)
        translate_segments.assert_called_once_with(
            ["Hello", "Bye"],
            target_language="vi-VN",
            source_language="",
        )
        tts.assert_called_once()
        create_subtitle.assert_called_once()
        render_existing_video.assert_called_once()


if __name__ == "__main__":
    unittest.main()
