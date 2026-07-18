"""Focused contract tests for the unified catalog shell."""

from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "catalog.html").read_text()


class CatalogMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.sections = []
        self.iframes = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "button" and values.get("data-section"):
            self.sections.append(values["data-section"])
        if tag == "iframe":
            self.iframes[values.get("id")] = values


class CatalogShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markup = CatalogMarkup()
        cls.markup.feed(SOURCE)

    def test_has_exactly_three_catalog_sections(self):
        self.assertEqual(self.markup.sections.count("three"), 1)
        self.assertEqual(self.markup.sections.count("p5"), 1)
        self.assertEqual(self.markup.sections.count("strudel"), 1)

    def test_ids_are_unique(self):
        self.assertEqual(len(self.markup.ids), len(set(self.markup.ids)))

    def test_catalog_routes_remain_on_one_origin(self):
        for path in (
            "/threejs/browser/index.html?forceWebGL=1",
            "/assets/browse.html",
            "/assets/music/browse.html",
            "/livecode.html?embedded=1",
        ):
            self.assertIn(path, SOURCE)
            self.assertFalse(path.startswith("http"))

    def test_visible_and_engine_frames_are_separate(self):
        self.assertEqual(
            self.markup.iframes["catalog-frame"]["src"],
            "/threejs/browser/index.html?forceWebGL=1",
        )
        self.assertEqual(
            self.markup.iframes["engine-frame"]["src"],
            "/livecode.html?embedded=1",
        )
        self.assertEqual(self.markup.iframes["engine-frame"]["aria-hidden"], "true")

    def test_audio_click_preserves_user_activation(self):
        start = SOURCE.index("function enableAudio()")
        end = SOURCE.index("document.querySelectorAll('.section-tab')", start)
        handler = SOURCE[start:end]
        self.assertIn("button.click()", handler)
        self.assertNotIn("await ", handler)
        self.assertIn("__livecodeAudioReady", SOURCE)

    def test_music_controls_use_unified_server_api(self):
        self.assertIn("fetch('/status'", SOURCE)
        self.assertIn("fetch('/strudel/hush'", SOURCE)
        self.assertIn("getElementById('start-btn')", SOURCE)


if __name__ == "__main__":
    unittest.main()
