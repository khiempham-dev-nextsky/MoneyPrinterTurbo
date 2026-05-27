import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.schema import VideoAspect, VideoConcatMode, VideoTransitionMode
from webui.studio.state import (
    StudioCreateState,
    build_video_params,
    deserialize_create_state,
    serialize_create_state,
)


class TestStudioState(unittest.TestCase):
    def test_build_video_params_maps_create_state_to_backend_schema(self):
        state = StudioCreateState(
            video_subject="Ngu ngon hon",
            video_script="Hay ngu dung gio.",
            video_terms="good sleep, sleep routine",
            video_language="vi-VN",
            video_source="tiktok",
            video_aspect=VideoAspect.portrait.value,
            video_concat_mode=VideoConcatMode.sequential.value,
            video_transition_mode=VideoTransitionMode.fade_in.value,
            video_clip_duration=7,
            video_count=2,
            voice_name="vi-VN-HoaiMyNeural-Female",
            voice_volume=1.2,
            voice_rate=1.1,
            bgm_type="random",
            bgm_volume=0.3,
            subtitle_enabled=True,
            subtitle_position="custom",
            custom_position=72.0,
            font_name="BeVietnamPro-Bold.ttf",
            text_fore_color="#FFFFFF",
            font_size=68,
            stroke_color="#111111",
            stroke_width=2.0,
        )

        params = build_video_params(state)

        self.assertEqual(params.video_subject, "Ngu ngon hon")
        self.assertEqual(params.video_script, "Hay ngu dung gio.")
        self.assertEqual(params.video_terms, "good sleep, sleep routine")
        self.assertEqual(params.video_language, "vi-VN")
        self.assertEqual(params.video_source, "tiktok")
        self.assertEqual(params.video_aspect, VideoAspect.portrait.value)
        self.assertEqual(params.video_concat_mode, VideoConcatMode.sequential.value)
        self.assertEqual(params.video_transition_mode, VideoTransitionMode.fade_in.value)
        self.assertEqual(params.video_clip_duration, 7)
        self.assertEqual(params.video_count, 2)
        self.assertEqual(params.voice_name, "vi-VN-HoaiMyNeural-Female")
        self.assertEqual(params.voice_volume, 1.2)
        self.assertEqual(params.voice_rate, 1.1)
        self.assertEqual(params.bgm_type, "random")
        self.assertEqual(params.bgm_volume, 0.3)
        self.assertTrue(params.subtitle_enabled)
        self.assertEqual(params.subtitle_position, "custom")
        self.assertEqual(params.custom_position, 72.0)
        self.assertEqual(params.font_name, "BeVietnamPro-Bold.ttf")
        self.assertEqual(params.font_size, 68)
        self.assertEqual(params.stroke_width, 2.0)

    def test_build_video_params_reuses_local_material_records(self):
        state = StudioCreateState(
            video_subject="Local video",
            video_source="local",
            local_video_materials=[
                {"provider": "local", "url": "/tmp/a.mp4", "duration": 5},
                {"provider": "local", "url": "", "duration": 0},
            ],
        )

        params = build_video_params(state)

        self.assertEqual(len(params.video_materials), 1)
        self.assertEqual(params.video_materials[0].provider, "local")
        self.assertEqual(params.video_materials[0].url, "/tmp/a.mp4")
        self.assertEqual(params.video_materials[0].duration, 5)

    def test_create_state_round_trip_preserves_full_settings(self):
        state = StudioCreateState(
            video_subject="Morning focus",
            video_script="Plan your day before opening email.",
            video_terms="productive work, focused work",
            video_language="en-US",
            local_video_materials=[
                {"provider": "local", "url": "/tmp/focus.mp4", "duration": 8}
            ],
            uploaded_audio_path="/tmp/uploaded.mp3",
            custom_audio_file="/tmp/custom.mp3",
            video_source="local",
            video_aspect="16:9",
            video_concat_mode="sequential",
            video_transition_mode="FadeIn",
            video_clip_duration=8,
            video_count=3,
            n_threads=4,
            voice_name="en-US-JennyNeural-Female",
            voice_volume=1.5,
            voice_rate=1.2,
            bgm_type="custom",
            bgm_file="/tmp/bgm.mp3",
            bgm_volume=0.4,
            subtitle_enabled=False,
            subtitle_position="custom",
            custom_position=64.0,
            font_name="Inter-Bold.ttf",
            text_fore_color="#F8FAFC",
            text_background_color=False,
            font_size=74,
            stroke_color="#020617",
            stroke_width=3.5,
        )

        restored = deserialize_create_state(serialize_create_state(state))

        self.assertEqual(restored, state)


if __name__ == "__main__":
    unittest.main()
