import os


FONT_EXTENSIONS = (".ttf", ".ttc", ".otf")
DEFAULT_FONT_NAME = "MicrosoftYaHeiBold.ttc"
DEFAULT_VIETNAMESE_FONT_NAME = "BeVietnamPro-Bold.ttf"
VIETNAMESE_RECOMMENDED_FONTS = {
    "BeVietnamPro-Bold.ttf": "Khuyến nghị tiếng Việt",
    "BeVietnamPro-Regular.ttf": "Khuyến nghị tiếng Việt",
    "NotoSans-VF.ttf": "Đa ngôn ngữ",
}


def _is_vietnamese_locale(value: str | None) -> bool:
    return (value or "").strip().lower().startswith("vi")


def list_font_names(font_dir: str) -> list[str]:
    font_names = []
    for root, _, files in os.walk(font_dir):
        for filename in files:
            if filename.lower().endswith(FONT_EXTENSIONS):
                font_names.append(filename)

    font_names = sorted(set(font_names))
    recommended_rank = {
        font_name: index for index, font_name in enumerate(VIETNAMESE_RECOMMENDED_FONTS)
    }
    return sorted(
        font_names,
        key=lambda font_name: (
            0 if font_name in recommended_rank else 1,
            recommended_rank.get(font_name, len(recommended_rank)),
            font_name.lower(),
        ),
    )


def format_font_label(font_name: str) -> str:
    recommendation = VIETNAMESE_RECOMMENDED_FONTS.get(font_name)
    if recommendation:
        return f"{font_name} ({recommendation})"
    return font_name


def select_default_font_name(
    font_names: list[str],
    saved_font_name: str | None = "",
    ui_language: str | None = "",
    video_language: str | None = "",
) -> str:
    if saved_font_name in font_names:
        return saved_font_name

    if (
        _is_vietnamese_locale(ui_language) or _is_vietnamese_locale(video_language)
    ) and DEFAULT_VIETNAMESE_FONT_NAME in font_names:
        return DEFAULT_VIETNAMESE_FONT_NAME

    if DEFAULT_FONT_NAME in font_names:
        return DEFAULT_FONT_NAME

    return font_names[0] if font_names else ""
