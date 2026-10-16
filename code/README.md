# Downloader code

This folder contains everything needed to run the YouTube downloader. The program
uses Python and the [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) library.

## What each file does

| File | Purpose |
|---|---|
| `downloader.py` | The complete, commented program: single video, whole playlist, audio only, quality, FFmpeg location, output folder, optional browser login |
| `youtube_support.py` | Checks the YouTube engine, matching EJS scripts and Deno |
| `test_youtube_support.py` | Eight dependency and packaging regression tests |
| `requirements.txt` | `yt-dlp` with its recommended helpers, plus the `deno` JavaScript runtime |
| `test_downloader.py` | 18 downloader tests (no internet needed) |
| `downloads/` | Default save folder, created by the first download and ignored by Git |

## Install

Use Python 3.10 or newer. Install [FFmpeg](https://ffmpeg.org/download.html) too
(recommended): it joins the best video and best audio into one MP4. From this folder:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda users can create an environment instead of `.venv`:

```bash
conda create -n ytdl python=3.12 -y
conda activate ytdl
python -m pip install -r requirements.txt
```

## Run

| Goal | Command |
|---|---|
| One video, saved in `downloads/` | `python downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"` |
| Whole playlist, saved in `downloads/` | `python downloader.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"` |
| Save in another folder | `python downloader.py "LINK" -o ~/Videos` |
| Only the sound, as MP3 | `python downloader.py "LINK" --audio` |
| Another quality: this or lower (default 720) | `python downloader.py "LINK" --quality 480` |
| Exactly this quality, else skip the video | `python downloader.py "LINK" --quality 1080 --exact-quality` |
| FFmpeg is not on the PATH | `python downloader.py "LINK" --ffmpeg-location /path/to/ffmpeg/bin` |
| Stop now, continue later | press `Ctrl+C`, then run the same command again |
| YouTube asks you to sign in | `python downloader.py "LINK" --browser firefox` |
| Let the program ask for the link | `python downloader.py` |
| Show help | `python downloader.py --help` |

Always put the link inside quotes: YouTube links contain `&`, which the terminal
would otherwise treat as a special character.

## Expected output

A single video is saved with its exact YouTube title:

```text
downloads/Me at the zoo.mp4
```

With `--audio` the same video becomes `downloads/Me at the zoo.mp3`.

A playlist gets a folder with the playlist title. Every video inside it is
numbered in playlist order and keeps its exact title:

```text
Get more creative with AI/
├── 01 - Vibe coding in Google AI Studio is changing the game.mp4
├── 02 - 3 Incredible #NanoBanana Community Builds.mp4
└── ...
```

The terminal shows yt-dlp's progress and ends with one of these lines:

```text
Done. All files were downloaded.
Finished, but some files could not be downloaded (see the errors above).
```

The second line appears when, for example, a playlist contains a private or
deleted video. The other videos are still downloaded.

## Test

```bash
python -m unittest -v
```

Expected ending:

```text
Ran 26 tests in ...

OK
```

## Common problems

- **`n challenge solving failed` / missing EJS / page needs reloading**: install
  with `python -m pip install -U -r requirements.txt`. `yt-dlp[default]` installs
  the matching challenge solver; plain `yt-dlp` omits it. The engine, local scripts,
  and Deno are checked before downloading. Refreshing the browser cannot repair
  missing Python dependencies.
- **`Sign in to confirm you're not a bot`**: log in to YouTube in a browser, close
  it, then add `--browser firefox` (or `chrome`, `edge`, `brave`, ...).
- **`No supported JavaScript runtime could be found`**: activate the environment
  where `deno` was installed, or run `python -m pip install deno`.
- **Download suddenly fails after it worked before**: YouTube changed something.
  Update with `python -m pip install -U "yt-dlp[default]"`.
- **`Got error: ... bytes read, ... more expected`, and a `.f137.mp4.part`
  (video) plus a `.f140.m4a` (audio) file are left**: the network dropped.
  YouTube sends video and audio separately and FFmpeg joins them only when both
  are complete. The program retries 10 times; if it still fails, run the same
  command again. It continues the unfinished part, joins both, and deletes the
  temporary files.
- **`Requested format is not available` with `--exact-quality`**: that exact
  quality does not exist for this video, so it was skipped (the rest of a playlist
  still downloads). Choose another `--quality` or leave out `--exact-quality`.
- **`Error: Cannot run FFmpeg at ...`**: the `--ffmpeg-location` path is wrong. Give
  the FFmpeg program itself or the folder that contains it.
- **`Error: FFmpeg exists but cannot run ... (exit code 0x...)`**: that FFmpeg is
  broken or misses a library (`0xC0000135` on Windows = missing DLL). Reinstall it,
  or point `--ffmpeg-location` to a working copy.
- **Video has no sound or the quality is low**: FFmpeg is missing. Install it and
  check with `ffmpeg -version`.

Download only videos that you own or have permission to save, and respect
YouTube's Terms of Service and the creators' copyrights.

Author: [Alireza Khajehvandi](https://alirezaaies.github.io/)
