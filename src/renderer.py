import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    VideoClip,
    concatenate_videoclips,
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, MultiplyVolume
from moviepy.video.fx import FadeIn, FadeOut

from src.models import SceneScript
from src.scene_builder import build_scene_frame_generator

logger = logging.getLogger(__name__)

MOTION_SEQUENCE = ["zoom_in", "pan_right", "drift_up", "pan_left", "zoom_out"]


def render_scenes_to_video(
    scenes: List[SceneScript],
    voiceover_data: List[Tuple[Optional[Path], float]],
    output_path: Path,
    orientation: str = "16:9",
    bgm_path: Optional[Path] = None,
    bgm_volume: float = 0.12,
    motion_style: str = "dynamic_mix",
    watermark_text: str = "REALTY ASSISTANT EXCLUSIVE",
    show_progress_bar: bool = True,
    duration_mode: str = "dynamic",
    custom_scene_duration: Optional[float] = None,
    fps: int = 24,
) -> Dict[str, Any]:
    """Assembles animated visual scenes, voiceovers, and background music into an elite broadcast MP4.
    Guarantees zero voiceover overlap and pristine audio-visual synchronization.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    video_clips = []
    clips_to_close = []
    total_scenes = len(scenes)

    try:
        for idx, (scene, (vo_file, vo_dur)) in enumerate(zip(scenes, voiceover_data)):
            # Pacing calculation based on user settings
            if duration_mode == "custom" and custom_scene_duration and custom_scene_duration > 0:
                scene_duration = max(custom_scene_duration, (vo_dur + 0.3) if vo_dur else 3.0)
            elif duration_mode == "fast":
                scene_duration = max(vo_dur + 0.4, 3.2) if (vo_file and vo_dur > 0) else 3.2
            elif duration_mode == "relaxed":
                scene_duration = max(vo_dur + 1.2, 5.0) if (vo_file and vo_dur > 0) else 5.0
            else:  # dynamic
                scene_duration = max(vo_dur + 0.8, 4.0) if (vo_file and vo_dur > 0) else max(scene.duration, 4.0)

            # Motion style selection
            if motion_style == "zoom_in":
                motion_type = "zoom_in"
            elif motion_style == "pans_only":
                motion_type = "pan_right" if idx % 2 == 0 else "pan_left"
            elif motion_style == "gentle_drift":
                motion_type = "drift_up"
            else:  # dynamic_mix
                motion_type = MOTION_SEQUENCE[idx % len(MOTION_SEQUENCE)]

            # Contextual luxury badges
            if scene.scene_type == "intro":
                badge_text = "PREMIUM RESIDENCE"
            elif scene.scene_type == "cta":
                badge_text = "SCHEDULE PRIVATE TOUR"
            else:
                badge_text = f"HIGHLIGHT {idx} OF {total_scenes - 2}"

            # Visual frame generator
            make_frame, w, h = build_scene_frame_generator(
                image_path=scene.image_path,
                badge_text=badge_text,
                headline=scene.headline,
                subtext=scene.subtext,
                duration=scene_duration,
                orientation=orientation,
                motion_type=motion_type,
                watermark_text=watermark_text,
                show_progress_bar=show_progress_bar,
            )

            v_clip = VideoClip(make_frame, duration=scene_duration)
            v_clip = v_clip.with_effects([FadeIn(0.2), FadeOut(0.2)])
            clips_to_close.append(v_clip)

            # Attach voiceover directly to this specific scene clip
            if vo_file and vo_file.exists():
                vo_clip = AudioFileClip(str(vo_file)).with_start(0.25)
                clips_to_close.append(vo_clip)
                v_clip = v_clip.with_audio(vo_clip)

            video_clips.append(v_clip)

        # Concatenate scenes sequentially along with their attached narration audio
        narrated_video = concatenate_videoclips(video_clips)
        total_duration = narrated_video.duration

        # Background music mixing with subtle ducking
        final_video = narrated_video
        if bgm_path and Path(bgm_path).exists() and bgm_volume > 0.0:
            try:
                bgm_raw = AudioFileClip(str(bgm_path))
                clips_to_close.append(bgm_raw)

                # Loop or trim BGM to match exact video duration
                if bgm_raw.duration < total_duration:
                    from moviepy.audio.fx import AudioLoop
                    bgm_track = bgm_raw.with_effects([AudioLoop(duration=total_duration)])
                else:
                    bgm_track = bgm_raw.subclipped(0, total_duration)

                bgm_track = bgm_track.with_effects([
                    MultiplyVolume(bgm_volume),
                    AudioFadeIn(0.8),
                    AudioFadeOut(2.0),
                ])
                clips_to_close.append(bgm_track)

                # Composite narration audio with subtle background music
                if narrated_video.audio is not None:
                    final_audio = CompositeAudioClip([bgm_track, narrated_video.audio])
                else:
                    final_audio = bgm_track

                clips_to_close.append(final_audio)
                final_video = narrated_video.with_audio(final_audio)

            except Exception as e:
                logger.warning("BGM mixing encountered issue (%s). Proceeding with voiceover audio.", e)

        # Write final video with H.264 + AAC
        temp_audio = str(output_path.parent / f"temp_{output_path.stem}_audio.m4a")
        final_video.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            temp_audiofile=temp_audio,
            remove_temp=True,
            logger=None,
        )

        filesize_mb = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0.0

        return {
            "success": True,
            "output_path": str(output_path),
            "duration": round(total_duration, 2),
            "resolution": f"{w}x{h}",
            "orientation": orientation,
            "scenes_count": len(scenes),
            "filesize_mb": round(filesize_mb, 2),
        }

    finally:
        # Close all open file handles
        for clip in clips_to_close:
            try:
                clip.close()
            except Exception:
                pass
