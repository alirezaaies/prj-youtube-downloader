# Build a YouTube Downloader with Python

A small, practical, bilingual tutorial project. It takes a beginner from an empty
folder to a working program that downloads **one YouTube video** or a **whole
playlist**, using the exact video titles. The same hands-on book is available in
English and Persian.

Created by **[Alireza Khajehvandi](https://alirezaaies.github.io/)**.

📘 **Read the tutorial:** [English PDF](docs/english/YouTube_Downloader_Tutorial_en.pdf) ·
[Persian PDF (فارسی)](docs/persian/YouTube_Downloader_Tutorial_fa.pdf)

## What the program does

- **One video link** → saves the video, named with its exact title:
  `Me at the zoo.mp4`.
- **A playlist link** → creates a folder named after the playlist and saves every
  video in it, numbered in playlist order: `01 - First video.mp4`,
  `02 - Second video.mp4`, …
- **Save folder** → `-o FOLDER` chooses where files go. Without it, files are saved
  in `code/downloads/` (next to `downloader.py`), wherever you start it from. Git
  ignores that folder, so videos never end up in the repository.
- **Only the sound** → `--audio` saves just the audio as an `.mp3` (192 kbit/s),
  for single videos and whole playlists.
- **Best quality that plays everywhere** → best video and audio joined into one
  `.mp4` (H.264 + AAC, usually 1080p).
- **Friendly and robust** → asks for the link if you forget it, skips private or
  deleted playlist videos, retries 10 times after a network drop, accepts links that
  zsh pasted with `\?` and `\=`, and stops politely with `Ctrl+C` so the same command
  can continue later.

The whole program is one 119-line file built on the
[`yt-dlp`](https://github.com/yt-dlp/yt-dlp) library.

## Start in five minutes

You need Python 3.10 or newer, [FFmpeg](https://ffmpeg.org/download.html), and an
internet connection.

**1. Install FFmpeg** (joins the best video and audio into one file):

```bash
sudo apt install ffmpeg        # Ubuntu / Debian
brew install ffmpeg            # macOS
winget install Gyan.FFmpeg     # Windows PowerShell
```

**2. Get the code and install the packages:**

```bash
git clone https://github.com/alirezaaies/prj-youtube-downloader.git
cd prj-youtube-downloader/code
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

With Conda instead of `venv`:

```bash
conda create -n ytdl python=3.12 -y
conda activate ytdl
python -m pip install -r requirements.txt
```

**3. Download:**

```bash
python downloader.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

Expected ending of the output:

```text
Saving to: /.../prj-youtube-downloader/code/downloads
...
Done. All files were downloaded.
```

`Me at the zoo.mp4` is now in `code/downloads/`.

## Usage

| Goal | Command |
|---|---|
| One video | `python downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"` |
| Whole playlist | `python downloader.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"` |
| Save in another folder | `python downloader.py "LINK" -o ~/Videos` |
| Only the sound (MP3) | `python downloader.py "LINK" --audio` |
| Stop now, continue later | press `Ctrl+C`, then run the same command again |
| YouTube asks you to sign in | `python downloader.py "LINK" --browser firefox` |
| Let the program ask for the link | `python downloader.py` |
| Help | `python downloader.py --help` |

Always put the link in quotes. A playlist download produces:

```text
Get more creative with AI/
├── 01 - Vibe coding in Google AI Studio is changing the game.mp4
├── 02 - 3 Incredible #NanoBanana Community Builds.mp4
└── ...
```

Run the nine offline tests (no internet needed) from the `code` folder:

```bash
python -m unittest -v
```

## Common problems

| Problem | Fix |
|---|---|
| `Sign in to confirm you're not a bot` | Sign in to YouTube in a browser, close it, add `--browser firefox` (or `chrome`, `edge`, …). A VPN change can also help. |
| `No supported JavaScript runtime could be found` | Activate the environment; `deno` comes from `requirements.txt` (`python -m pip install deno`). |
| `Got error: ... bytes read, ... more expected`; a `.f137.mp4.part` (video) and a `.f140.m4a` (audio) file are left | The network dropped. The program retries 10 times; if it still fails, run the **same command** again: it continues the unfinished part and joins video and audio. |
| No sound or low quality | FFmpeg is missing; check `ffmpeg -version`. |
| Worked before, now fails | YouTube changed something: `python -m pip install -U "yt-dlp[default]"`. |
| A whole playlist starts instead of one video | Remove `&list=...` from the link. |

The tutorial's chapter 8 has the full troubleshooting table, and chapter 7 explains how
the network-drop and zsh problems were found and fixed.

## Repository map

```text
prj-youtube-downloader/
├── code/
│   ├── downloader.py           # the complete, commented program
│   ├── requirements.txt        # yt-dlp[default] and deno
│   ├── test_downloader.py      # nine offline tests
│   ├── README.md               # code-specific guide
│   └── downloads/              # your downloads (created automatically, ignored by Git)
├── docs/
│   ├── english/                # English book (XeLaTeX) + PDF
│   ├── persian/                # Persian book (XePersian, RTL) + PDF
│   └── README.md               # how to build the books
├── .gitignore                  # ignores videos, environments, LaTeX helpers
├── LICENSE
└── README.md
```

## The tutorial books

Eight chapters, each with a goal, explanations, runnable examples, checkpoints, and
expected results:

1. What we will build
2. Prepare Python, FFmpeg, and the project
3. The Python tools we use (modules, functions, dictionaries, `pathlib`, `argparse`, …)
4. Meet `yt-dlp` (formats, output templates, post-processors, cookies)
5. Write the program step by step
6. Run and test the program (videos, playlists, audio, Ctrl+C)
7. Lessons from real use: how bugs were found and fixed, and why
8. Troubleshooting and next steps

See the [documentation build guide](docs/README.md) to rebuild the PDFs with XeLaTeX.

## Responsible use

Download only videos that you own, that are licensed for it, or that you have
permission to save. Respect YouTube's Terms of Service and creators' copyrights.
This project teaches Python; how you use it is your responsibility.

---

## فارسی — معرفی و شروع سریع

این مخزن یک پروژهٔ آموزشی و عملی پایتون به دو زبان فارسی و انگلیسی است. برنامهٔ
`downloader.py` با کتابخانهٔ `yt-dlp` ساخته شده است و:

- با **پیوند یک ویدیو**، همان ویدیو را با عنوان دقیقش ذخیره می‌کند؛
- با **پیوند یک پلی‌لیست**، پوشه‌ای به نام پلی‌لیست می‌سازد و همهٔ ویدیوها را با
  عنوان دقیق و شماره‌گذاری به ترتیب پلی‌لیست در آن ذخیره می‌کند؛
- با گزینهٔ `-o` در پوشهٔ دلخواه شما ذخیره می‌کند و اگر پوشه‌ای ندهید، فایل‌ها را
  در پوشهٔ `code/downloads/` ذخیره می‌کند که گیت آن را نادیده می‌گیرد؛
- با گزینهٔ `--audio` فقط صدا را به شکل فایل `mp3` ذخیره می‌کند؛
- پس از قطع شبکه تا ۱۰ بار دوباره تلاش می‌کند و با `Ctrl+C` مؤدبانه متوقف می‌شود تا
  همان دستور بعداً ادامه دهد؛
- بهترین تصویر و صدا را در یک فایل `mp4` ترکیب می‌کند که همه‌جا پخش می‌شود.

📘 **کتاب آموزشی:** [نسخهٔ فارسی](docs/persian/YouTube_Downloader_Tutorial_fa.pdf) ·
[نسخهٔ انگلیسی](docs/english/YouTube_Downloader_Tutorial_en.pdf)

### مراحل اجرا

۱. پایتون ۳٫۱۰ یا جدیدتر و `FFmpeg` را نصب کنید (دستورهای نصب در بخش انگلیسی بالا
آمده‌اند).

۲. مخزن را دریافت کنید، وارد پوشهٔ `code` شوید، یک محیط مجازی بسازید و بسته‌ها را
نصب کنید:

```bash
git clone https://github.com/alirezaaies/prj-youtube-downloader.git
cd prj-youtube-downloader/code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

۳. دانلود کنید:

```bash
python downloader.py "پیوند ویدیو یا پلی‌لیست"
python downloader.py "پیوند" -o ~/Videos          # ذخیره در پوشهٔ دلخواه
python downloader.py "پیوند" --audio              # فقط صدا (mp3)
python downloader.py "پیوند" --browser firefox    # وقتی یوتیوب ورود می‌خواهد
python downloader.py                              # برنامه پیوند را می‌پرسد
```

در پایان، پیام `Done. All files were downloaded.` نمایش داده می‌شود. پیوند را همیشه
داخل گیومه بنویسید. آزمون‌های آفلاین را با `python -m unittest -v` اجرا کنید.

اگر پیام `Sign in to confirm you're not a bot` را دیدید، در مرورگر وارد یوتیوب شوید،
مرورگر را ببندید و گزینهٔ `--browser firefox` (یا نام مرورگر خودتان) را اضافه کنید.
اگر دانلود با خطای `Got error: ... bytes read` قطع شد و فقط فایل تصویر نیمه‌کاره و فایل صدا ماند، همان دستور را دوباره اجرا کنید تا دانلود ادامه یابد و تصویر و صدا ترکیب شوند.
اگر برنامه‌ای که قبلاً کار می‌کرد ناگهان خطا داد، `yt-dlp` را با دستور
`python -m pip install -U "yt-dlp[default]"` به‌روز کنید.

کتاب آموزشی در هشت فصل، از نصب پایتون تا نوشتن خط‌به‌خط کد، اجرا، آزمون و رفع
اشکال را با مثال توضیح می‌دهد. فقط ویدیوهایی را دانلود کنید که اجازهٔ ذخیرهٔ آن‌ها
را دارید و قوانین یوتیوب و حق نشر سازندگان را رعایت کنید.

---

## Questions and contributions

If a step is unclear or behaves differently on your system, open a GitHub issue
with your operating system, Python version, command, and the complete error
message. Remove private information first. Focused pull requests that keep both
language editions synchronized are welcome.

If this project helped you, star the repository and share what you built.

## Connect with Alireza Khajehvandi

- [LinkedIn](https://www.linkedin.com/in/alirezakhajehvandi)
- [YouTube](https://www.youtube.com/@AlirezaAIES)
- [Telegram channel](https://t.me/AlirezaAIES)
- [Instagram](https://www.instagram.com/alireza.aies)
- [GitHub](https://github.com/alirezaaies)
- [Personal website and portfolio](https://alirezaaies.github.io/)

## License

This project is available under the [MIT License](LICENSE).
