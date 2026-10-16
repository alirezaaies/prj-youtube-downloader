"""Progress and Persian rendering regressions; no window/network required."""

import unittest
from unittest.mock import patch
import subprocess

from presentation import DownloadProgress, display_text
import build


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tracker = DownloadProgress()
        self.info = {"id": "video", "format_id": "v"}
        self.tracker.begin(self.info)

    def update(self, **status):
        return self.tracker.update({"status": "downloading", "info_dict": self.info, **status})

    def test_hls_uses_fragments_instead_of_fluctuating_size_estimate(self):
        first = self.update(fragment_index=4, fragment_count=10,
                            downloaded_bytes=400, total_bytes_estimate=1000)
        second = self.update(fragment_index=5, fragment_count=10,
                             downloaded_bytes=500, total_bytes_estimate=10000)
        self.assertAlmostEqual(first["percent"], 39.2)
        self.assertAlmostEqual(second["percent"], 49)

    def test_byte_estimate_revision_cannot_move_bar_backwards(self):
        first = self.update(downloaded_bytes=700, total_bytes_estimate=1000)
        second = self.update(downloaded_bytes=750, total_bytes_estimate=2000)
        self.assertEqual(second["percent"], first["percent"])

    def test_retry_cannot_move_bar_backwards(self):
        first = self.update(downloaded_bytes=700, total_bytes=1000)
        second = self.update(downloaded_bytes=100, total_bytes=1000)
        self.assertEqual(second["percent"], first["percent"])

    def test_separate_video_then_audio_share_one_bar(self):
        self.tracker.begin({"id": "pair", "requested_formats": [
            {"format_id": "v", "filesize": 900}, {"format_id": "a", "filesize": 100}]})
        video = self.tracker.update({"status": "finished", "info_dict": {"id": "pair", "format_id": "v"}})
        audio = self.tracker.update({"status": "downloading", "downloaded_bytes": 10,
                                    "total_bytes": 100, "info_dict": {"id": "pair", "format_id": "a"}})
        self.assertAlmostEqual(video["percent"], 88.2)
        self.assertGreater(audio["percent"], video["percent"])
        self.assertEqual((audio["part"], audio["parts"]), (2, 2))
        self.assertFalse(video["transferred"])

    def test_unknown_stream_sizes_use_fixed_equal_shares(self):
        self.tracker.begin({"id": "pair", "requested_formats": [
            {"format_id": "v"}, {"format_id": "a"}]})
        first = self.tracker.update({"status": "finished", "info_dict": {"format_id": "v"}})
        second = self.tracker.update({"status": "downloading", "downloaded_bytes": 0,
                                     "total_bytes": 100, "info_dict": {"format_id": "a"}})
        self.assertEqual(first["percent"], 49)
        self.assertEqual(second["percent"], 49)

    def test_reserves_completion_until_postprocessing_success(self):
        result = self.update(status="finished")
        self.assertEqual(result["percent"], 98)
        self.assertTrue(result["transferred"])

    def test_underestimated_size_does_not_falsely_report_download_finished(self):
        result = self.update(downloaded_bytes=150, total_bytes_estimate=100)
        self.assertLessEqual(result["percent"], 98)
        self.assertFalse(result["transferred"])

    def test_next_playlist_entry_resets_progress(self):
        self.update(status="finished")
        self.tracker.begin({"id": "next", "playlist_index": 2, "format_id": "v"})
        result = self.update(downloaded_bytes=100, total_bytes=1000)
        self.assertAlmostEqual(result["percent"], 9.8)

    def test_unknown_total_does_not_invent_a_percentage(self):
        self.assertIsNone(self.update(downloaded_bytes=100)["percent"])


class TextTests(unittest.TestCase):
    def test_english_status_and_paths_are_unchanged(self):
        text = "Saving /tmp/Example video.mp4 - 52%"
        self.assertEqual(display_text(text), text)

    def test_persian_is_joined_and_ordered_inside_english_log_line(self):
        self.assertEqual(display_text("Saving سلام - GitHub.mp4"),
                         "Saving \ufee1\ufefc\ufeb3 - GitHub.mp4")

    def test_multiple_lines_keep_their_order(self):
        rendered = display_text("First line\nسلام\nLast line")
        self.assertTrue(rendered.startswith("First line\n"))
        self.assertTrue(rendered.endswith("\nLast line"))


class BuildFontTests(unittest.TestCase):
    def test_bitmap_only_linux_tk_is_rejected(self):
        with patch.object(build, "SYSTEM", "linux"), patch.object(build.shutil, "which", return_value="ldd"), \
                patch.object(build.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "libtk8.6.so", "")):
            with self.assertRaisesRegex(RuntimeError, "Xft"):
                build.check_tk_build()

    def test_linux_tk_with_xft_is_accepted(self):
        with patch.object(build, "SYSTEM", "linux"), patch.object(build.shutil, "which", return_value="ldd"), \
                patch.object(build.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "libXft.so.2", "")):
            build.check_tk_build()


if __name__ == "__main__":
    unittest.main()
