from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class PropertyInput(BaseModel):
    """Input representation of a property listing to generate video for."""
    name: str = Field(..., min_length=2, description="Property title/project name")
    location: str = Field(default="Prime Location", description="Property location/sector/city")
    price: str = Field(default="Price On Request", description="Listing price or price range")
    property_type: str = Field(default="Premium Residential Property", description="e.g. 3 BHK, Villa, Penthouse")
    features: List[str] = Field(
        default_factory=lambda: ["Modern architectural design", "Prime connected location", "Luxury lifestyle amenities"],
        description="Key property highlights and amenities"
    )
    contact_cta: str = Field(default="Contact our sales team for bookings and site visits.", description="CTA text")
    images: List[str] = Field(default_factory=list, description="List of local image file paths")
    orientation: Literal["16:9", "9:16", "1:1"] = Field(default="16:9", description="Video aspect ratio (16:9, 9:16, 1:1)")
    language: Literal["en", "hi"] = Field(default="en", description="Narration language ('en' for Indian English, 'hi' for Hindi)")
    voice_id: Optional[str] = Field(default=None, description="Specific neural voice ID from available voice catalog")
    speech_rate: str = Field(default="+10%", description="Speech tempo: e.g. -10%, +0%, +10%, +20%")
    duration_mode: Literal["dynamic", "fast", "relaxed", "custom"] = Field(default="dynamic", description="Pacing profile")
    custom_scene_duration: Optional[float] = Field(default=None, description="Fixed manual seconds per scene when duration_mode='custom'")
    motion_style: Literal["dynamic_mix", "zoom_in", "pans_only", "gentle_drift"] = Field(default="dynamic_mix", description="Camera motion sequence style")
    watermark_text: str = Field(default="REALTY ASSISTANT EXCLUSIVE", description="Top-left brand watermark text")
    show_progress_bar: bool = Field(default=True, description="Render dynamic golden progress bar along bottom")
    enable_ai_script: bool = Field(default=True, description="Whether to invoke Gemini LLM or use deterministic template")
    bgm_volume: float = Field(default=0.12, ge=0.0, le=1.0, description="Background music volume multiplier")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        val = str(v).strip()
        if not val:
            return "Exclusive Property Showcase"
        return val

    @field_validator("features", mode="before")
    @classmethod
    def clean_features(cls, v) -> List[str]:
        if isinstance(v, str):
            items = [item.strip() for item in v.split("\n") if item.strip()]
            return items if items else ["Modern architectural design", "Prime connected location", "Luxury lifestyle amenities"]
        elif isinstance(v, list):
            cleaned = [str(x).strip() for x in v if str(x).strip()]
            return cleaned if cleaned else ["Modern architectural design", "Prime connected location", "Luxury lifestyle amenities"]
        return ["Modern architectural design", "Prime connected location", "Luxury lifestyle amenities"]

    def get_valid_images(self, base_dir: Optional[Path] = None) -> List[Path]:
        """Filters and returns existing image paths, resolving relative paths against base_dir."""
        valid_paths = []
        for img in self.images:
            p = Path(img)
            if not p.is_absolute() and base_dir is not None:
                p = (base_dir / p).resolve()
            if p.exists() and p.is_file():
                valid_paths.append(p)
        return valid_paths


class SceneScript(BaseModel):
    """Specification for a single visual and auditory scene in the video."""
    scene_index: int
    scene_type: Literal["intro", "feature", "cta"]
    headline: str
    subtext: str
    voiceover_text: str
    image_path: Optional[str] = None
    duration: float = Field(default=4.5, description="Scene duration in seconds")


class VideoScript(BaseModel):
    """Complete generated multi-scene video script."""
    property_name: str
    language: str
    source: Literal["gemini", "template", "custom_storyboard"]
    scenes: List[SceneScript]
