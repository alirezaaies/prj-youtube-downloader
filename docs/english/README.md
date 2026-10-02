# English documentation

Read the finished book: [`YouTube_Downloader_Tutorial_en.pdf`](YouTube_Downloader_Tutorial_en.pdf).

To rebuild it, open `main.tex` in TeXstudio, select **XeLaTeX** as the compiler,
and build twice. `config.tex` contains the fonts, colours, links, code-listing
rules, and reusable boxes. The seven files in `chapters/` hold the tutorial content
and are included by `main.tex`; compile only `main.tex`.

The source prefers TeX Gyre Pagella and falls back to DejaVu Serif. It finds
`code/downloader.py` whether compilation starts in this folder or at the repository
root.

Every content page has a compact, clickable social footer; the cover provides the
same destinations in its author block. See the [documentation build guide](../README.md)
for requirements and troubleshooting.
