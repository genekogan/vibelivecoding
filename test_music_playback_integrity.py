"""Regression tests for honest, transactional music playback."""

import json
from pathlib import Path
import unittest

from assets.tools.validate import Gate, check_stem_schema
from livecode_server import LivecodeController


ROOT = Path(__file__).resolve().parent
MUSIC_BROWSER = (ROOT / "assets/music/browse.html").read_text()
LIVE_CLIENT = (ROOT / "livecode.html").read_text()
ARC_VERIFIER = (ROOT / "assets/tools/verify_arcs.py").read_text()


class ControllerPlaybackTest(unittest.TestCase):
    def test_browser_execution_errors_raise(self):
        with self.assertRaisesRegex(RuntimeError, "bad pattern"):
            LivecodeController._raise_for_browser_error(
                {"type": "error", "message": "bad pattern"}
            )

    def test_failed_new_track_is_removed(self):
        controller = LivecodeController()
        calls = []

        def replay():
            calls.append(dict(controller._tracks))
            if len(calls) == 1:
                raise RuntimeError("compile failed")

        controller._replay_all = replay
        with self.assertRaisesRegex(RuntimeError, "compile failed"):
            controller.set_track("bass", 'note("c2").s("sawtooth").play()')
        self.assertNotIn("bass", controller._tracks)
        self.assertEqual(len(calls), 2)

    def test_failed_track_update_restores_previous_code(self):
        controller = LivecodeController()
        controller._tracks["bass"] = "old-code"
        calls = []

        def replay():
            calls.append(dict(controller._tracks))
            if len(calls) == 1:
                raise RuntimeError("compile failed")

        controller._replay_all = replay
        with self.assertRaisesRegex(RuntimeError, "compile failed"):
            controller.set_track("bass", "new-code.play()")
        self.assertEqual(controller._tracks["bass"], "old-code")
        self.assertEqual(calls[-1]["bass"], "old-code")


class CatalogPlaybackContractTest(unittest.TestCase):
    def test_verified_stems_pass_static_schema(self):
        failures = []
        for path in sorted((ROOT / "assets/music/stems").glob("*/*.json")):
            asset = json.loads(path.read_text())
            if not asset.get("verified"):
                continue
            try:
                check_stem_schema(asset)
            except Gate as error:
                failures.append(f"{asset.get('id', path.stem)}: {error}")
        self.assertEqual(failures, [])

    def test_music_browser_never_swallows_playback_errors(self):
        self.assertNotIn("const post = (p, b) =>", MUSIC_BROWSER)
        self.assertIn("if (!response.ok || body?.ok === false", MUSIC_BROWSER)
        self.assertIn("id=\"play-error\"", MUSIC_BROWSER)
        self.assertIn("await requireAudioEngine()", MUSIC_BROWSER)

    def test_arcs_are_not_mistaken_for_standalone_tracks(self):
        self.assertIn("if (a.kind === 'arc')", MUSIC_BROWSER)
        self.assertIn("An arc is an arrangement, not a standalone sound", MUSIC_BROWSER)
        self.assertIn("const recommendedIds", MUSIC_BROWSER)
        breakdown = json.loads(
            (ROOT / "assets/music/arcs/arc.breakdown_first.arc.json").read_text()
        )
        self.assertEqual(breakdown["kind"], "arc")
        self.assertNotIn("slot", breakdown)
        self.assertNotIn("code", breakdown)

    def test_track_api_rejects_missing_names_explicitly(self):
        server = (ROOT / "livecode_server.py").read_text()
        self.assertIn("strudel track requires a non-empty name", server)

    def test_arc_gate_fails_on_http_playback_errors(self):
        self.assertIn("response.raise_for_status()", ARC_VERIFIER)

    def test_audio_startup_fails_closed(self):
        startup = LIVE_CLIENT[LIVE_CLIENT.index("// ── Start") :]
        failure = startup.index("catch (e)")
        self.assertNotIn('overlay").style.display = "none"', startup[failure:])
        self.assertIn("window.__livecodeAudioError = message", startup)
        self.assertIn('ac.state !== "running"', startup)


if __name__ == "__main__":
    unittest.main()
