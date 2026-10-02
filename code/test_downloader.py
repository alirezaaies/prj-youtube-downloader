"""Offline checks for downloader.py. Run with: python -m unittest -v"""

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

    def test_default_folder_is_next_to_script(self):
        self.assertEqual(downloader.SCRIPT_FOLDER, Path(downloader.__file__).resolve().parent)

    def test_options_use_given_folder_and_browser(self):
        options = downloader.build_options(VIDEO, "/tmp/videos", "firefox")
        self.assertEqual(options["paths"], {"home": "/tmp/videos"})
        self.assertEqual(options["cookiesfrombrowser"], ("firefox",))

    def test_quality_without_ffmpeg(self):
        with patch("shutil.which", return_value=None):
            self.assertEqual(downloader.video_quality(), "best")


if __name__ == "__main__":
    unittest.main()
