"""Build the desktop app for this computer's operating system with PyInstaller.

Run inside the activated build environment:   python build.py

Result in dist/:
    Windows:  "YouTube Downloader" folder with "YouTube Downloader.exe", and a .zip
    macOS:    "YouTube Downloader.app", and a .zip
    Linux:    "YouTube Downloader" folder with the program, and a .tar.gz
plus a .sha256 file so receivers can check that the archive was not changed.

PyInstaller cannot build for other systems: build the Windows app on Windows,
the macOS app on a Mac, and the Linux app on Linux.
"""

import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__

APP_NAME = "YouTube Downloader"
HERE = Path(__file__).resolve().parent
EXE = ".exe" if sys.platform == "win32" else ""
SYSTEM = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")


def find_deno():
    """The deno program installed by pip into this environment (required)."""
    next_to_python = Path(sys.executable).parent / f"deno{EXE}"
    path = next_to_python if next_to_python.is_file() else shutil.which("deno")
    if not path:
        sys.exit("deno was not found. Run: python -m pip install -r requirements.txt")
    return str(path)


def find_ffmpeg():
    """An FFmpeg you placed in the ffmpeg/ folder (optional), or None."""
    path = HERE / "ffmpeg" / f"ffmpeg{EXE}"
    return str(path) if path.is_file() else None


def pyinstaller_arguments(deno, ffmpeg):
    """All PyInstaller settings, one per line, so each one is easy to read."""
    icon = {"windows": "icon.ico", "macos": "icon.icns"}.get(SYSTEM, "icon.png")
    sep = os.pathsep  # "SOURCE;DEST" on Windows, "SOURCE:DEST" elsewhere
    args = [
        str(HERE / "app.py"),
        "--name", APP_NAME,
        "--windowed",              # a window app: no console window
        "--onedir",                # a folder: starts fast, no unpacking
        "--noconfirm",             # replace an older build without asking
        "--clean",                 # start from an empty cache
        "--paths", str(HERE.parent / "code"),    # find downloader.py
        "--add-data", f"{HERE / 'assets' / 'icon.png'}{sep}assets",
        "--add-binary", f"{deno}{sep}bin",       # YouTube needs a JS runtime
        "--icon", str(HERE / "assets" / icon),
        "--distpath", str(HERE / "dist"),
        "--workpath", str(HERE / "build"),
        "--specpath", str(HERE / "build"),
    ]
    if ffmpeg:
        args += ["--add-binary", f"{ffmpeg}{sep}bin"]
    if SYSTEM == "macos":
        args += ["--osx-bundle-identifier", "io.github.alirezaaies.youtubedownloader"]
    return args


def make_archive():
    """Pack the built app into one file that is easy to share."""
    dist = HERE / "dist"
    arch = platform.machine().lower() or "unknown"
    base = dist / f"YouTube-Downloader-{SYSTEM}-{arch}"
    if SYSTEM == "macos":
        # ditto is built into macOS and keeps the .app bundle intact.
        archive = Path(f"{base}.zip")
        subprocess.run(["ditto", "-c", "-k", "--keepParent",
                        str(dist / f"{APP_NAME}.app"), str(archive)], check=True)
    elif SYSTEM == "windows":
        archive = Path(shutil.make_archive(str(base), "zip", dist, APP_NAME))
    else:
        # tar.gz keeps the "executable" permission of the Linux program.
        archive = Path(shutil.make_archive(str(base), "gztar", dist, APP_NAME))
    return archive


def write_checksum(archive):
    """Write the SHA-256 fingerprint of the archive next to it."""
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return digest


def main():
    deno, ffmpeg = find_deno(), find_ffmpeg()
    print(f"Building {APP_NAME} for {SYSTEM}")
    print(f"  deno:   {deno}")
    print(f"  ffmpeg: {ffmpeg or 'not bundled (the app uses the one on the computer)'}")
    PyInstaller.__main__.run(pyinstaller_arguments(deno, ffmpeg))
    archive = make_archive()
    digest = write_checksum(archive)
    size = archive.stat().st_size / 1024 / 1024
    print(f"\nDone: {archive}  ({size:.0f} MB)")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
