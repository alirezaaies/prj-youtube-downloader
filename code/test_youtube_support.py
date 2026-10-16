"""Offline regression checks for missing/mismatched YouTube solver packages."""

import subprocess
import sys
import unittest
from unittest.mock import patch

import youtube_support as support


class YouTubeSupportTests(unittest.TestCase):
    def test_old_engine_requests_requirements_update(self):
        with patch.object(support, "ENGINE_VERSION", "2026.08.19"):
            with self.assertRaisesRegex(RuntimeError, "too old"):
                support.check_installation()

    def test_plain_ytdlp_without_ejs_gets_actionable_error(self):
        with patch.dict(sys.modules, {"yt_dlp_ejs": None}):
            with self.assertRaisesRegex(RuntimeError, "yt-dlp-ejs.*missing"):
                support.check_installation()

    def test_mismatched_solver_is_rejected(self):
        with patch.object(support, "requires", return_value=["yt-dlp-ejs==999"]):
            with self.assertRaisesRegex(RuntimeError, "incompatible"):
                support.check_installation()

    def test_missing_bundled_javascript_is_rejected(self):
        with patch("yt_dlp_ejs.yt.solver.core", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                support.check_installation()

    def test_valid_local_solver_is_accepted(self):
        self.assertTrue(support.check_installation())

    def test_missing_runtime_is_reported(self):
        with patch.object(support, "find_deno", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Deno 2.3.*missing"):
                support.check_support()

    def test_old_runtime_is_rejected(self):
        result = subprocess.CompletedProcess([], 0, "deno 2.2.0\n", "")
        with patch.object(support.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "unsupported"):
                support.check_support("/test/deno")

    def test_working_runtime_path_is_passed_to_ytdlp(self):
        result = subprocess.CompletedProcess([], 0, "deno 2.3.0\n", "")
        with patch.object(support.subprocess, "run", return_value=result):
            self.assertEqual(support.check_support("/test/deno"), "/test/deno")


if __name__ == "__main__":
    unittest.main()
