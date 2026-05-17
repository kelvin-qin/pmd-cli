# pmd — Print Markdown

> Terminal Markdown renderer. Zero dependencies. One command.

**pmd** renders Markdown files directly in your terminal with ANSI colors and Unicode box-drawing characters. No browser, no GUI, no npm install. Just Python 3.9+ and `pip install pmd-cli`.

<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/v/pmd" alt="PyPI"></a>
<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/pyversions/pmd" alt="Python 3.9+"></a>
<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/l/pmd" alt="License MIT"></a>

## Quick start

```bash
pip install pmd-cli # or: pipx install pmd-cli
pmd README.md
cat doc.md | pmd    # stdin works too
```

## Features

### Headings — 6 levels with colors

| Level | Style | Marker |
|-------|-------|--------|
| H1 | White on magenta | ■ |
| H2 | White on blue | ▸ |
| H3 | Black on cyan | ▸ |
| H4–H6 | Green / Yellow / Gray | ▸ |

No underlines, no `#` prefixes — just color and shape.

### Inline formatting

- **Bold** `**text**`
- *Italic* `*text*`
- ***Bold-italic*** `***text***`
- ~~Strikethrough~~ `~~text~~`
- `Code` — **bold green** for visibility
- [Links](https://example.com) — blue underlined

### Code blocks — bordered, language-tagged

```
┌ python ──────────────────
│ def hello():
│     print("world")
└──────────────────────────
```

Clean box borders, language label in the top frame. No syntax highlighting — just readable code.

### Tables — autofit, cell wrapping, inline formatting

```
┌──────────┬───────┬─────────────────┐
│ Name     │ Age   │ City            │
├──────────┼───────┼─────────────────┤
│ Alice    │ 30    │ Beijing         │
│ Bob      │ 25    │ Shanghai        │
└──────────┴───────┴─────────────────┘
```

- Unicode box-drawing glyphs
- Columns autofit to content — **compact by default**
- Long cells wrap within their column
- Inline formatting (`` `code` ``, `**bold**`) preserved inside cells

### Task lists

```
  ● Completed task
  ○ Pending task
```

GFM-style `- [x]` / `- [ ]` rendered as green filled / gray empty circles. Mix with regular list items freely.

### Blockquotes

```
▎ Cyan bar + dimmed text
▎ Clean and compact
```

### CJK / Emoji support

Chinese, Japanese, Korean characters measured at correct display width (2 columns). Table alignment and text wrapping work properly for mixed-script documents.

## Why pmd?

| Tool | Language | Dependencies |
|------|----------|-------------|
| **pmd** | Python 3 | **Zero** |
| `glow` | Go | Requires Go toolchain or prebuilt binary |
| `rich-cli` | Python | `rich` + 10+ transitive deps |
| `mdcat` | Rust | Requires Rust or prebuilt binary |
| `mdr` | Ruby | Requires Ruby + `gem install` |

pmd is the lightest option when you need markdown rendering on a server, container, CI runner, or air-gapped machine where installing compilers or heavy packages isn't practical.

## Alternatives vs. built-in `less` / `cat`

These show raw markdown source:

```
# Heading                ← looks like a comment
**bold** *italic*        ← noise characters everywhere
| table | columns |      ← misaligned without rendering
```

pmd shows the **rendered** document — the way it was meant to be read.

## Install

```bash
pip install pmd-cli          # system-wide
pip install --user pmd-cli   # user only
pipx install pmd-cli         # isolated CLI (recommended)
```

Python 3.9 or later. No other dependencies.

## Usage

```bash
# File
pmd README.md

# Stdin
curl -s https://example.com/doc.md | pmd

# From clipboard (macOS)
pbpaste | pmd

# From clipboard (Linux)
xclip -o | pmd
```

## Project structure

```
src/pmd/
  __init__.py      # version
  __main__.py      # parser + renderer (~850 lines)
pyproject.toml     # pip metadata
```

Single-file core — easy to vendor, fork, or embed.

## License

MIT
