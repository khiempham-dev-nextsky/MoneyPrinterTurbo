import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services import task as tm
from app.models.schema import MaterialInfo, VideoParams

resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")

class TestTaskService(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_get_video_materials_routes_tiktok_to_tiktok_service(self):
        task_id = "00000000-0000-0000-0000-000000000000"
        params = VideoParams(
            video_subject="skincare review",
            video_script="A creator reviews a skincare product.",
            video_source="tiktok",
            video_clip_duration=3,
            video_count=1,
            video_language="en-US",
        )

        with (
            patch(
                "app.services.task.tiktok.discover_and_download_videos",
                return_value=["/tmp/tiktok.mp4"],
            ) as discover,
            patch("app.services.task.material.download_videos") as download_videos,
        ):
            result = tm.get_video_materials(
                task_id=task_id,
                params=params,
                video_terms=[],
                audio_duration=8,
            )

        self.assertEqual(result, ["/tmp/tiktok.mp4"])
        download_videos.assert_not_called()
        discover.assert_called_once_with(
            task_id=task_id,
            video_subject="skincare review",
            video_script="A creator reviews a skincare product.",
            video_language="en-US",
            search_terms=[],
            audio_duration=8,
            max_clip_duration=3,
        )

    def test_start_generates_terms_for_tiktok_like_stock_sources(self):
        task_id = "00000000-0000-0000-0000-000000000001"
        params = VideoParams(
            video_subject="sleep health",
            video_script="Sleep early and avoid caffeine.",
            video_source="tiktok",
            video_clip_duration=3,
            video_count=1,
            voice_name="en-US-JennyNeural-Female",
            bgm_type="",
        )

        with (
            patch("app.services.task.llm.generate_terms", return_value=["sleep routine", "avoid caffeine"]) as generate_terms,
            patch("app.services.task.generate_audio", return_value=("/tmp/audio.mp3", 5, None)),
            patch("app.services.task.generate_subtitle", return_value=""),
            patch("app.services.task.tiktok.discover_and_download_videos", return_value=["/tmp/tiktok.mp4"]) as discover,
            patch("app.services.task.generate_final_videos", return_value=(["/tmp/final.mp4"], ["/tmp/combined.mp4"])),
        ):
            result = tm.start(task_id=task_id, params=params)

        self.assertEqual(result["terms"], ["sleep routine", "avoid caffeine"])
        generate_terms.assert_called_once()
        discover.assert_called_once_with(
            task_id=task_id,
            video_subject="sleep health",
            video_script="Sleep early and avoid caffeine.",
            video_language="",
            search_terms=["sleep routine", "avoid caffeine"],
            audio_duration=5,
            max_clip_duration=3,
        )

    def test_get_video_materials_routes_stock_sources_to_material_service(self):
        params = VideoParams(
            video_subject="cat",
            video_script="A cat plays.",
            video_source="pexels",
            video_clip_duration=3,
            video_count=1,
        )

        with patch(
            "app.services.task.material.download_videos", return_value=["/tmp/pexels.mp4"]
        ) as download_videos:
            result = tm.get_video_materials(
                task_id="task-id",
                params=params,
                video_terms=["cat"],
                audio_duration=5,
            )

        self.assertEqual(result, ["/tmp/pexels.mp4"])
        download_videos.assert_called_once()

    def test_get_video_materials_rejects_unsupported_source(self):
        params = VideoParams(
            video_subject="cat",
            video_script="A cat plays.",
            video_source="douyin",
            video_clip_duration=3,
            video_count=1,
        )

        with self.assertRaises(ValueError) as cm:
            tm.get_video_materials(
                task_id="task-id",
                params=params,
                video_terms=[],
                audio_duration=5,
            )

        self.assertIn("unsupported video_source: douyin", str(cm.exception))
    
    def test_task_local_materials(self):
        task_id = "00000000-0000-0000-0000-000000000000"
        video_materials=[]
        for i in range(1, 4):
            video_materials.append(MaterialInfo(
                provider="local",
                url=os.path.join(resources_dir, f"{i}.png"),
                duration=0
            ))

        params = VideoParams(
            video_subject="金钱的作用",
            video_script="金钱不仅是交换媒介，更是社会资源的分配工具。它能满足基本生存需求，如食物和住房，也能提供教育、医疗等提升生活品质的机会。拥有足够的金钱意味着更多选择权，比如职业自由或创业可能。但金钱的作用也有边界，它无法直接购买幸福、健康或真诚的人际关系。过度追逐财富可能导致价值观扭曲，忽视精神层面的需求。理想的状态是理性看待金钱，将其作为实现目标的工具而非终极目的。",
            video_terms="money importance, wealth and society, financial freedom, money and happiness, role of money",
            video_aspect="9:16",
            video_concat_mode="random",
            video_transition_mode="None",
            video_clip_duration=3,
            video_count=1,
            video_source="local",
            video_materials=video_materials,
            video_language="",
            voice_name="zh-CN-XiaoxiaoNeural-Female",
            voice_volume=1.0,
            voice_rate=1.0,
            bgm_type="random",
            bgm_file="",
            bgm_volume=0.2,
            subtitle_enabled=True,
            subtitle_position="bottom",
            custom_position=70.0,
            font_name="MicrosoftYaHeiBold.ttc",
            text_fore_color="#FFFFFF",
            text_background_color=True,
            font_size=60,
            stroke_color="#000000",
            stroke_width=1.5,
            n_threads=2,
            paragraph_number=1
        )
        result = tm.start(task_id=task_id, params=params)
        print(result)
    

if __name__ == "__main__":
    unittest.main()
