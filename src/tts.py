import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from moviepy import AudioFileClip

logger = logging.getLogger(__name__)

# Complete catalog of studio-grade neural voices
AVAILABLE_VOICES: Dict[str, Dict[str, str]] = {
    # Indian English Voices
    "en-IN-Neerja": {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja (Indian English - Professional Female)",
        "language": "en",
        "gender": "female",
    },
    "en-IN-Prabhat": {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat (Indian English - Confident Male)",
        "language": "en",
        "gender": "male",
    },
    # Hindi Voices
    "hi-IN-Swara": {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (Hindi - Expressive Female)",
        "language": "hi",
        "gender": "female",
    },
    "hi-IN-Madhur": {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur (Hindi - Authoritative Male)",
        "language": "hi",
        "gender": "male",
    },
    # International Voices
    "en-US-Jenny": {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US English - Warm & Modern Female)",
        "language": "en",
        "gender": "female",
    },
    "en-US-Guy": {
        "id": "en-US-GuyNeural",
        "name": "Guy (US English - Commercial Male)",
        "language": "en",
        "gender": "male",
    },
    "en-GB-Sonia": {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (British English - Luxury / Sophisticated Female)",
        "language": "en",
        "gender": "female",
    },
}

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "en-male": "en-IN-PrabhatNeural",
    "hi": "hi-IN-SwaraNeural",
    "hi-male": "hi-IN-MadhurNeural",
}


def _normalize_speech_text(text: str, language: str) -> str:
    """Cleans symbols and expands real estate abbreviations for fluid, natural speech."""
    s = text.strip()
    if language == "hi":
        s = s.replace("₹", "रुपये ")
        s = s.replace("Cr", "करोड़")
        s = s.replace("sq.ft.", "स्क्वायर फीट")
        s = s.replace("BHK", "बी एच के")
    else:
        s = s.replace("₹", "Rupees ")
        s = s.replace("Cr", "Crore")
        s = s.replace("sq.ft.", "square feet")
        s = s.replace("BHK", "B H K")
    return s


async def _synthesize_edge_tts(text: str, voice: str, output_path: Path, rate: str = "+10%") -> None:
    """Invokes edge-tts to generate voiceover audio with commercial tempo."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(output_path))


def _synthesize_gtts(text: str, lang: str, output_path: Path) -> None:
    """Fallback TTS generator using Google Text-to-Speech."""
    from gtts import gTTS
    gtts_lang = "hi" if lang == "hi" else "en"
    tld = "co.in" if gtts_lang == "en" else "com"
    tts = gTTS(text=text, lang=gtts_lang, tld=tld, slow=False)
    tts.save(str(output_path))


def resolve_voice_id(language: str = "en", preferred_gender: str = "female", specific_voice: Optional[str] = None) -> str:
    """Resolves specific voice identifier from user selection or defaults."""
    if specific_voice:
        if specific_voice in AVAILABLE_VOICES:
            return AVAILABLE_VOICES[specific_voice]["id"]
        for v in AVAILABLE_VOICES.values():
            if v["id"] == specific_voice:
                return v["id"]

    voice_key = f"{language}-male" if preferred_gender == "male" else language
    return VOICE_MAP.get(voice_key, VOICE_MAP.get(language, "en-IN-NeerjaNeural"))


def generate_scene_voiceover(
    text: str,
    output_path: Path,
    language: str = "en",
    preferred_gender: str = "female",
    specific_voice: Optional[str] = None,
    speech_rate: str = "+10%",
) -> Tuple[Optional[Path], float]:
    """Generates voiceover audio for a scene with granular voice & pacing control.
    Tries edge-tts first; falls back to gTTS if unavailable.
    Returns (audio_path, duration_in_seconds).
    """
    clean_text = _normalize_speech_text(text, language)
    if not clean_text:
        return None, 3.5

    output_path.parent.mkdir(parents=True, exist_ok=True)
    voice = resolve_voice_id(language=language, preferred_gender=preferred_gender, specific_voice=specific_voice)

    # Attempt 1: edge-tts
    try:
        asyncio.run(_synthesize_edge_tts(clean_text, voice, output_path, rate=speech_rate))
        if output_path.exists() and output_path.stat().st_size > 0:
            with AudioFileClip(str(output_path)) as clip:
                duration = float(clip.duration)
            return output_path, duration
    except Exception as e:
        logger.warning("edge-tts synthesis failed (%s). Attempting gTTS fallback...", e)

    # Attempt 2: gTTS fallback
    try:
        _synthesize_gtts(clean_text, language, output_path)
        if output_path.exists() and output_path.stat().st_size > 0:
            with AudioFileClip(str(output_path)) as clip:
                duration = float(clip.duration)
            return output_path, duration
    except Exception as e2:
        logger.error("gTTS fallback also failed (%s). Proceeding with silent scene duration.", e2)

    return None, 4.0
