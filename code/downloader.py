"""Download one YouTube video or a whole playlist with yt-dlp.

Examples:
    python downloader.py "VIDEO_OR_PLAYLIST_LINK"
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" -o ~/Videos
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --audio
    python downloader.py "VIDEO_OR_PLAYLIST_LINK" --browser firefox
    python downloader.py          # asks for the link
"""

import argparse
import shutil
from pathlib import Path

from yt_dlp import YoutubeDL

# When no folder is given, files go to a "downloads" folder next to this script.
SCRIPT_FOLDER = Path(__file__).resolve().parent
DOWNLOAD_FOLDER = SCRIPT_FOLDER / "downloads"


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


def video_quality():
    """Choose the best quality that this computer can save."""
    if shutil.which("ffmpeg"):
        # Best video + best audio, joined into one file by ffmpeg.
        return "bestvideo*+bestaudio/best"
    # Without ffmpeg, take the best file that already contains both.
    return "best"


def build_options(url, folder, browser=None, audio=False):
    """Collect all settings in the dictionary that yt-dlp expects."""
    options = {
        "format": video_quality(),
        # Prefer H.264 video and AAC (m4a) audio: an mp4 that plays everywhere.
        "format_sort": ["vcodec:h264", "res", "acodec:m4a"],
        "merge_output_format": "mp4",
        "paths": {"home": str(folder)},
        "outtmpl": file_name_template(url),
        "ignoreerrors": True,  # skip a private or deleted playlist video
        # Retry after a network drop (the Python default is 0 retries).
        "retries": 10,
    }
    if audio:
        # Only the sound: the best audio stream, converted to mp3 by ffmpeg.
        options["format"] = "bestaudio/best"
        if shutil.which("ffmpeg"):
            options["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                 "preferredquality": "192"},
            ]
    if browser:
        # Reuse the YouTube login of this browser when YouTube asks for it.
        options["cookiesfrombrowser"] = (browser,)
    return options


def download(url, folder=DOWNLOAD_FOLDER, browser=None, audio=False):
    """Download the link into folder. Return 0 when everything succeeded."""
    folder = Path(folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Saving to: {folder}")

    with YoutubeDL(build_options(url, folder, browser, audio)) as ydl:
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
    args = parser.parse_args()

    url = args.url or input("Paste a YouTube video or playlist link: ").strip()
    url = url.replace("\\", "")  # zsh may paste ? and = as \? and \=
    if not url:
        parser.error("a link is required")

    try:
        result = download(url, args.output, args.browser, args.audio)
    except KeyboardInterrupt:
        print("\nStopped. Run the same command again to continue.")
        return

    if result == 0:
        print("Done. All files were downloaded.")
    else:
        print("Finished, but some files could not be downloaded (see the errors above).")


if __name__ == "__main__":
    main()
