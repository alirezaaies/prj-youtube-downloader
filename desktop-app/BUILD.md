# ساخت و به‌روزرسانی نسخهٔ دسکتاپ

## لینوکس و مک

روی لینوکس، پایتون سیستم همراه Tk لازم است:

```bash
sudo apt install python3-venv python3-tk ffmpeg
```

از پوشهٔ اصلی پروژه:

```bash
cd desktop-app
/usr/bin/python3 -m venv .venv-system  # لینوکس؛ فقط بار اول
source .venv-system/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
python app.py --check
python -m unittest -v
python -m unittest discover -s ../code -v
python build.py
```

برای بیلدهای بعدی، محیط را فعال کنید و `python build.py` را اجرا کنید. اگر
وابستگی‌ها یا `requirements.txt` تغییر کرده‌اند، پیش از بیلد دوباره دستور نصب
پیش‌نیازها را اجرا کنید. سازنده، وجود و سازگاری موتور، EJS و Deno را بررسی می‌کند.

در لینوکس مسیر `/usr/bin/python3` مهم است: اگر `python3` به کوندا اشاره کند،
ممکن است Tk بدون Xft وارد بسته شود و فونت‌ها پیکسلی یا فارسی مربع شود. سازنده
این وضعیت را بررسی می‌کند. محیط قبلی را لازم نیست حذف کنید.

روی مک، از Python همراه Tk استفاده کنید و FFmpeg را نصب کنید؛ به‌جای خط ایجاد
محیط بالا از `python3 -m venv .venv-system` استفاده کنید. هر خروجی باید روی
سیستم‌عامل هدف ساخته شود.

## ویندوز، PowerShell

Python همراه گزینهٔ Tk را نصب کنید. از پوشهٔ اصلی پروژه:

```powershell
cd desktop-app
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
.\.venv\Scripts\python.exe app.py --check
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe -m unittest discover -s ../code -v
.\.venv\Scripts\python.exe build.py
```

برای ساخت پس از تغییر کد، دستور آخر کافی است؛ در صورت تغییر وابستگی‌ها ابتدا
دستور نصب پیش‌نیازها را دوباره اجرا کنید.

## خروجی و جایگزینی نسخهٔ قبلی

خروجی در `desktop-app/dist/` ساخته می‌شود:

| سیستم | فایل قابل اشتراک |
|---|---|
| Linux | `YouTube-Downloader-linux-x86_64.tar.gz` |
| Windows | `YouTube-Downloader-windows-amd64.zip` |
| macOS | `YouTube-Downloader-macos-arm64.zip` یا نسخهٔ `x86_64` |

نام معماری به رایانهٔ سازنده بستگی دارد. فایل `.sha256` کنار خروجی برای بررسی
صحت بسته است. در لینوکس می‌توانید فایل اجرایی ساخته‌شده را نیز بررسی کنید:

```bash
"./dist/YouTube Downloader/YouTube Downloader" --check
```

باید نسخهٔ `yt-dlp 2026.10.10.233141` یا جدیدتر، نسخهٔ EJS سازگار و تأیید Deno
را ببینید. روی ویندوزِ بدون کنسول، نتیجهٔ `--check` از کد خروجی مشخص می‌شود؛
نسخه‌ها در گزارش شروع پنجره هم نمایش داده می‌شوند.

برنامهٔ قبلی را ببندید و **کل بستهٔ جدید** را در پوشه‌ای تازه باز کنید. تعویض
فقط فایل اجرایی کافی نیست؛ پوشهٔ `_internal` نیز بخشی از برنامه است. اجرای
`pip install` به‌تنهایی فایل اجرایی قبلی را به‌روز نمی‌کند.

## FFmpeg و اسکریپت‌های حل چالش

برای کیفیت بالا و تبدیل MP3، FFmpeg باید روی رایانهٔ مقصد نصب باشد یا همراه
برنامه قرار بگیرد. برای همراه‌کردن، آن را پیش از بیلد در
`desktop-app/ffmpeg/ffmpeg` (ویندوز: `ffmpeg.exe`) بگذارید؛ نکات مجوز آن در
[README](README.md#optional-bundle-ffmpeg) آمده است.

`yt-dlp[default]` را به `yt-dlp` ساده تغییر ندهید؛ بخش `[default]` اسکریپت‌های
سازگار `yt-dlp-ejs` را نصب می‌کند. Deno به‌تنهایی کافی نیست. این پروژه اسکریپت‌ها
را محلی بسته‌بندی می‌کند و برای دانلود معمول نیازی به دریافت کد اجرایی از GitHub
در زمان اجرا ندارد. جزئیات در [راهنمای رسمی EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS).
