"""YouTube Downloader: a desktop window for the program in ../code/downloader.py.

Run from source:   python app.py
Build an app:      python build.py      (see README.md)
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# --- Where the program and its bundled files are -----------------------------
APP_FOLDER = Path(__file__).resolve().parent
# In a built app, PyInstaller unpacks bundled files into sys._MEIPASS.
RESOURCES = Path(getattr(sys, "_MEIPASS", APP_FOLDER))

# Reuse the tested command-line program (code/downloader.py) without changing it.
sys.path.insert(0, str(APP_FOLDER.parent / "code"))
import downloader  # noqa: E402  (must come after the path is added)
from yt_dlp import YoutubeDL  # noqa: E402
from yt_dlp.utils import DownloadCancelled  # noqa: E402

# A built window app has no console: send stray prints to "nowhere".
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# --- Settings and look ------------------------------------------------------
APP_NAME = "YouTube Downloader"
DEFAULT_FOLDER = Path.home() / "Downloads" / APP_NAME
SETTINGS_FILE = Path.home() / ".youtube-downloader.json"
QUALITIES = ["2160", "1440", "1080", "720", "480", "360", "240", "144"]
BROWSERS = ["None", "firefox", "chrome", "edge", "brave", "chromium",
            "opera", "vivaldi", "safari"]
EXE = ".exe" if sys.platform == "win32" else ""

ACCENT, ACCENT_DARK = "#B3261E", "#8C1D18"   # the red of the tutorial books
BG, CARD = "#F4F5F7", "#FFFFFF"              # window and panel backgrounds
TEXT, MUTED = "#243447", "#5F6B7A"           # main and secondary text
GREEN, ORANGE, RED = "#1B7F5C", "#B26A00", "#B3261E"


# --- Small helpers (no window needed, so they are easy to test) -------------
def bundled_tool(name):
    """Return the path of a program shipped inside the app, or None."""
    path = RESOURCES / "bin" / f"{name}{EXE}"
    return str(path) if path.is_file() else None


def find_ffmpeg(chosen=""):
    """The FFmpeg to use: the user's choice, the bundled one, or the system one."""
    return chosen or bundled_tool("ffmpeg") or shutil.which("ffmpeg")


def javascript_runtime():
    """Describe the JavaScript runtime that YouTube downloads need (deno)."""
    if bundled_tool("deno"):
        return "built in"
    if shutil.which("deno"):
        return "deno from this computer"
    return ""


def clean_link(text):
    """Remove spaces and the backslashes that some terminals add to links."""
    return text.strip().replace("\\", "")


def human_size(num_bytes):
    """1536000 -> '1.5 MB'."""
    size = float(num_bytes or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


def progress_text(info):
    """Build a short status line from the values the progress hook collected."""
    parts = []
    if info.get("count"):
        parts.append(f"Item {info['index']} of {info['count']}")
    percent = info.get("percent")
    parts.append(f"Downloading {percent:.0f}%" if percent is not None else "Downloading")
    if info.get("speed"):
        parts.append(f"{human_size(info['speed'])}/s")
    if info.get("eta") is not None:
        minutes, seconds = divmod(int(info["eta"]), 60)
        parts.append(f"{minutes}:{seconds:02d} left")
    return "  ·  ".join(parts)


def readable_log_line(message):
    """Turn a technical yt-dlp line into a short one, or return None to hide it."""
    if message.startswith("[download] Destination: "):
        return "Saving " + Path(message.split(": ", 1)[1]).name
    if message.startswith("[Merger] Merging formats into "):
        name = Path(message.split(" into ", 1)[1].strip('"')).name
        return "Joining video and audio into " + name
    if message.startswith("[ExtractAudio] Destination: "):
        return "Converting to MP3: " + Path(message.split(": ", 1)[1]).name
    if message.startswith(("[download] Downloading playlist", "[download] Downloading item",
                           "[download] Finished downloading playlist")):
        return message.removeprefix("[download] ")
    if "has already been downloaded" in message:
        return "Already downloaded: " + Path(message.split("] ", 1)[1].split(
            " has already")[0]).name
    return None  # other lines (web pages, players, temporary files) are hidden


def friendly_error(message):
    """Add a plain-English hint to the most common yt-dlp error messages."""
    hints = {
        "Sign in to confirm": "YouTube asks for a sign-in. Choose your browser under "
                              "'Browser login' (you must be signed in to YouTube "
                              "there), close that browser, and try again.",
        "Requested format is not available": "This exact quality does not exist for "
                                             "this video. Choose another quality or "
                                             "untick 'Exactly this quality'.",
        "Private video": "This video is private and was skipped.",
        "Video unavailable": "This video is unavailable and was skipped.",
        "This video is unavailable": "This video is unavailable and was skipped.",
        "Unsupported URL": "This is not a YouTube video or playlist link.",
        "Failed to resolve": "No internet connection, or the site cannot be reached.",
        "Could not copy": "Close the selected browser completely and try again.",
    }
    for key, hint in hints.items():
        if key in message:
            return hint
    return ""


def load_settings():
    """Read the choices saved last time; an unreadable file means 'no settings'."""
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    """Remember the user's choices for the next start (failures are harmless)."""
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass


def open_folder(path):
    """Show a folder in the system's file manager."""
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606  (opens Explorer, runs no command)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


# --- The download itself (runs in a background thread) ----------------------
class QueueLogger:
    """Receives yt-dlp's messages and passes them on to the window."""

    def __init__(self, events):
        self.events = events

    def debug(self, message):
        line = readable_log_line(message)  # None for technical details
        if line:
            self.events.put(("log", line, "info"))

    def info(self, message):
        self.debug(message)

    def warning(self, message):
        self.events.put(("log", f"Warning: {message}", "warning"))

    def error(self, message):
        self.events.put(("log", message, "error"))
        hint = friendly_error(message)
        if hint:
            self.events.put(("log", f"Tip: {hint}", "hint"))


def run_download(job, events, cancel):
    """Download one link with the settings in job; report through events.

    The window must only be changed by the main thread, so this function never
    touches it: it puts small messages into the events queue instead.
    """

    def on_progress(status):
        if cancel.is_set():  # the Cancel button was pressed
            raise DownloadCancelled("Cancelled by the user")
        if status["status"] == "downloading":
            done = status.get("downloaded_bytes") or 0
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            video = status.get("info_dict", {})
            events.put(("progress", {
                "percent": done * 100 / total if total else None,
                "speed": status.get("speed"),
                "eta": status.get("eta"),
                "index": video.get("playlist_index"),
                "count": video.get("n_entries") or video.get("playlist_count"),
            }))

    def on_postprocess(status):
        if status["status"] == "started":
            names = {"Merger": "Joining video and audio...",
                     "FFmpegExtractAudio": "Converting to MP3..."}
            text = names.get(status.get("postprocessor"))
            if text:
                events.put(("status", text))

    try:
        # Stop early, with a clear message, if the chosen FFmpeg cannot run.
        downloader.check_ffmpeg(job["ffmpeg"])
        options = downloader.build_options(
            job["url"], job["folder"], job["browser"], job["audio"],
            job["ffmpeg"], job["quality"], job["exact"])
        options.update({
            "logger": QueueLogger(events),         # messages go to the window
            "progress_hooks": [on_progress],       # percent, speed, time left
            "postprocessor_hooks": [on_postprocess],
            "noprogress": True,                    # no text progress bar
        })
        deno = bundled_tool("deno")
        if deno:
            # The JavaScript runtime shipped with the app (YouTube needs one).
            options["js_runtimes"] = {"deno": {"path": deno}}
        Path(job["folder"]).mkdir(parents=True, exist_ok=True)
        with YoutubeDL(options) as ydl:
            result = ydl.download([job["url"]])
        events.put(("done", "ok" if result == 0 else "partial", ""))
    except DownloadCancelled:
        events.put(("done", "cancelled", ""))
    except RuntimeError as exc:  # raised by check_ffmpeg
        events.put(("done", "error", str(exc)))
    except Exception as exc:  # anything unexpected: report it, never crash
        events.put(("done", "error", f"{type(exc).__name__}: {exc}"))


# --- The window --------------------------------------------------------------
class DownloaderWindow:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()      # messages from the download thread
        self.cancel = threading.Event()  # set when Cancel is pressed
        self.worker = None               # the running download thread
        settings = load_settings()

        # Variables connected to the widgets (Tk updates them automatically).
        self.url = tk.StringVar()
        self.folder = tk.StringVar(value=settings.get("folder", str(DEFAULT_FOLDER)))
        self.mode = tk.StringVar(value=settings.get("mode", "video"))
        self.quality = tk.StringVar(value=settings.get("quality", "720"))
        self.exact = tk.BooleanVar(value=settings.get("exact", False))
        self.browser = tk.StringVar(value=settings.get("browser", "None"))
        self.ffmpeg_choice = settings.get("ffmpeg", "")
        self.status = tk.StringVar(value="Paste a link and press Download.")

        self.build_style()
        self.build_layout()
        self.refresh_ffmpeg_label()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.poll_events)

    def build_style(self):
        """A clean, light theme based on ttk's portable 'clam' theme."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        self.root.configure(background=BG)
        style.configure(".", background=BG, foreground=TEXT)
        style.configure("Card.TFrame", background=CARD)
        style.configure("Card.TLabel", background=CARD, foreground=TEXT)
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED)
        style.configure("Header.TFrame", background=ACCENT)
        style.configure("Title.TLabel", background=ACCENT, foreground="white",
                        font=("TkDefaultFont", 17, "bold"))
        style.configure("Subtitle.TLabel", background=ACCENT, foreground="#F6D5D2")
        style.configure("Footer.TLabel", background=BG, foreground=MUTED)
        style.configure("Card.TRadiobutton", background=CARD)
        style.configure("Card.TCheckbutton", background=CARD)
        style.map("Card.TRadiobutton", background=[("active", CARD)])
        style.map("Card.TCheckbutton", background=[("active", CARD)])
        style.configure("TEntry", fieldbackground="white", padding=5)
        style.configure("TCombobox", padding=4)
        style.configure("TButton", padding=(12, 6))
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        bordercolor=ACCENT, font=("TkDefaultFont", 10, "bold"),
                        padding=(22, 8))
        style.map("Accent.TButton",
                  background=[("disabled", "#D9A5A1"), ("active", ACCENT_DARK)],
                  foreground=[("disabled", "white")])
        style.configure("Horizontal.TProgressbar", background=ACCENT,
                        troughcolor="#E6E8EB", bordercolor="#E6E8EB",
                        lightcolor=ACCENT, darkcolor=ACCENT)

    def build_layout(self):
        """Create all widgets: header, form, buttons, progress, log, footer."""
        self.root.title(APP_NAME)
        self.root.minsize(640, 600)
        # Rows: 0 header, 1 form, 2 buttons, 3 progress, 4 log, 5 footer.
        # Only the log (row 4) grows when the window is made larger.
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        header = ttk.Frame(self.root, style="Header.TFrame", padding=(22, 16))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Save a YouTube video, a whole playlist, or just "
                  "the sound.", style="Subtitle.TLabel").pack(anchor="w")

        form = ttk.Frame(self.root, style="Card.TFrame", padding=18)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(16, 8))
        form.columnconfigure(1, weight=1)

        def label(row, text):
            ttk.Label(form, text=text, style="Card.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=6)

        # Row 0: the link.
        label(0, "Video or playlist link")
        self.url_entry = ttk.Entry(form, textvariable=self.url)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=6)
        self.paste_button = ttk.Button(form, text="Paste", command=self.paste_link)
        self.paste_button.grid(row=0, column=2, padx=(8, 0))

        # Row 1: the save folder.
        label(1, "Save to")
        self.folder_entry = ttk.Entry(form, textvariable=self.folder)
        self.folder_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.browse_button = ttk.Button(form, text="Browse...",
                                        command=self.choose_folder)
        self.browse_button.grid(row=1, column=2, padx=(8, 0))

        # Row 2: video or audio only.
        label(2, "Download")
        modes = ttk.Frame(form, style="Card.TFrame")
        modes.grid(row=2, column=1, columnspan=2, sticky="w")
        self.video_radio = ttk.Radiobutton(
            modes, text="Video (MP4)", value="video", variable=self.mode,
            style="Card.TRadiobutton", command=self.update_quality_state)
        self.audio_radio = ttk.Radiobutton(
            modes, text="Audio only (MP3)", value="audio", variable=self.mode,
            style="Card.TRadiobutton", command=self.update_quality_state)
        self.video_radio.pack(side="left", padx=(0, 18))
        self.audio_radio.pack(side="left")

        # Row 3: quality.
        label(3, "Quality")
        quality_row = ttk.Frame(form, style="Card.TFrame")
        quality_row.grid(row=3, column=1, columnspan=2, sticky="w", pady=6)
        self.quality_box = ttk.Combobox(quality_row, textvariable=self.quality,
                                        values=QUALITIES, width=7, state="readonly")
        self.quality_box.pack(side="left")
        ttk.Label(quality_row, text="p", style="Card.TLabel").pack(side="left")
        self.exact_check = ttk.Checkbutton(
            quality_row, text="Exactly this quality (skip the video if missing)",
            variable=self.exact, style="Card.TCheckbutton")
        self.exact_check.pack(side="left", padx=(16, 0))

        # Row 4: optional browser login.
        label(4, "Browser login")
        browser_row = ttk.Frame(form, style="Card.TFrame")
        browser_row.grid(row=4, column=1, columnspan=2, sticky="w", pady=6)
        self.browser_box = ttk.Combobox(browser_row, textvariable=self.browser,
                                        values=BROWSERS, width=10, state="readonly")
        self.browser_box.pack(side="left")
        ttk.Label(browser_row, text="Only if YouTube asks you to sign in.",
                  style="Muted.TLabel").pack(side="left", padx=(12, 0))

        # Row 5: FFmpeg status.
        label(5, "FFmpeg")
        ffmpeg_row = ttk.Frame(form, style="Card.TFrame")
        ffmpeg_row.grid(row=5, column=1, columnspan=2, sticky="ew", pady=6)
        self.ffmpeg_label = tk.Label(ffmpeg_row, bg=CARD, anchor="w")
        self.ffmpeg_label.pack(side="left", fill="x", expand=True)
        self.ffmpeg_auto = ttk.Button(ffmpeg_row, text="Automatic",
                                      command=self.reset_ffmpeg)
        self.ffmpeg_auto.pack(side="right", padx=(8, 0))
        self.ffmpeg_button = ttk.Button(ffmpeg_row, text="Choose...",
                                        command=self.choose_ffmpeg)
        self.ffmpeg_button.pack(side="right")

        # Buttons.
        buttons = ttk.Frame(self.root, padding=(16, 4))
        buttons.grid(row=2, column=0, sticky="ew")
        self.download_button = ttk.Button(buttons, text="Download",
                                          style="Accent.TButton",
                                          command=self.start_download)
        self.download_button.pack(side="left")
        self.cancel_button = ttk.Button(buttons, text="Cancel", state="disabled",
                                        command=self.cancel_download)
        self.cancel_button.pack(side="left", padx=8)
        ttk.Button(buttons, text="Open folder",
                   command=lambda: open_folder(Path(self.folder.get()).expanduser())
                   ).pack(side="right")

        # Progress bar and status line.
        progress = ttk.Frame(self.root, padding=(16, 8, 16, 0))
        progress.grid(row=3, column=0, sticky="ew")
        progress.columnconfigure(0, weight=1)
        self.bar = ttk.Progressbar(progress, maximum=100)
        self.bar.grid(row=0, column=0, sticky="ew")
        self.status_label = tk.Label(progress, textvariable=self.status, bg=BG,
                                     fg=MUTED, anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        # The log: everything that happened, with errors in red.
        log_frame = ttk.Frame(self.root, padding=(16, 8))
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=8, wrap="word", state="disabled",
                           relief="flat", bg=CARD, fg=MUTED, padx=10, pady=8,
                           font=("TkFixedFont", 9), highlightthickness=1,
                           highlightbackground="#E1E4E8")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.tag_configure("error", foreground=RED)
        self.log.tag_configure("warning", foreground=ORANGE)
        self.log.tag_configure("hint", foreground=TEXT, font=("TkDefaultFont", 9, "bold"))
        self.log.tag_configure("ok", foreground=GREEN, font=("TkDefaultFont", 9, "bold"))


        ttk.Label(self.root, text="Download only videos you own or have permission "
                  "to save.", style="Footer.TLabel", padding=(16, 0, 16, 10)
                  ).grid(row=5, column=0, sticky="w")

        self.inputs = [self.url_entry, self.paste_button, self.folder_entry,
                       self.browse_button, self.video_radio, self.audio_radio,
                       self.quality_box, self.exact_check, self.browser_box,
                       self.ffmpeg_button, self.ffmpeg_auto]
        self.update_quality_state()
        self.url_entry.focus_set()
        self.write_startup_check()

    def write_startup_check(self):
        """Tell the user at once whether the needed helper programs exist."""
        from yt_dlp.version import __version__ as yt_dlp_version
        runtime = javascript_runtime()
        if runtime:
            self.write_log(f"Ready. yt-dlp {yt_dlp_version}, JavaScript runtime: "
                           f"{runtime}.", "ok")
        else:
            self.write_log("Warning: no JavaScript runtime (deno) was found, so "
                           "YouTube downloads will fail. Install deno from "
                           "https://deno.com or use the built app.", "warning")

    # --- Small actions -----------------------------------------------------
    def paste_link(self):
        try:
            self.url.set(clean_link(self.root.clipboard_get()))
        except tk.TclError:  # the clipboard is empty or holds no text
            self.status.set("The clipboard is empty. Copy a YouTube link first.")

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder.get() or Path.home())
        if folder:
            self.folder.set(folder)

    def choose_ffmpeg(self):
        path = filedialog.askopenfilename(title="Choose the FFmpeg program")
        if path:
            self.ffmpeg_choice = path
            self.refresh_ffmpeg_label()

    def reset_ffmpeg(self):
        self.ffmpeg_choice = ""
        self.refresh_ffmpeg_label()

    def refresh_ffmpeg_label(self):
        """Show which FFmpeg will be used, or explain what happens without it."""
        path = find_ffmpeg(self.ffmpeg_choice)
        if path:
            self.ffmpeg_label.configure(text=f"Found: {path}", fg=GREEN)
        else:
            self.ffmpeg_label.configure(
                text="Not found: videos up to about 360p, audio as M4A.", fg=ORANGE)

    def update_quality_state(self):
        """Quality has no meaning for audio only, so disable it there."""
        busy = self.worker is not None
        state = "disabled" if self.mode.get() == "audio" or busy else "readonly"
        self.quality_box.configure(state=state)
        self.exact_check.configure(state="disabled" if state == "disabled" else "normal")

    def write_log(self, text, tag="info"):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_busy(self, busy):
        """Lock the form during a download, unlock it afterwards."""
        for widget in self.inputs:
            widget.configure(state="disabled" if busy else "normal")
        for box in (self.quality_box, self.browser_box):
            if not busy:
                box.configure(state="readonly")
        self.download_button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self.update_quality_state()

    # --- Download control --------------------------------------------------
    def start_download(self):
        url = clean_link(self.url.get())
        if not url:
            messagebox.showinfo(APP_NAME, "Please paste a YouTube video or playlist "
                                "link first.")
            return
        if not url.startswith(("http://", "https://")):
            messagebox.showerror(APP_NAME, "This does not look like a link.\n\n"
                                 "A YouTube link starts with https://")
            return
        folder = Path(self.folder.get().strip() or DEFAULT_FOLDER).expanduser()
        job = {
            "url": url,
            "folder": folder,
            "audio": self.mode.get() == "audio",
            "quality": int(self.quality.get()),
            "exact": self.exact.get(),
            "browser": None if self.browser.get() == "None" else self.browser.get(),
            "ffmpeg": find_ffmpeg(self.ffmpeg_choice),
        }
        save_settings({"folder": str(folder), "mode": self.mode.get(),
                       "quality": self.quality.get(), "exact": self.exact.get(),
                       "browser": self.browser.get(), "ffmpeg": self.ffmpeg_choice})

        self.url.set(url)
        self.cancel.clear()
        self.bar.configure(value=0)
        self.status.set("Starting...")
        self.status_label.configure(fg=MUTED)
        self.write_log(f"--- {url}")
        self.write_log(f"Saving to: {folder}")
        self.worker = threading.Thread(target=run_download, daemon=True,
                                       args=(job, self.events, self.cancel))
        self.set_busy(True)
        self.worker.start()

    def cancel_download(self):
        self.cancel.set()
        self.cancel_button.configure(state="disabled")
        self.status.set("Cancelling... (stops at the next step)")

    def poll_events(self):
        """Every 100 ms: show what the download thread reported."""
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self.write_log(event[1], event[2])
                elif kind == "progress":
                    info = event[1]
                    if info["percent"] is not None:
                        self.bar.configure(value=info["percent"])
                    self.status.set(progress_text(info))
                elif kind == "status":
                    self.status.set(event[1])
                elif kind == "done":
                    self.finish(event[1], event[2])
        except queue.Empty:
            pass
        self.root.after(100, self.poll_events)

    def finish(self, result, details):
        """Show the final result clearly and unlock the form."""
        self.worker = None
        self.set_busy(False)
        messages = {
            "ok": ("Done. All files were downloaded.", GREEN, "ok"),
            "partial": ("Finished, but some files could not be downloaded. "
                        "See the red lines in the log.", ORANGE, "warning"),
            "cancelled": ("Cancelled. Press Download again to continue later.",
                          ORANGE, "warning"),
            "error": ("Stopped because of an error. See the log.", RED, "error"),
        }
        text, color, tag = messages[result]
        if result == "ok":
            self.bar.configure(value=100)
        self.status.set(text)
        self.status_label.configure(fg=color)
        self.write_log(text, tag)
        if result == "error":
            self.write_log(details, "error")
            messagebox.showerror(APP_NAME, details)

    def on_close(self):
        if self.worker and not messagebox.askyesno(
                APP_NAME, "A download is running. Stop it and quit?"):
            return
        self.cancel.set()
        self.root.destroy()


def main():
    if sys.platform == "win32":
        try:  # sharp text on high-resolution Windows screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    icon = RESOURCES / "assets" / "icon.png"
    if icon.is_file():
        root.iconphoto(True, tk.PhotoImage(file=str(icon)))
    DownloaderWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
