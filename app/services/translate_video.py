import os
import subprocess
from pathlib import Path

from loguru import logger

from app.models import const
from app.models.schema import TranslateVideoParams
from app.services import llm, source_video, state as sm, subtitle, video, voice
from app.utils import utils

CONTINUOUS_SEGMENT_PAUSE_SECONDS = 0.18


def _task_dir(task_id: str) -> Path:
    task_dir = Path(utils.task_dir(task_id))
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def _params_to_dict(params: TranslateVideoParams) -> dict:
    if hasattr(params, "model_dump"):
        return params.model_dump()
    return params.dict()


def _subtitle_texts(source_items) -> list[str]:
    return [str(item[2] or "").strip() for item in source_items if str(item[2] or "").strip()]


def _manual_translated_segments(translated_script: str, expected_count: int) -> list[str]:
    lines = [line.strip() for line in str(translated_script or "").splitlines() if line.strip()]
    if len(lines) == expected_count:
        return lines

    punctuation_lines = utils.split_string_by_punctuations(translated_script)
    if len(punctuation_lines) == expected_count:
        return punctuation_lines

    return lines or punctuation_lines


def write_translated_srt(source_items, translated_segments: list[str], output_file: str) -> str:
    if len(source_items) != len(translated_segments):
        raise ValueError("translated subtitle segment count must match source subtitles")

    lines = []
    for idx, item in enumerate(source_items, start=1):
        times = item[1]
        text = translated_segments[idx - 1]
        lines.append(f"{idx}\n{times}\n{text}")

    Path(output_file).write_text("\n\n".join(lines) + "\n\n", encoding="utf-8")
    return output_file


def _format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds) * 1000)))
    hours, remainder = divmod(total_ms, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_translated_srt_from_timeline(scheduled_segments: list[dict], output_file: str) -> str:
    lines = []
    for idx, segment in enumerate(scheduled_segments, start=1):
        start = _format_srt_timestamp(segment["start"])
        end = _format_srt_timestamp(segment["end"])
        text = str(segment.get("text") or "").strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}")

    Path(output_file).write_text("\n\n".join(lines) + "\n\n", encoding="utf-8")
    return output_file


def _parse_srt_timestamp(value: str) -> float:
    hours, minutes, seconds = value.strip().replace(",", ".").split(":")
    return (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)


def _parse_srt_timerange(value: str) -> tuple[float, float]:
    start, end = str(value).split("-->", 1)
    return _parse_srt_timestamp(start), _parse_srt_timestamp(end)


def _run_ffmpeg(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        error_message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(error_message or "ffmpeg command failed")


def _atempo_filter(speed: float) -> str:
    speed = max(float(speed), 0.5)
    factors = []
    remaining = speed
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return ",".join(f"atempo={factor:.6g}" for factor in factors)


def _speed_adjust_audio(input_file: str, output_file: str, speed: float) -> str:
    command = [
        video.get_ffmpeg_binary(),
        "-y",
        "-i",
        input_file,
        "-filter:a",
        _atempo_filter(speed),
        "-vn",
        output_file,
    ]
    _run_ffmpeg(command)
    return output_file


def _mix_synced_segments(
    segment_inputs: list[tuple[int, str]],
    output_file: str,
    source_duration: float,
) -> str:
    if not segment_inputs:
        raise ValueError("no translated audio segments to mix")

    command = [
        video.get_ffmpeg_binary(),
        "-y",
        "-f",
        "lavfi",
        "-t",
        f"{source_duration:.3f}",
        "-i",
        "anullsrc=channel_layout=mono:sample_rate=44100",
    ]
    for _, segment_file in segment_inputs:
        command.extend(["-i", segment_file])

    delay_filters = []
    delayed_labels = []
    for input_index, (delay_ms, _) in enumerate(segment_inputs, start=1):
        label = f"a{input_index}"
        delay_filters.append(f"[{input_index}:a]adelay={delay_ms}:all=1[{label}]")
        delayed_labels.append(f"[{label}]")

    mix_filter = (
        f"[0:a]{''.join(delayed_labels)}"
        f"amix=inputs={len(segment_inputs) + 1}:duration=first:dropout_transition=0[aout]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join([*delay_filters, mix_filter]),
            "-map",
            "[aout]",
            "-ac",
            "1",
            "-ar",
            "44100",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            output_file,
        ]
    )
    _run_ffmpeg(command)
    return output_file


def build_synced_dub_audio(
    source_items,
    translated_segments: list[str],
    params: TranslateVideoParams,
    task_dir: Path,
    source_duration: float,
) -> str:
    if len(source_items) != len(translated_segments):
        raise ValueError("translated segment count must match source subtitles")

    segment_inputs = []
    for idx, item in enumerate(source_items, start=1):
        translated_text = str(translated_segments[idx - 1] or "").strip()
        if not translated_text:
            continue

        start_time, end_time = _parse_srt_timerange(item[1])
        slot_duration = max(end_time - start_time, 0.1)
        segment_file = str(task_dir / f"segment-{idx:03d}.mp3")
        sub_maker = voice.tts(
            text=translated_text,
            voice_name=voice.parse_voice_name(params.voice_name),
            voice_rate=params.voice_rate,
            voice_file=segment_file,
            voice_volume=params.voice_volume,
        )
        if sub_maker is None:
            raise ValueError(f"failed to generate TTS for translated segment {idx}")

        segment_duration = float(voice.get_audio_duration(segment_file) or 0)
        segment_input = segment_file
        if segment_duration > slot_duration:
            speed = segment_duration / slot_duration
            segment_input = _speed_adjust_audio(
                input_file=segment_file,
                output_file=str(task_dir / f"segment-{idx:03d}-sync.mp3"),
                speed=speed,
            )

        segment_inputs.append((int(start_time * 1000), segment_input))

    output_file = str(task_dir / "translated-audio.mp3")
    return _mix_synced_segments(
        segment_inputs=segment_inputs,
        output_file=output_file,
        source_duration=source_duration,
    )


def build_continuous_dub_audio(
    source_items,
    translated_segments: list[str],
    params: TranslateVideoParams,
    task_dir: Path,
    source_duration: float,
) -> tuple[str, list[dict]]:
    if len(source_items) != len(translated_segments):
        raise ValueError("translated segment count must match source subtitles")

    segment_inputs = []
    scheduled_segments = []
    previous_end = None
    for idx, item in enumerate(source_items, start=1):
        translated_text = str(translated_segments[idx - 1] or "").strip()
        if not translated_text:
            continue

        original_start, original_end = _parse_srt_timerange(item[1])
        slot_duration = max(original_end - original_start, 0.1)
        segment_file = str(task_dir / f"segment-{idx:03d}.mp3")
        sub_maker = voice.tts(
            text=translated_text,
            voice_name=voice.parse_voice_name(params.voice_name),
            voice_rate=params.voice_rate,
            voice_file=segment_file,
            voice_volume=params.voice_volume,
        )
        if sub_maker is None:
            raise ValueError(f"failed to generate TTS for translated segment {idx}")

        segment_duration = float(voice.get_audio_duration(segment_file) or 0)
        effective_duration = segment_duration if segment_duration > 0 else slot_duration
        segment_input = segment_file
        if segment_duration > slot_duration:
            speed = segment_duration / slot_duration
            segment_input = _speed_adjust_audio(
                input_file=segment_file,
                output_file=str(task_dir / f"segment-{idx:03d}-sync.mp3"),
                speed=speed,
            )
            effective_duration = slot_duration

        if previous_end is None:
            scheduled_start = original_start
        else:
            scheduled_start = previous_end + CONTINUOUS_SEGMENT_PAUSE_SECONDS

        scheduled_end = scheduled_start + max(effective_duration, 0.05)
        if source_duration > 0 and scheduled_end > source_duration:
            scheduled_end = source_duration
        if scheduled_end <= scheduled_start:
            scheduled_end = scheduled_start + 0.05

        segment_inputs.append((int(round(scheduled_start * 1000)), segment_input))
        scheduled_segments.append(
            {
                "start": scheduled_start,
                "end": scheduled_end,
                "text": translated_text,
            }
        )
        previous_end = scheduled_end

    output_file = str(task_dir / "translated-audio.mp3")
    audio_path = _mix_synced_segments(
        segment_inputs=segment_inputs,
        output_file=output_file,
        source_duration=source_duration,
    )
    return audio_path, scheduled_segments


def _save_project_metadata(
    task_dir: Path,
    translated_script: str,
    params: TranslateVideoParams,
) -> None:
    payload = {
        "script": translated_script,
        "search_terms": [],
        "params": _params_to_dict(params),
        "task_type": "translate",
    }
    (task_dir / "script.json").write_text(utils.to_json(payload), encoding="utf-8")


def _resolve_source_video(task_id: str, params: TranslateVideoParams) -> str:
    source_path = str(params.source_video_path or "").strip()
    if source_path:
        source_video.validate_source_video(source_path)
        return source_path

    source_url = str(params.source_video_url or "").strip()
    if not source_url:
        raise ValueError("source video path or url is required")
    return source_video.download_source_video_url(task_id, source_url)


def _generate_translated_subtitle_from_tts(
    sub_maker,
    translated_script: str,
    fallback_subtitle_path: str,
    output_subtitle_path: str,
) -> str:
    voice.create_subtitle(
        sub_maker=sub_maker,
        text=translated_script,
        subtitle_file=output_subtitle_path,
    )
    if os.path.exists(output_subtitle_path) and subtitle.file_to_subtitles(output_subtitle_path):
        return output_subtitle_path
    return fallback_subtitle_path


def start(task_id: str, params: TranslateVideoParams):
    logger.info(f"start translate video task: {task_id}")
    task_dir = _task_dir(task_id)
    sm.state.update_task(
        task_id,
        state=const.TASK_STATE_PROCESSING,
        progress=5,
        params=_params_to_dict(params),
        task_type="translate",
    )

    try:
        source_path = _resolve_source_video(task_id, params)
        source_info = source_video.validate_source_video(source_path)
        source_duration = float(source_info.get("duration") or 0)
        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=15)

        source_audio_path = str(task_dir / "source-audio.wav")
        source_video.extract_audio(source_path, source_audio_path)
        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=25)

        source_subtitle_path = str(task_dir / "source.srt")
        subtitle.create(audio_file=source_audio_path, subtitle_file=source_subtitle_path)
        source_items = subtitle.file_to_subtitles(source_subtitle_path)
        if not source_items:
            raise ValueError("failed to transcribe source video audio")
        source_texts = _subtitle_texts(source_items)
        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=45)

        if str(params.translated_script or "").strip():
            translated_segments = _manual_translated_segments(
                params.translated_script,
                expected_count=len(source_texts),
            )
            if len(translated_segments) != len(source_texts):
                raise ValueError(
                    "manual translated script must match source subtitle segment count"
                )
        else:
            translated_segments = llm.translate_segments(
                source_texts,
                target_language=params.target_language,
                source_language=params.source_language or "",
            )

        translated_script = "\n".join(translated_segments)
        fallback_subtitle_path = str(task_dir / "translated-source-timing.srt")
        write_translated_srt(source_items, translated_segments, fallback_subtitle_path)
        _save_project_metadata(task_dir, translated_script, params)
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_PROCESSING,
            progress=60,
            script=translated_script,
        )

        subtitle_path = ""
        audio_path = ""
        if not params.voice_enabled:
            if params.subtitle_enabled:
                subtitle_path = fallback_subtitle_path
        elif params.dubbing_mode == "continuous":
            audio_path, scheduled_segments = build_continuous_dub_audio(
                source_items=source_items,
                translated_segments=translated_segments,
                params=params,
                task_dir=task_dir,
                source_duration=source_duration,
            )
            if params.subtitle_enabled:
                subtitle_path = write_translated_srt_from_timeline(
                    scheduled_segments,
                    str(task_dir / "translated-continuous-timing.srt"),
                )
        elif params.dubbing_mode == "sync":
            audio_path = build_synced_dub_audio(
                source_items=source_items,
                translated_segments=translated_segments,
                params=params,
                task_dir=task_dir,
                source_duration=source_duration,
            )
            if params.subtitle_enabled:
                subtitle_path = fallback_subtitle_path
        else:
            audio_path = str(task_dir / "translated-audio.mp3")
            sub_maker = voice.tts(
                text=translated_script,
                voice_name=voice.parse_voice_name(params.voice_name),
                voice_rate=params.voice_rate,
                voice_file=audio_path,
                voice_volume=params.voice_volume,
            )
            if sub_maker is None:
                raise ValueError("failed to generate translated TTS audio")

            if params.subtitle_enabled:
                subtitle_path = _generate_translated_subtitle_from_tts(
                    sub_maker=sub_maker,
                    translated_script=translated_script,
                    fallback_subtitle_path=fallback_subtitle_path,
                    output_subtitle_path=str(task_dir / "translated.srt"),
                )

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=80)

        final_video_path = str(task_dir / "final-1.mp4")
        video.render_existing_video(
            source_video_path=source_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_file=final_video_path,
            params=params,
        )
        if not os.path.exists(final_video_path):
            raise ValueError("failed to render translated video")

        result = {
            "videos": [final_video_path],
            "source_video": source_path,
            "source_audio": source_audio_path,
            "source_subtitle": source_subtitle_path,
            "audio_file": audio_path,
            "subtitle_path": subtitle_path,
            "script": translated_script,
            "terms": [],
            "materials": [source_path],
            "task_type": "translate",
        }
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_COMPLETE,
            progress=100,
            **result,
        )
        return result
    except Exception as exc:
        logger.exception(exc)
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_FAILED,
            progress=100,
            error=str(exc),
            task_type="translate",
        )
        raise
