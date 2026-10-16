"""Display-only helpers: monotonic download progress and Persian text for Tk 8."""

import unicodedata

import arabic_reshaper
from bidi.algorithm import get_display


def display_text(text):
    """Shape and order RTL runs for Tk's LTR text widget, without changing files."""
    if not any(unicodedata.bidirectional(char) in ("R", "AL") for char in text):
        return text
    return "\n".join(get_display(arabic_reshaper.reshape(line), base_dir="L")
                     for line in text.split("\n"))


class DownloadProgress:
    """Combine the selected streams; estimates/retries cannot move a video back.

    A fixed share is assigned to each selected stream before transfer. Use byte
    sizes if all are known, otherwise equal shares. Fragment counts are more
    reliable than fluctuating HLS byte estimates. Reserve 2% for postprocessing.
    """

    def __init__(self):
        self.item = None
        self.fractions = {}
        self.weights = {}
        self.percent = None
        self.finished = set()

    def begin(self, info):
        item = (info.get("extractor_key"), info.get("id"), info.get("playlist_index"))
        if self.item == item:
            return
        self.item = item
        formats = info.get("requested_formats") or [info]
        keys = [str(fmt.get("format_id") or "media") for fmt in formats]
        sizes = [fmt.get("filesize") or fmt.get("filesize_approx") or 0 for fmt in formats]
        shares = sizes if all(size > 0 for size in sizes) else [1] * len(formats)
        self.weights = dict(zip(keys, (size / sum(shares) for size in shares)))
        self.fractions = dict.fromkeys(keys, 0.0)
        self.percent = None
        self.finished = set()

    def update(self, status):
        info = status.get("info_dict") or {}
        if self.item is None:
            self.begin(info)
        key = str(info.get("format_id") or "media")
        if key not in self.fractions:
            # Single-stream downloads may report a more specific format id.
            if len(self.fractions) == 1 and not any(self.fractions.values()):
                old = next(iter(self.fractions))
                self.fractions[key] = self.fractions.pop(old)
                self.weights[key] = self.weights.pop(old)
            else:
                return None
        if status.get("status") == "finished":
            fraction = 1.0
            self.finished.add(key)
        elif status.get("fragment_count"):
            fraction = (status.get("fragment_index") or 0) / status["fragment_count"]
        else:
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            fraction = (status.get("downloaded_bytes") or 0) / total if total else None
        if fraction is not None:
            self.fractions[key] = max(self.fractions[key], min(1.0, max(0.0, fraction)))
            value = 98 * sum(self.weights[k] * self.fractions[k] for k in self.weights)
            self.percent = max(self.percent or 0, value)
        return {
            "percent": self.percent,
            "speed": status.get("speed"),
            "eta": status.get("eta"),
            "index": info.get("playlist_index"),
            "count": info.get("n_entries") or info.get("playlist_count"),
            "part": list(self.weights).index(key) + 1,
            "parts": len(self.weights),
            "transferred": all(key in self.finished for key in self.fractions),
        }
