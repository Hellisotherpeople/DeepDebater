"""Text-to-speech utilities."""

from __future__ import annotations

import os
import re

from deep_debater.config import DebateConfig


def strip_html(html: str) -> str:
    """Strip HTML tags and entities, collapse whitespace."""
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"&[a-zA-Z0-9#]+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def generate_speech(
    config: DebateConfig,
    text: str,
    filename: str,
    voice: str | None = None,
) -> str:
    """Generate TTS audio, with automatic truncation fallback.

    Returns the path to the saved audio file.
    """
    if not config.enable_tts:
        return ""

    from openai import OpenAI

    client = OpenAI(api_key=config.openai_api_key)
    voice = voice or config.affirmative_voice
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    try:
        _tts_to_file(client, config.voice_model, voice, text, filename)
    except Exception as e:
        if "string_too_long" in str(e) or "400" in str(e):
            truncated = text[: int(len(text) * 0.75)]
            _tts_to_file(client, config.voice_model, voice, truncated, filename)
        else:
            raise
    return filename


def _tts_to_file(client, model: str, voice: str, text: str, filename: str):
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        instructions="Speak clearly.",
    ) as response:
        response.stream_to_file(filename)


def generate_cross_ex_audio(
    config: DebateConfig,
    pairs: list[dict],
    output_dir: str,
    q_voice: str,
    a_voice: str,
    q_key: str = "negative_question",
    a_key: str = "affirmative_response",
) -> str:
    """Generate and concatenate cross-examination audio.

    Returns the path to the combined audio file.
    """
    if not config.enable_tts:
        return ""

    from pydub import AudioSegment

    os.makedirs(output_dir, exist_ok=True)
    segments = []

    for i, pair in enumerate(pairs, 1):
        q_path = os.path.join(output_dir, f"q_{i}.mp3")
        a_path = os.path.join(output_dir, f"a_{i}.mp3")
        generate_speech(config, pair[q_key], q_path, voice=q_voice)
        generate_speech(config, pair[a_key], a_path, voice=a_voice)
        segments.append(AudioSegment.from_file(q_path))
        segments.append(AudioSegment.from_file(a_path))

    if not segments:
        return ""

    combined = segments[0]
    for seg in segments[1:]:
        combined += seg

    combined_path = os.path.join(output_dir, "combined.mp3")
    combined.export(combined_path, format="mp3")
    return combined_path
