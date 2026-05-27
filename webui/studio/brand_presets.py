import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SubtitlePreset:
    name: str
    font_name: str
    font_size: int
    text_fore_color: str
    stroke_color: str
    stroke_width: float
    subtitle_position: str
    custom_position: float


def default_subtitle_presets() -> list[SubtitlePreset]:
    return [
        SubtitlePreset(
            name="Clean Vietnamese Shorts",
            font_name="BeVietnamPro-Bold.ttf",
            font_size=64,
            text_fore_color="#FFFFFF",
            stroke_color="#111111",
            stroke_width=1.8,
            subtitle_position="bottom",
            custom_position=70.0,
        ),
        SubtitlePreset(
            name="Bold Caption",
            font_name="BeVietnamPro-Bold.ttf",
            font_size=72,
            text_fore_color="#FFFFFF",
            stroke_color="#000000",
            stroke_width=2.4,
            subtitle_position="center",
            custom_position=50.0,
        ),
        SubtitlePreset(
            name="Minimal Lower Third",
            font_name="BeVietnamPro-Regular.ttf",
            font_size=52,
            text_fore_color="#F8FAFC",
            stroke_color="#0F172A",
            stroke_width=1.0,
            subtitle_position="bottom",
            custom_position=78.0,
        ),
    ]


def _preset_from_dict(record: dict) -> SubtitlePreset | None:
    required = {
        "name",
        "font_name",
        "font_size",
        "text_fore_color",
        "stroke_color",
        "stroke_width",
        "subtitle_position",
        "custom_position",
    }
    if not required.issubset(record):
        return None
    return SubtitlePreset(
        name=str(record["name"]),
        font_name=str(record["font_name"]),
        font_size=int(record["font_size"]),
        text_fore_color=str(record["text_fore_color"]),
        stroke_color=str(record["stroke_color"]),
        stroke_width=float(record["stroke_width"]),
        subtitle_position=str(record["subtitle_position"]),
        custom_position=float(record["custom_position"]),
    )


def load_subtitle_presets(path: str | Path) -> list[SubtitlePreset]:
    preset_path = Path(path)
    if not preset_path.exists():
        return default_subtitle_presets()
    try:
        payload = json.loads(preset_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_subtitle_presets()
    if not isinstance(payload, list):
        return default_subtitle_presets()

    presets = []
    for record in payload:
        if not isinstance(record, dict):
            continue
        preset = _preset_from_dict(record)
        if preset:
            presets.append(preset)
    return presets or default_subtitle_presets()


def save_subtitle_presets(path: str | Path, presets: Iterable[SubtitlePreset]) -> None:
    preset_path = Path(path)
    preset_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(preset) for preset in presets]
    preset_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_subtitle_preset(
    presets: Iterable[SubtitlePreset], name: str
) -> SubtitlePreset | None:
    for preset in presets:
        if preset.name == name:
            return preset
    return None

