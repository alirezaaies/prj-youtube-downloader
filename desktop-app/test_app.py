"""Offline checks for the desktop app's helpers. Run with: python -m unittest -v

These tests never open a window and never use the internet.
"""

import unittest
import queue
import threading
from unittest.mock import patch, Mock

import app


class AppHelperTests(unittest.TestCase):
    def test_clean_link_removes_spaces_and_backslashes(self):
        self.assertEqual(app.clean_link("  https://youtu.be/x\\?si\\=1 "),
                         "https://youtu.be/x?si=1")

    def test_human_size(self):
        self.assertEqual(app.human_size(512), "512 B")
        self.assertEqual(app.human_size(1536000), "1.5 MB")

    def test_progress_text_for_a_playlist(self):
        text = app.progress_text({"count": 15, "index": 2, "percent": 45.2,
                                  "speed": 2200000, "eta": 42})
        self.assertEqual(text, "Item 2 of 15  ·  Downloading 45%  ·  2.1 MB/s  ·  0:42 left")

    def test_progress_text_without_details(self):
        self.assertEqual(app.progress_text({"percent": None}), "Downloading")

    def test_friendly_error_explains_sign_in(self):
        hint = app.friendly_error("ERROR: [youtube] x: Sign in to confirm you're not a bot")
        self.assertIn("Browser login", hint)

    def test_friendly_error_is_empty_for_unknown_messages(self):
        self.assertEqual(app.friendly_error("something new"), "")

    def test_log_lines_become_short_and_readable(self):
        self.assertEqual(app.readable_log_line("[download] Destination: /tmp/x/My video.f135.mp4"),
                         "Saving My video.f135.mp4")
        self.assertEqual(app.readable_log_line('[Merger] Merging formats into "/tmp/x/A.mp4"'),
                         "Joining video and audio into A.mp4")
        self.assertEqual(app.readable_log_line("[download] Downloading item 2 of 15"),
                         "Downloading item 2 of 15")

    def test_technical_log_lines_are_hidden(self):
        self.assertIsNone(app.readable_log_line("[youtube] abc: Downloading webpage"))
        self.assertIsNone(app.readable_log_line("Deleting original file /tmp/a.m4a"))

    def test_chosen_ffmpeg_wins(self):
        self.assertEqual(app.find_ffmpeg("/my/ffmpeg"), "/my/ffmpeg")

    def test_no_bundled_tools_when_running_from_source(self):
        self.assertIsNone(app.bundled_tool("ffmpeg"))

    def test_missing_ffmpeg_everywhere(self):
        with patch("shutil.which", return_value=None):
            self.assertIsNone(app.find_ffmpeg(""))


class SolverWorkerTests(unittest.TestCase):
    def test_missing_ejs_stops_before_contacting_youtube(self):
        events = queue.Queue()
        with patch.object(app.downloader.youtube_support, "check_support",
                          side_effect=RuntimeError("Missing yt-dlp-ejs")), \
                patch.object(app, "YoutubeDL") as engine:
            app.run_download({"ffmpeg": None}, events, threading.Event())
        engine.assert_not_called()
        self.assertEqual(events.get_nowait(), ("done", "error", "Missing yt-dlp-ejs"))

    def test_worker_passes_verified_runtime_to_engine(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            events = queue.Queue()
            engine = Mock()
            engine.__enter__ = Mock(return_value=engine)
            engine.__exit__ = Mock(return_value=False)
            engine.download.return_value = 0
            job = {"url": "https://youtu.be/yt1TAv5U780", "folder": folder,
                   "browser": None, "audio": False, "ffmpeg": None,
                   "quality": 720, "exact": False}
            with patch.object(app.downloader.youtube_support, "check_support", return_value="/test/deno"), \
                    patch.object(app, "YoutubeDL", return_value=engine) as factory:
                app.run_download(job, events, threading.Event())
            self.assertEqual(factory.call_args.args[0]["js_runtimes"],
                             {"deno": {"path": "/test/deno"}})
            self.assertEqual(events.get_nowait(), ("done", "ok", ""))


if __name__ == "__main__":
    unittest.main()
