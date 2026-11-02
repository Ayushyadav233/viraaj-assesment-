import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from src.models import PropertyInput, SceneScript, VideoScript

load_dotenv()
logger = logging.getLogger(__name__)

KEYWORD_MAP = {
    "kitchen": ["kitchen", "chef", "modular", "cooking", "dining", "pantry"],
    "living": ["living", "marble", "hall", "layout", "lounge", "ceiling", "drawing"],
    "bedroom": ["bedroom", "master", "suite", "wardrobe", "bed", "closet"],
    "pool": ["pool", "swimming", "water", "deck", "cabana"],
    "balcony": ["balcony", "view", "golf", "terrace", "panoramic", "skyline"],
    "bath": ["bath", "bathroom", "tub", "jacuzzi", "spa"],
    "club": ["club", "gym", "sports", "fitness", "amenities", "clubhouse"],
    "exterior": ["exterior", "facade", "entrance", "tower", "elevation", "twilight", "drone", "villa"],
}


def find_matching_image(
    text: str,
    candidate_images: List[Path],
    used_images: set,
    default_idx: int = 0,
) -> Optional[str]:
    """Semantically correlates visual photo assets with spoken scene concepts.
    Ensures that when a kitchen, pool, or master suite is discussed, the corresponding photo appears.
    """
    if not candidate_images:
        return None

    text_lower = text.lower()

    # 1. Search for semantic category match in filename
    for category, terms in KEYWORD_MAP.items():
        if any(term in text_lower for term in terms):
            for img in candidate_images:
                str_path = str(img)
                if str_path not in used_images and category in img.stem.lower():
                    used_images.add(str_path)
                    return str_path

    # 2. If already used or no direct category in filename, pick first unused image
    for img in candidate_images:
        str_path = str(img)
        if str_path not in used_images:
            used_images.add(str_path)
            return str_path

    # 3. Fallback: cycle candidate images
    fallback_path = str(candidate_images[default_idx % len(candidate_images)])
    return fallback_path


def _generate_feature_voiceover(feature: str, language: str) -> str:
    """Generates broadcast-grade architectural copywriting for property highlights."""
    f_lower = feature.lower()
    is_hi = language == "hi"

    if any(k in f_lower for k in ["living", "marble", "hall", "layout", "ceiling"]):
        return (
            "खुले और भव्य लिविंग स्पेस, इटैलियन मार्बल और शानदार फिनिशिंग के साथ।"
            if is_hi
            else "Step into expansive, light-filled living halls adorned with imported Italian marble and grand proportions."
        )

    if any(k in f_lower for k in ["kitchen", "modular", "chef", "cooking"]):
        return (
            "प्रीमियम फिटिंग्स के साथ बना आधुनिक और स्मार्ट यूरोपीय मॉड्यूलर किचन।"
            if is_hi
            else "A state-of-the-art European modular kitchen tailored with premium built-in appliances."
        )

    if any(k in f_lower for k in ["bed", "bedroom", "suite", "wardrobe"]):
        return (
            "शानदार मास्टर बेडरूम सुइट, वॉक-इन वार्डरोब और बेहतरीन इंटीरियर्स के साथ।"
            if is_hi
            else "Your master suite offers a private sanctuary with bespoke wardrobes and tranquil elegance."
        )

    if any(k in f_lower for k in ["pool", "swim", "deck"]):
        return (
            "रिलैक्स करें टेम्परेचर-कंट्रोल्ड इन्फिनिटी पूल और सनडेक के साथ।"
            if is_hi
            else "Unwind at the resort-style infinity swimming pool and sun-drenched private deck."
        )

    if any(k in f_lower for k in ["balcony", "view", "golf", "terrace"]):
        return (
            "अपनी प्राइवेट बालकनी से लुत्फ उठाएं खुले और खूबसूरत नजारों का।"
            if is_hi
            else "Enjoy breathtaking panoramic skyline views and fresh breezes from your private balcony."
        )

    if any(k in f_lower for k in ["bath", "spa", "tub"]):
        return (
            "स्पा-प्रेरित मास्टर बाथरूम, शानदार मार्बल फिनिश और सोकिंग टब के साथ।"
            if is_hi
            else "A spa-inspired master bathroom crafted with Italian marble and a soaking tub."
        )

    # General feature
    return (
        f"यहाँ आपको मिलता है {feature}।"
        if is_hi
        else f"Designed for luxury lifestyle, featuring {feature}."
    )


def generate_template_script(prop: PropertyInput, image_paths: List[Path]) -> VideoScript:
    """Deterministic, broadcast-quality script generator adhering strictly to supplied facts.
    Matches visuals to spoken text semantically.
    """
    is_hindi = prop.language == "hi"
    scenes: List[SceneScript] = []
    used_images = set()

    # 1. Intro Scene (Matched to Exterior)
    intro_img = find_matching_image("exterior elevation facade entrance", image_paths, used_images, default_idx=0)
    if is_hindi:
        intro_headline = prop.name
        intro_subtext = f"{prop.property_type} • {prop.location} • {prop.price}"
        intro_vo = f"{prop.location} के प्राइम लोकेशन पर प्रस्तुत है {prop.name}। लक्ज़री लाइफस्टाइल, कीमत मात्र {prop.price} से।"
    else:
        intro_headline = prop.name
        intro_subtext = f"{prop.property_type} • {prop.location} • {prop.price}"
        intro_vo = f"Welcome to {prop.name}, an iconic address in {prop.location}. Luxury living starts at {prop.price}."

    scenes.append(
        SceneScript(
            scene_index=0,
            scene_type="intro",
            headline=intro_headline,
            subtext=intro_subtext,
            voiceover_text=intro_vo,
            image_path=intro_img,
            duration=4.5,
        )
    )

    # 2. Feature Scenes (Semantically paired with corresponding photos)
    features = prop.features if prop.features else ["Spacious modern layout", "Premium branded fixtures", "Prime connectivity"]

    for i, feat in enumerate(features):
        feat_img = find_matching_image(feat, image_paths, used_images, default_idx=i + 1)

        # Clean, punchy headline
        short_headline = feat.split(" with ")[0].split(" and ")[0]
        if len(short_headline) > 36:
            short_headline = feat[:36].strip()

        feat_vo = _generate_feature_voiceover(feat, prop.language)

        scenes.append(
            SceneScript(
                scene_index=len(scenes),
                scene_type="feature",
                headline=short_headline.title(),
                subtext=feat,
                voiceover_text=feat_vo,
                image_path=feat_img,
                duration=4.2,
            )
        )

    # 3. Call To Action Scene (Matched to Twilight Exterior / Entrance)
    cta_img = find_matching_image("twilight exterior entrance", image_paths, used_images, default_idx=len(image_paths) - 1)
    if is_hindi:
        cta_headline = "आज ही संपर्क करें"
        cta_subtext = prop.contact_cta
        cta_vo = "अपने सपनों का आशियाना आज ही चुनें। एक्सक्लूसिव साइट विजिट और ऑफर्स के लिए आज ही संपर्क करें।"
    else:
        cta_headline = "Schedule Your Private Tour"
        cta_subtext = prop.contact_cta
        cta_vo = "Experience this masterpiece in person. Contact Realty Assistant today to schedule your private tour."

    scenes.append(
        SceneScript(
            scene_index=len(scenes),
            scene_type="cta",
            headline=cta_headline,
            subtext=cta_subtext,
            voiceover_text=cta_vo,
            image_path=cta_img,
            duration=4.5,
        )
    )

    return VideoScript(
        property_name=prop.name,
        language=prop.language,
        source="template",
        scenes=scenes,
    )


def validate_ai_output(prop: PropertyInput, raw_scenes: list) -> bool:
    """Verifies that AI generated scenes strictly adhere to constraints."""
    if not isinstance(raw_scenes, list) or len(raw_scenes) < 2:
        return False

    for s in raw_scenes:
        if not isinstance(s, dict):
            return False
        vo = s.get("voiceover_text", "")
        if len(vo.split()) > 35:
            logger.warning("AI voiceover line too long: %s", vo)
            return False

    return True


def generate_gemini_script(prop: PropertyInput, image_paths: List[Path], api_key: Optional[str] = None) -> VideoScript:
    """Generates an engaging, professional script via Google Gemini API.
    Enforces strict grounding and semantic visual pairing.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or key.strip() == "your_gemini_api_key_here":
        logger.info("No valid Gemini API key found. Using deterministic template engine.")
        return generate_template_script(prop, image_paths)

    num_scenes = max(3, min(len(prop.features) + 2, len(image_paths) if image_paths else 5))
    lang_name = "Hindi (in Devanagari script)" if prop.language == "hi" else "Indian English"

    prompt = f"""You are a luxury real estate video copywriter creating an Architectural Digest style commercial promo for {prop.name}.

STRICT FACTUAL GROUNDING MANDATE:
- You must ONLY use facts explicitly provided in the input below.
- NEVER invent sq.ft., prices, nearby metro/schools, or amenities not present in the input.
- Language: {lang_name}.
- Keep spoken voiceover lines punchy, natural, and under 16 words per scene for natural commercial cadence.

INPUT PROPERTY DETAILS:
- Property Name: {prop.name}
- Location: {prop.location}
- Price: {prop.price}
- Property Type: {prop.property_type}
- Key Features:
{chr(10).join(f"  * {f}" for f in prop.features)}
- CTA / Contact: {prop.contact_cta}

Generate exactly {num_scenes} scenes in valid JSON format conforming to this structure:
{{
  "scenes": [
    {{
      "scene_type": "intro",
      "headline": "Short impactful headline (max 5 words)",
      "subtext": "Brief subtitle with location and price",
      "voiceover_text": "One punchy spoken sentence for narration (max 15 words)"
    }},
    {{
      "scene_type": "feature",
      "headline": "Short title of the feature (max 4 words)",
      "subtext": "Exact feature description from input",
      "voiceover_text": "One natural spoken sentence describing this exact feature (max 15 words)"
    }},
    {{
      "scene_type": "cta",
      "headline": "Action-oriented call to action (max 5 words)",
      "subtext": "Contact details from input",
      "voiceover_text": "One inviting closing sentence containing contact info (max 16 words)"
    }}
  ]
}}
Only return the raw JSON object.
"""

    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        raw_text = response.text.strip()
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"^```\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        data = json.loads(raw_text)
        raw_scenes = data.get("scenes", [])

        if not validate_ai_output(prop, raw_scenes):
            logger.warning("AI output validation failed. Falling back to template.")
            return generate_template_script(prop, image_paths)

        scenes: List[SceneScript] = []
        used_images = set()

        for i, s in enumerate(raw_scenes):
            headline = s.get("headline", prop.name)
            subtext = s.get("subtext", "")
            vo_text = s.get("voiceover_text", "")
            stype = s.get("scene_type", "feature" if 0 < i < len(raw_scenes) - 1 else ("intro" if i == 0 else "cta"))

            img = find_matching_image(f"{headline} {subtext}", image_paths, used_images, default_idx=i)

            scenes.append(
                SceneScript(
                    scene_index=i,
                    scene_type=stype,
                    headline=headline,
                    subtext=subtext,
                    voiceover_text=vo_text,
                    image_path=img,
                    duration=4.2,
                )
            )

        return VideoScript(
            property_name=prop.name,
            language=prop.language,
            source="gemini",
            scenes=scenes,
        )

    except Exception as e:
        logger.warning("Gemini API call failed (%s). Gracefully falling back to template engine.", e)
        return generate_template_script(prop, image_paths)


def create_script(prop: PropertyInput, image_paths: List[Path], api_key: Optional[str] = None) -> VideoScript:
    """Master entry point for script generation."""
    if prop.enable_ai_script:
        return generate_gemini_script(prop, image_paths, api_key=api_key)
    return generate_template_script(prop, image_paths)
