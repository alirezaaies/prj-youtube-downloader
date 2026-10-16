"""Validate the YouTube engine, local challenge solver, and JavaScript runtime.

Both the CLI and desktop builder use this check. Solver scripts are shipped
locally; normal operation does not need to download executable code from GitHub.
"""

import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, requires
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version
from yt_dlp.version import __version__ as ENGINE_VERSION

MIN_ENGINE_VERSION = "2026.10.10.233141.dev0"
REPAIR = "Run: python -m pip install -U -r requirements.txt, then rebuild the app."


def find_deno():
    """Also support launching a venv's Python without activating its PATH."""
    name = "deno.exe" if sys.platform == "win32" else "deno"
    adjacent = Path(sys.executable).parent / name
    return str(adjacent) if adjacent.is_file() else shutil.which("deno")


def check_installation():
    """Return the installed EJS version after checking compatibility and files."""
    if Version(ENGINE_VERSION) < Version(MIN_ENGINE_VERSION):
        raise RuntimeError(f"yt-dlp {ENGINE_VERSION} is too old for this build. {REPAIR}")
    try:
        from yt_dlp_ejs import version
        from yt_dlp_ejs.yt import solver

        # Use the engine's own dependency declaration, rather than guessing an
        # independently updated solver version. Metadata is bundled by build.py.
        dependency = next((Requirement(item) for item in requires("yt-dlp") or []
                           if Requirement(item).name == "yt-dlp-ejs"), None)
        if dependency is None or Version(version) not in dependency.specifier:
            raise ValueError("solver version does not match yt-dlp")
        if not solver.core() or not solver.lib():
            raise ValueError("empty challenge solver scripts")
        return version
    except (ImportError, OSError, ValueError, PackageNotFoundError, InvalidVersion) as exc:
        raise RuntimeError("YouTube challenge scripts (yt-dlp-ejs) are missing, "
                           f"incompatible, or incomplete. {REPAIR}") from exc


def check_support(deno=None):
    """Validate all prerequisites; return an explicit Deno executable path."""
    check_installation()
    deno = deno or find_deno()
    if not deno:
        raise RuntimeError(f"Deno 2.3+ is missing. {REPAIR}")
    try:
        result = subprocess.run([str(deno), "--version"], capture_output=True,
                                text=True, errors="replace", timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Cannot run Deno at {deno}. {REPAIR}") from exc
    match = re.search(r"deno (\d+)\.(\d+)\.(\d+)", result.stdout)
    if result.returncode or not match or tuple(map(int, match.groups())) < (2, 3, 0):
        raise RuntimeError(f"Deno 2.3+ is required; this runtime is unsupported. {REPAIR}")
    return str(deno)
