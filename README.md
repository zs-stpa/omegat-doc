# omegat-doc

Presentation "Contributions to OmegaT since summer 2026" (German, Esperanto,
English) and its generator. Not an official OmegaT project document.

The finished deck is attached to each [release](../../releases) as one
self-contained HTML file: open it in a browser, turn pages with the arrow
keys, space or a click; switch the language with DE · EO · EN or the keys
1, 2, 3. Hover tiles and charts for details.

Build it yourself (Python 3 standard library only):

    python3 make_deck.py [version]      # writes dist/OmegaT-Beitraege-Sommer-2026-<version>.html

- `deck_content.py`: all texts, in German, Esperanto and English
- `make_deck.py`: layout and rendering (SVG per slide, one HTML file)
- `assets/`: images (SVG, lossless WebP), clips (H.264, silent), language pack figures
- `tools/`: how the assets were prepared from the original recordings and screenshots
  - `render_numerals.py`: glyph images of slide 6 (free Noto fonts, InupiaqNumbers for Kaktovik; fetched into `.fonts-cache/`)
  - `check_numerals.py`: confirms OmegaT's numeral parser reads every sample of slide 6 as claimed (`OMEGAT_HOME=… python3 tools/check_numerals.py`)

A pushed tag `v*` builds the deck and publishes it as a release.
