import unittest
from pathlib import Path
from PIL import Image

from src.models import PropertyInput, SceneScript, VideoScript
from src.script_generator import create_script, generate_template_script, validate_ai_output
from src.scene_builder import create_placeholder_background, create_overlay_card
from src.tts import _normalize_speech_text


class TestPropertyVideoGenerator(unittest.TestCase):
    """Test suite covering core models, validation, and visual generators."""

    def test_property_input_defaults(self):
        prop = PropertyInput(name="Skyline Vista")
        self.assertEqual(prop.name, "Skyline Vista")
        self.assertEqual(prop.location, "Prime Location")
        self.assertEqual(prop.orientation, "16:9")
        self.assertEqual(prop.language, "en")
        self.assertTrue(len(prop.features) > 0)

    def test_template_script_structure(self):
        prop = PropertyInput(
            name="Emerald Heights",
            location="Sector 150, Noida",
            price="₹1.85 Cr",
            property_type="3 BHK Luxury Apartment",
            features=["Infinity Pool", "Marble Flooring"],
            contact_cta="Call 9876543210",
        )
        script = create_script(prop, [Path("img1.jpg"), Path("img2.jpg")])
        self.assertEqual(script.source, "template")
        self.assertEqual(script.scenes[0].scene_type, "intro")
        self.assertEqual(script.scenes[-1].scene_type, "cta")
        self.assertTrue(any(s.scene_type == "feature" for s in script.scenes))

    def test_hindi_script_generation(self):
        prop = PropertyInput(
            name="Emerald Heights",
            location="Sector 150, Noida",
            price="₹1.85 Cr",
            property_type="3 BHK Luxury Apartment",
            features=["Infinity Pool"],
            contact_cta="Call 9876543210",
            language="hi",
        )
        script = create_script(prop, [Path("img1.jpg")])
        self.assertEqual(script.language, "hi")
        self.assertIn("प्रस्तुत है", script.scenes[0].voiceover_text)

    def test_speech_normalization(self):
        en_text = _normalize_speech_text("Price is ₹1.5 Cr with 2,000 sq.ft. in 3 BHK", "en")
        self.assertNotIn("₹", en_text)
        self.assertIn("Rupees", en_text)
        self.assertIn("Crore", en_text)
        self.assertIn("square feet", en_text)

        hi_text = _normalize_speech_text("कीमत ₹1.5 Cr और 2,000 sq.ft.", "hi")
        self.assertNotIn("₹", hi_text)
        self.assertIn("रुपये", hi_text)
        self.assertIn("करोड़", hi_text)

    def test_placeholder_background_generation(self):
        bg = create_placeholder_background(1920, 1080, "Test Placeholder")
        self.assertIsInstance(bg, Image.Image)
        self.assertEqual(bg.size, (1920, 1080))

    def test_overlay_card_rendering(self):
        overlay = create_overlay_card(1920, 1080, "PREMIUM", "Test Headline", "Test Subtext", "16:9")
        self.assertIsInstance(overlay, Image.Image)
        self.assertEqual(overlay.size, (1920, 1080))
        self.assertEqual(overlay.mode, "RGBA")

    def test_custom_storyboard_script_source(self):
        script = VideoScript(
            property_name="Test Property",
            language="en",
            source="custom_storyboard",
            scenes=[
                SceneScript(
                    scene_index=0,
                    scene_type="intro",
                    headline="Intro",
                    subtext="Sub",
                    voiceover_text="Voiceover",
                )
            ],
        )
        self.assertEqual(script.source, "custom_storyboard")


if __name__ == "__main__":
    unittest.main()
