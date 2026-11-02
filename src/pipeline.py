import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.models import PropertyInput, VideoScript
from src.renderer import render_scenes_to_video
from src.script_generator import create_script
from src.tts import generate_scene_voiceover

logger = logging.getLogger(__name__)


def generate_property_video(
    prop: PropertyInput,
    output_dir: Optional[Path] = None,
    output_filename: Optional[str] = None,
    bgm_path: Optional[Path] = None,
    api_key: Optional[str] = None,
    custom_script: Optional[VideoScript] = None,
    status_callback: Optional[Callable[[str, float], None]] = None,
) -> Dict[str, Any]:
    """Complete end-to-end orchestration pipeline for creating AI property promo videos.
    Safely handles edge cases like missing images, API quotas, or audio fallbacks.
    """
    def update_status(msg: str, progress: float):
        if status_callback:
            try:
                status_callback(msg, progress)
            except Exception:
                pass
        logger.info("[%.0f%%] %s", progress * 100, msg)

    # 1. Output directory setup
    out_dir = Path(output_dir) if output_dir else Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Derive clean output path
    if output_filename:
        target_p = Path(output_filename)
        if target_p.parent != Path("."):
            final_video_path = target_p
            out_dir = target_p.parent
        else:
            final_video_path = out_dir / target_p.name
    else:
        sanitized_name = re.sub(r"[^\w\-_]", "_", prop.name.lower())[:35].strip("_")
        aspect_tag = "vert" if prop.orientation == "9:16" else ("sq" if prop.orientation == "1:1" else "horiz")
        final_video_path = out_dir / f"{sanitized_name}_{prop.language}_{aspect_tag}.mp4"

    final_video_path.parent.mkdir(parents=True, exist_ok=True)
    temp_audio_dir = out_dir / "temp_audio"
    temp_audio_dir.mkdir(parents=True, exist_ok=True)

    update_status("Validating property inputs and resolving visual assets...", 0.10)

    # 2. Validate images
    valid_images = prop.get_valid_images(base_dir=Path.cwd())
    if not valid_images:
        logger.warning("No valid local images found. Pipeline will render luxury gradient slides.")

    update_status("Generating promotional script and scene captions...", 0.25)

    # 3. Generate script (or use custom edited script from web studio)
    if custom_script:
        script = custom_script
    else:
        script = create_script(prop, valid_images, api_key=api_key)

    update_status("Synthesizing neural voiceover narration...", 0.45)

    # 4. Generate scene voiceovers with custom voice and tempo
    voiceover_data: List[Tuple[Optional[Path], float]] = []
    temp_files_to_clean: List[Path] = []

    for i, scene in enumerate(script.scenes):
        scene_audio_path = temp_audio_dir / f"scene_{i}_{prop.language}.mp3"
        vo_path, vo_duration = generate_scene_voiceover(
            text=scene.voiceover_text,
            output_path=scene_audio_path,
            language=prop.language,
            specific_voice=prop.voice_id,
            speech_rate=prop.speech_rate,
        )
        voiceover_data.append((vo_path, vo_duration))
        if vo_path and vo_path.exists():
            temp_files_to_clean.append(vo_path)

    update_status("Rendering animated scenes, Ken Burns camera motion, and mixing audio...", 0.70)

    # 5. Locate background music
    if bgm_path and Path(bgm_path).exists():
        resolved_bgm = Path(bgm_path)
    elif Path("assets/bgm.mp3").exists():
        resolved_bgm = Path("assets/bgm.mp3")
    elif Path("assets/bgm.wav").exists():
        resolved_bgm = Path("assets/bgm.wav")
    else:
        resolved_bgm = None

    # 6. Render final MP4 video
    render_result = render_scenes_to_video(
        scenes=script.scenes,
        voiceover_data=voiceover_data,
        output_path=final_video_path,
        orientation=prop.orientation,
        bgm_path=resolved_bgm,
        bgm_volume=prop.bgm_volume,
        motion_style=prop.motion_style,
        watermark_text=prop.watermark_text,
        show_progress_bar=prop.show_progress_bar,
        duration_mode=prop.duration_mode,
        custom_scene_duration=prop.custom_scene_duration,
        fps=24,
    )

    update_status("Cleaning up temporary audio buffers...", 0.95)

    # 7. Cleanup temp audio files
    for tmp in temp_files_to_clean:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass

    try:
        if temp_audio_dir.exists() and not any(temp_audio_dir.iterdir()):
            temp_audio_dir.rmdir()
    except Exception:
        pass

    update_status("Video generation complete!", 1.0)

    render_result["script_source"] = script.source
    render_result["script"] = script.model_dump()
    return render_result
