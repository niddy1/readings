# Readings

Personal "books I read this year" shelf. Plain static site (index.html + books/), served by GitHub Pages at ianandreu.com/readings.

## Workflow

- Commit and push straight to `main`. No branches, no PRs. Pushing to `main` is deploying to the live site, and that's fine.
- No build step; keep asset paths relative.

## Spines

Every book on the shelf is drawn from its spine image. In the `DATA` block of `index.html`, each book has:

- `spine`: path to the spine picture, e.g. `books/2187-spine-b.jpg`.
- `sr`: spine ratio, the picture's width divided by its height (0.15 means the spine is drawn 15% as wide as it is tall).

A book with no `spine` falls back to the page's generated coloured spine. Three books are in that state because they have no cover image in `books/`: Cathedral, Sisters of a Halved Heart, The Stalker.

There are three kinds of spine file in `books/`:

- `<name>-spine.jpg` with a short name (`aoi`, `woosters`, ...): real photographs. Leave these alone.
- `<id>-spine-b.jpg`: 69 designed spines, made in November 2026 by the scripts in `spinegen/`. These are what `index.html` uses.
- `<id>-spine.jpg` with a numeric id (8 files): an earlier generated attempt from `tools/`. No longer referenced by `index.html`. `tools/` is superseded by `spinegen/`.

### How the `-spine-b` images are made

They are original designs matched to each cover's colours, type and feel, not copies of the real editions' spines. Each is 1100px tall; width is `1100 * sr`. For books that had no `sr`, it was set from page count: `0.105 + 0.00021 * pages`, clamped to 0.115–0.25.

- `spinegen/lib.py`: text rendering, and `finish()`, which adds paper grain, spine-curve lighting, paperback creases and edge wear, then saves the JPEG. Wear is randomised per book (seeded by id) so no two spines share a pattern; do not add any shading that is identical on every book.
- `spinegen/eng.py`: layout engine. A spine is a background plus a top-to-bottom list of items (vertical text, horizontal text, cover crop, rule, gap, flex spacer). Text shrinks automatically to fit.
- `spinegen/first8.py`: hand-built designs for Uncle Fred in the Springtime, Middlesex, The Goldfinch, The Hitchhiker's Guide, The Overstory, White Noise, Lonesome Dove, Mrs. Dalloway.
- `spinegen/rest.py`: one spec per book for the other 61, including the shared template for the cream Wodehouse series (`ev(...)`).

Run from the repo root; with no arguments each script renders everything, or pass keys/ids to render some:

```
python3 spinegen/first8.py            # or: first8.py mid gold
python3 spinegen/rest.py              # or: rest.py 54983 11376
```

Needs Python 3 with Pillow, NumPy and OpenCV (`pip install pillow numpy opencv-python`). The fonts are bundled in `spinegen/fonts/` (only the styles actually used; licences in `spinegen/fonts/licenses/`), so it runs on any OS. To use a new font, add the file there and a key to `F` in `lib.py`. Output is deterministic: re-running gives byte-identical images.

### Rules of thumb learned along the way

- Spines display at roughly 230–290px tall, so check any new spine scaled to about 264px. Thin or light lettering fades at that size: use bold weights, dark-on-light or light-on-dark, and titles of at least ~45px in the 1100px image.
- Harry Potter and Shooting Columbo spines are type and colour only, with no character art.
- Publisher names at the foot are plain text from memory of the edition and may be wrong.
- Covers for Ring for Jeeves, Something Fresh, Uncle Fred and The Goldfinch are very small (about 125px wide), so crops from them are soft.

### Adding a spine for a new book

1. Put the cover at `books/<id>-cover.jpg` (or upload it through edit mode, below).
2. Add a spec to `spinegen/rest.py` (copy a similar book) and run `python3 spinegen/rest.py <id>`.
3. In `index.html`, set the book's `spine` to `books/<id>-spine-b.jpg` and `sr` to the image's width ÷ height.

## Edit mode (changing a cover from the page)

Open the site with `?edit` on the end, e.g. `ianandreu.com/readings/?edit`. Normal visitors never see any of this.

1. **Connect once.** The bar at top right asks for a GitHub token. Make a fine-grained token at github.com/settings/personal-access-tokens/new with *Repository access: Only select repositories → niddy1/readings* and *Permissions → Contents: Read and write*. Paste it and press Connect. It is kept in that browser's localStorage under `readings.githubToken` and sent only to api.github.com. "Disconnect" removes it.
2. **Change a cover.** Take a book off the shelf, press *Change cover…*, pick a JPEG/PNG/WebP. The page shrinks it to at most 900px tall, re-encodes it as JPEG and shows it on the shelf as a preview.
3. **Save to GitHub** makes one commit on `main` ("Change cover: <title>") containing `books/<id>-cover.jpg` and `index.html` with that book's `cover` and `cr` updated. GitHub Pages then redeploys, about a minute. *Cancel* drops the preview.

How it works (all in the `EDIT MODE` block of the script in `index.html`):

- Uses the GitHub Git Data API: read `main`, fetch the current `index.html` from GitHub (not the copy in the browser), edit only the `const DATA = ...;` line, create two blobs, a tree, a commit, then move `main`. If `main` moved in the meantime the save is rebuilt once on the new head.
- The saved `cover` path gets a `?v=<timestamp>` suffix so browsers fetch the new image instead of a cached old one. Scripts that read `cover` paths from `DATA` should strip anything after `?`; `spinegen` builds the cover path from the id, so it's unaffected.
- The spine is not changed. Re-run `spinegen` for that book if the new cover calls for a new spine.
- Constants at the top of the block: `GH_REPO`, `GH_BRANCH`, `COVER_MAX_H`, `COVER_QUALITY`.
- Covers can be added this way for books that had none (e.g. Cathedral, Sisters of a Halved Heart, The Stalker); after that, spinegen can make them a spine.
