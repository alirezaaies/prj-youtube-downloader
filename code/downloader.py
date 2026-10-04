"""Download one YouTube video or a whole playlist with yt-dlp.

Examples:
    python downloader.py "VIDEO_OR_PLAYLIST_LINK"
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" -o ~/Videos
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --audio
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --quality 480
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --quality 1080 --exact-quality
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --ffmpeg-location /opt/ffmpeg/bin
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --browser firefox
    python downloader.py          # asks for the link
"""

import argparse
import shutil
import subprocess
from pathlib import Path

from yt_dlp import YoutubeDL

# When no folder is given, files go to a "downloads" folder next to this script.
SCRIPT_FOLDER = Path(__file__).resolve().parent
DOWNLOAD_FOLDER = SCRIPT_FOLDER / "downloads"
# Video quality like YouTube's "720p": 360, 480, 720, 1080, etc. It is the
# short side of the picture (the height of a wide video).
DEFAULT_QUALITY = 720
# False: this quality or lower (or the nearest one above if nothing lower
# exists). True: exactly this quality, otherwise the video is skipped.
DEFAULT_EXACT_QUALITY = False


def is_playlist(url):
    """Return True when the link contains a playlist id (list=...)."""
    return "list=" in url


def file_name_template(url):
    """Tell yt-dlp how to name each downloaded file."""
    if is_playlist(url):
        # Playlist title/01 - Video title.mp4
        return "%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"
    # Video title.mp4
    return "%(title)s.%(ext)s"


def video_quality(quality=DEFAULT_QUALITY, exact=DEFAULT_EXACT_QUALITY,
                  ffmpeg_location=None):
    """Build the yt-dlp format text for the requested quality.

    Quality means the short side of the picture, like YouTube's "720p": the
    height of a wide video, but the width of a vertical (phone) video.
    """
    if quality <= 0:
        raise ValueError("quality must be a positive number of pixels")
    has_ffmpeg = ffmpeg_location or shutil.which("ffmpeg")
    if not exact:
        # No filter here: "res:<quality>" in format_sort (see build_options)
        # picks the largest video up to this quality, or the smallest above it
        # when nothing smaller exists, so a video is never skipped for quality.
        return "bestvideo*+bestaudio/best" if has_ffmpeg else "best"
    # Exact: a wide video must be exactly this high, a vertical one this wide.
    wide = f"[height={quality}][width>={quality}]"
    tall = f"[width={quality}][height>={quality}]"
    if has_ffmpeg:
        # Best video + best audio, joined by ffmpeg; after each "/" comes the
        # next choice to try: a vertical video, then ready-made files.
        return (f"bestvideo*{wide}+bestaudio/bestvideo*{tall}+bestaudio/"
                f"best{wide}/best{tall}")
    # Without ffmpeg, only ready-made files that contain video and audio.
    return f"best{wide}/best{tall}"


def build_options(url, folder, browser=None, audio=False, ffmpeg_location=None,
                  quality=DEFAULT_QUALITY, exact_quality=DEFAULT_EXACT_QUALITY):
    """Collect all settings in the dictionary that yt-dlp expects."""
    options = {
        "format": video_quality(quality, exact_quality, ffmpeg_location),
        # The ffmpeg program yt-dlp must use (None lets yt-dlp search by itself).
        "ffmpeg_location": ffmpeg_location or shutil.which("ffmpeg"),
        # Order of preference: the requested quality first ("res" is the short
        # side), then H.264 video and AAC (m4a) audio: an mp4 that plays
        # everywhere.
        "format_sort": [f"res:{quality}", "vcodec:h264", "acodec:m4a"],
        "merge_output_format": "mp4",
        "paths": {"home": str(folder)},
        "outtmpl": file_name_template(url),
        # Skip a video that fails (private, deleted, failed merge) and continue
        # with the rest of the playlist instead of stopping.
        "ignoreerrors": True,
        # Retry after a network drop (the Python default is 0 retries).
        "retries": 10,
    }
    if audio:
        # Only the sound: the best audio stream; the video quality is ignored.
        options["format"] = "bestaudio/best"
        if options["ffmpeg_location"]:
            # ffmpeg converts the downloaded audio to a 192 kbit/s mp3 file.
            options["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                 "preferredquality": "192"},
            ]
    if browser:
        # Reuse the YouTube login of this browser when YouTube asks for it.
        options["cookiesfrombrowser"] = (browser,)
    return options


def check_ffmpeg(location):
    """Run "ffmpeg -version" once: finding the file does not prove it works."""
    if not location:
        return  # No ffmpeg: the program still works with ready-made files.
    executable = Path(location).expanduser()
    if executable.is_dir():
        # A folder was given: look for the ffmpeg program inside it
        # (shutil.which also finds "ffmpeg.exe" on Windows).
        executable = executable / "ffmpeg"
        executable = Path(shutil.which(str(executable)) or str(executable))
    try:
        result = subprocess.run(
            [str(executable), "-version"], capture_output=True, text=True,
            errors="replace", timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        # OSError: the file is missing or not executable. Timeout: it hangs.
        raise RuntimeError(f"Cannot run FFmpeg at {executable}: {exc}") from exc
    if result.returncode:
        # The program started but reported an error (for example a broken build
        # or a missing system library). Show its own message to the user.
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"FFmpeg exists but cannot run: {executable} "
            f"(exit code 0x{result.returncode & 0xffffffff:08X}). "
            "Repair the FFmpeg installation or use --ffmpeg-location with a "
            f"working build. {details}"
        )


def download(url, folder=DOWNLOAD_FOLDER, browser=None, audio=False,
             ffmpeg_location=None, quality=DEFAULT_QUALITY,
             exact_quality=DEFAULT_EXACT_QUALITY):
    """Download the link into folder. Return 0 when everything succeeded."""
    # Use the ffmpeg the user gave, otherwise the one found on the PATH.
    if ffmpeg_location:
        location = str(Path(ffmpeg_location).expanduser())
    else:
        location = shutil.which("ffmpeg")
    # Stop early with a clear message if that ffmpeg cannot run.
    check_ffmpeg(location)

    folder = Path(folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Saving to: {folder}")

    options = build_options(url, folder, browser, audio, location,
                            quality, exact_quality)
    with YoutubeDL(options) as ydl:
        return ydl.download([url])


def main():
    parser = argparse.ArgumentParser(
        description="Download a YouTube video or a whole playlist."
    )
    parser.add_argument("url", nargs="?", help="video or playlist link")
    parser.add_argument(
        "-o", "--output", default=DOWNLOAD_FOLDER,
        help="folder for the files (default: downloads/ next to this script)",
    )
    parser.add_argument(
        "-a", "--audio", action="store_true",
        help="save only the sound, as an mp3 file",
    )
    parser.add_argument(
        "--browser",
        help="use this browser's YouTube login, e.g. firefox or chrome",
    )
    parser.add_argument(
        "--ffmpeg-location",
        help="path to a working ffmpeg executable or its containing folder",
    )
    parser.add_argument(
        "--quality", type=int, default=DEFAULT_QUALITY,
        help=f"video quality such as 480 or 720: this or lower "
             f"(default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--exact-quality", action="store_true", default=DEFAULT_EXACT_QUALITY,
        help="require exactly this quality; skip the video if unavailable "
             "(ignored for audio)",
    )
    args = parser.parse_args()
    # type=int already rejects text; this also rejects 0 and negative numbers.
    if args.quality <= 0:
        parser.error("--quality must be a positive number, such as 720")

    url = args.url or input("Paste a YouTube video or playlist link: ").strip()
    url = url.replace("\\", "")  # zsh may paste ? and = as \? and \=
    if not url:
        parser.error("a link is required")

    try:
        result = download(url, args.output, args.browser, args.audio,
                          args.ffmpeg_location, args.quality, args.exact_quality)
    except RuntimeError as exc:
        # A broken ffmpeg: print one clear line and exit with code 1.
        parser.exit(1, f"Error: {exc}\n")
    except KeyboardInterrupt:
        print("\nStopped. Run the same command again to continue.")
        return

    if result == 0:
        print("Done. All files were downloaded.")
    else:
        print("Finished, but some files could not be downloaded (see the errors above).")


if __name__ == "__main__":
    main()
