# Documentation build guide

The tutorial is a small, chapter-based practical book in two editions:

| Edition | Ready-to-read PDF | Notes |
|---|---|---|
| English | [`english/YouTube_Downloader_Tutorial_en.pdf`](english/YouTube_Downloader_Tutorial_en.pdf) | [`english/README.md`](english/README.md) |
| Persian (فارسی) | [`persian/YouTube_Downloader_Tutorial_fa.pdf`](persian/YouTube_Downloader_Tutorial_fa.pdf) | [`persian/README.md`](persian/README.md) |

Both editions have the same seven chapters, code, commands, checkpoints,
expected output, troubleshooting, and practice ideas. Only the language and the
writing direction differ.

| Chapter | Topic |
|---|---|
| 1 | What we will build: behaviour, how it works, project structure |
| 2 | Prepare Python, FFmpeg, the project folder, the environment, and the packages |
| 3 | Every Python tool used in the program, each with a runnable example |
| 4 | `yt-dlp`: format selection, output templates, settings, and cookies |
| 5 | Write `downloader.py` step by step, then the complete listing |
| 6 | Run it for a video, a playlist, and a custom folder; the offline tests |
| 7 | Troubleshooting table and practice ideas |

## Requirements

Install a TeX distribution that includes XeLaTeX and these packages:

```text
fontspec, geometry, xcolor, graphicx, fontawesome5, eso-pic, booktabs, array,
tabularx, enumitem, listings, tcolorbox, fancyhdr, titlesec, hyperref, xepersian
```

TeX Live users may need the `texlive-xetex`, `texlive-latex-extra`, and the
Persian/Arabic language collections. MiKTeX installs missing packages when
prompted.

## Build in TeXstudio

1. Open `english/main.tex` or `persian/main.tex`.
2. Select **Options → Configure TeXstudio → Build** and set the default compiler
   to **XeLaTeX**.
3. Build `main.tex` twice so the table of contents is up to date.

Do not compile `config.tex` or a chapter by itself.

## Build from a terminal

```bash
cd docs/english        # or docs/persian
xelatex main.tex
xelatex main.tex
```

The result is `main.pdf` (ignored by Git). To publish a new version, copy it over
the named PDF in the same folder, for example
`cp main.pdf YouTube_Downloader_Tutorial_en.pdf`.

## Fonts

- English: TeX Gyre Pagella, falling back to DejaVu Serif; code in DejaVu Sans Mono.
- Persian: IRANSansX, falling back to B Nazanin and then Noto Naskh Arabic; Latin
  words in TeX Gyre Pagella; code in DejaVu Sans Mono.

Change only the font lines in `config.tex` if none of these fonts is installed.

## Source structure

Each edition contains:

- `main.tex`: cover, how-to-use page, contents, chapter order, author page;
- `config.tex`: packages, fonts, colours, social footer, code style, boxes;
- `chapters/*.tex`: one topic per chapter;
- `README.md`: edition-specific notes.

Chapters 2, 5 and 6 import the real files from `code/` (`requirements.txt`,
`downloader.py`, `test_downloader.py`). Chapter 5 prints each step with the
`\CodeLines{first}{last}` command, so the line numbers in the book are the line
numbers of the real file. **If you edit `downloader.py`, check the line ranges in
chapter 5 of both editions.**

## Troubleshooting

- **`Control sequence \g__pdf_backend_object_int already defined`** (or another
  error inside LaTeX's own files): an old copy of LaTeX core packages in your
  personal `~/texmf` folder conflicts with your TeX distribution. Build once with
  `TEXMFHOME=/nonexistent xelatex main.tex` to confirm, then update or remove the
  outdated folders in `~/texmf/tex/latex/` (for example `l3kernel`, `l3backend`,
  `base`).
- **A font is not found**: install it or change the font lines in `config.tex`.
- **Strange output after an error**: delete the helper files (`*.aux`, `*.toc`,
  `*.out`, `*.log`) and build twice again.

## Generated files

The LaTeX sources and helper files are ignored by Git (`.gitignore`). Only the two
final PDFs are published in the repository.
