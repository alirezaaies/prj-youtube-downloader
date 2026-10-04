"""Offline checks for downloader.py. Run with: python -m unittest -v"""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import downloader

VIDEO = "https://www.youtube.com/watch?v=abc123"
PLAYLIST = "https://www.youtube.com/playlist?list=PL123"


class DownloaderTests(unittest.TestCase):
    def test_detects_playlist_and_single_video(self):
        self.assertTrue(downloader.is_playlist(PLAYLIST))
        self.assertFalse(downloader.is_playlist(VIDEO))

    def test_single_video_is_named_by_title(self):
        self.assertEqual(downloader.file_name_template(VIDEO), "%(title)s.%(ext)s")

    def test_playlist_gets_its_own_folder(self):
        name = downloader.file_name_template(PLAYLIST)
        self.assertTrue(name.startswith("%(playlist_title)s/"))

    def test_default_folder_is_downloads_next_to_script(self):
        script_folder = Path(downloader.__file__).resolve().parent
        self.assertEqual(downloader.DOWNLOAD_FOLDER, script_folder / "downloads")

    def test_options_use_given_folder_and_browser(self):
        options = downloader.build_options(VIDEO, "/tmp/videos", "firefox")
        self.assertEqual(options["paths"], {"home": "/tmp/videos"})
        self.assertEqual(options["cookiesfrombrowser"], ("firefox",))

    def test_retries_after_network_drop(self):
        self.assertEqual(downloader.build_options(VIDEO, "/tmp/videos")["retries"], 10)

    def test_audio_only_becomes_mp3(self):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            options = downloader.build_options(VIDEO, "/tmp/videos", audio=True)
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")

    def test_audio_only_without_ffmpeg_keeps_original_file(self):
        with patch("shutil.which", return_value=None):
            options = downloader.build_options(VIDEO, "/tmp/videos", audio=True)
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertNotIn("postprocessors", options)

    def test_quality_without_ffmpeg(self):
        with patch("shutil.which", return_value=None):
            self.assertEqual(downloader.video_quality(), "best")

    def test_default_quality_prefers_720_or_lower(self):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            options = downloader.build_options(VIDEO, "/tmp/videos")
        self.assertEqual(options["format"], "bestvideo*+bestaudio/best")
        self.assertEqual(options["format_sort"][0], "res:720")

    def test_quality_option_changes_the_preference(self):
        options = downloader.build_options(VIDEO, "/tmp/videos", quality=480)
        self.assertEqual(options["format_sort"][0], "res:480")

    def test_exact_quality_works_for_wide_and_vertical_videos(self):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            text = downloader.video_quality(1080, exact=True)
        self.assertIn("bestvideo*[height=1080][width>=1080]+bestaudio", text)  # wide
        self.assertIn("bestvideo*[width=1080][height>=1080]+bestaudio", text)  # vertical

    def test_exact_quality_without_ffmpeg_uses_ready_made_files(self):
        with patch("shutil.which", return_value=None):
            text = downloader.video_quality(360, exact=True)
        self.assertEqual(text, "best[height=360][width>=360]/best[width=360][height>=360]")

    def test_quality_must_be_positive(self):
        with self.assertRaises(ValueError):
            downloader.video_quality(0)

    def test_given_ffmpeg_location_is_used(self):
        with patch("shutil.which", return_value=None):
            options = downloader.build_options(VIDEO, "/tmp/videos",
                                               ffmpeg_location="/opt/ffmpeg")
        self.assertEqual(options["ffmpeg_location"], "/opt/ffmpeg")
        self.assertTrue(options["format"].startswith("bestvideo*"))

    def test_no_ffmpeg_needs_no_check(self):
        self.assertIsNone(downloader.check_ffmpeg(None))

    def test_missing_ffmpeg_file_is_reported(self):
        with self.assertRaises(RuntimeError):
            downloader.check_ffmpeg("/no/such/folder/ffmpeg")

    def test_broken_ffmpeg_is_reported(self):
        broken = subprocess.CompletedProcess([], returncode=1, stdout="", stderr="bad build")
        with patch("subprocess.run", return_value=broken):
            with self.assertRaises(RuntimeError):
                downloader.check_ffmpeg("/usr/bin/ffmpeg")


if __name__ == "__main__":
    unittest.main()
