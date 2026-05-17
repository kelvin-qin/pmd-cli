#!/usr/bin/env python3
"""pmd - Terminal Markdown renderer with ANSI formatting.

Zero dependencies, Python 3 stdlib only.
Usage: pmd <file.md>  or  cat file.md | pmd
"""

import re
import sys
import os
import shutil
import textwrap


# ═══════════════════════════════════════════════════════════════════════
# ANSI Styles
# ═══════════════════════════════════════════════════════════════════════

def _s(*codes):
    """Build an ANSI SGR sequence from attribute codes."""
    return '\033[' + ';'.join(str(c) for c in codes) + 'm'

RESET = _s(0)

# Heading styles — descending visual weight
STYLE = {
    'h1': _s(1, 37, 45),      # bold white on magenta
    'h2': _s(1, 37, 44),      # bold white on blue
    'h3': _s(1, 30, 46),      # bold black on cyan
    'h4': _s(1, 32),          # bold green (no bg)
    'h5': _s(1, 33),          # bold yellow
    'h6': _s(2, 37),          # dim white
    'bold': _s(1, 31),          # bold red
    'italic': _s(3),
    'bold_italic': _s(1, 3, 31),  # bold italic red
    'strikethrough': _s(9),
    'code': _s(1, 32),        # bold green
    'link': _s(4, 34),        # underline blue
    'image': _s(2, 35),       # dim magenta
    'bq_bar': _s(36),         # cyan blockquote bar
    'bq_text': _s(2),         # dim blockquote text
    'table_head': _s(1, 4),   # bold underline
    'table_border': _s(2),    # dim borders
    'hr': _s(2),              # dim horizontal rule
    'bullet': _s(36),         # cyan bullet
    'list_num': _s(33),       # yellow numbers
    'dim': _s(2),
}

def style(text, name):
    """Wrap text in an ANSI style."""
    s = STYLE.get(name)
    return f'{s}{text}{RESET}' if s else text


# ═══════════════════════════════════════════════════════════════════════
# Inline Parser
# ═══════════════════════════════════════════════════════════════════════

# Regex matching all inline elements; order determines priority.
_INLINE_RE = re.compile(
    r'`(?P<code>[^`\n]+)`'
    r'|!\[(?P<image_alt>[^\]]*)\]\((?P<image_url>[^)]*)\)'
    r'|\[(?P<link_text>[^\]]*)\]\((?P<link_url>[^)]*)\)'
    r'|\*\*\*(?P<bold_italic>.+?)\*\*\*'
    r'|\*\*(?P<bold>.+?)\*\*'
    r'|(?<!\*)\*(?!\*)(?P<italic>.+?)(?<!\*)\*(?!\*)'
    r'|(?<=\b)__(?=\S)(?P<bold2>.+?)(?<=\S)__(?=\b)'
    r'|(?<=\b)_(?!_)(?=\S)(?P<italic2>.+?)(?<=\S)(?<!_)_(?=\b)'
    r'|~~(?P<strike>.+?)~~'
)


def parse_inline(text):
    """Parse inline Markdown into a list of (type, text, url) tuples.
    Uses a two-pass approach: code spans first, then remaining formatting.
    This ensures `` `code` `` inside `**bold**` is rendered correctly.
    """
    if not text:
        return []

    # Pass 1: pre-render code spans and replace with rendered ANSI text.
    # This ensures `` `code` `` inside `**bold**` renders with both styles.
    code_re = re.compile(r'`(?P<code>[^`\n]+)`')

    def render_code(m):
        return style(m.group('code'), 'code')

    text = code_re.sub(render_code, text)

    # Pass 2: parse remaining formatting on the text with pre-rendered code
    tokens = []
    pos = 0

    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            tokens.append(('text', text[pos:m.start()], ''))

        kind = m.lastgroup
        if kind in ('image_alt', 'image_url'):
            tokens.append(('image', m.group('image_alt') or m.group('image_url'), m.group('image_url')))
        elif kind in ('link_text', 'link_url'):
            tokens.append(('link', m.group('link_text'), m.group('link_url')))
        elif kind == 'bold_italic':
            tokens.append(('bold_italic', m.group('bold_italic'), ''))
        elif kind in ('bold', 'bold2'):
            tokens.append(('bold', m.group(kind), ''))
        elif kind in ('italic', 'italic2'):
            tokens.append(('italic', m.group(kind), ''))
        elif kind == 'strike':
            tokens.append(('strikethrough', m.group('strike'), ''))

        pos = m.end()

    if pos < len(text):
        tokens.append(('text', text[pos:], ''))

    return tokens


# ═══════════════════════════════════════════════════════════════════════
# Block Parser
# ═══════════════════════════════════════════════════════════════════════

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')
FENCE_RE = re.compile(r'^```(\w*)\s*$')
BQ_RE = re.compile(r'^>\s?(.*)')
UL_RE = re.compile(r'^(\s*)([-*+])\s+(.*)')
OL_RE = re.compile(r'^(\s*)(\d+)[.)]\s+(.*)')
HR_RE = re.compile(r'^(?:[-*_]\s?){3,}$')
TABLE_ROW_RE = re.compile(r'^\|(.+)\|$')


def parse_blocks(text):
    """Parse Markdown text into a list of block dicts."""
    lines = text.split('\n')
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        # Skip blank lines
        if lines[i].strip() == '':
            i += 1
            continue

        line = lines[i]

        # Heading
        m = HEADING_RE.match(line)
        if m:
            blocks.append({
                'type': 'heading',
                'level': len(m.group(1)),
                'content': m.group(2),
            })
            i += 1
            continue

        # Horizontal rule (only if not part of a table)
        hr_match = HR_RE.match(line.strip())
        if hr_match and '|' not in line.strip():
            blocks.append({'type': 'hr'})
            i += 1
            continue

        # Fenced code block
        m = FENCE_RE.match(line.strip())
        if m:
            lang = m.group(1)
            i += 1
            code_lines = []
            while i < n and not FENCE_RE.match(lines[i].strip()):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1  # closing fence
            blocks.append({
                'type': 'code_block',
                'language': lang,
                'lines': code_lines,
            })
            continue

        # Blockquote
        m = BQ_RE.match(line)
        if m:
            bq_lines = []
            while i < n:
                m2 = BQ_RE.match(lines[i])
                if m2:
                    bq_lines.append(m2.group(1))
                    i += 1
                elif lines[i].strip() == '':
                    # Check if next non-blank continues blockquote
                    j = i + 1
                    while j < n and lines[j].strip() == '':
                        j += 1
                    if j < n and BQ_RE.match(lines[j]):
                        bq_lines.append('')
                        i += 1
                    else:
                        break
                else:
                    break
            blocks.append({'type': 'blockquote', 'lines': bq_lines})
            continue

        # Table
        if TABLE_ROW_RE.match(line.strip()):
            table_rows = []
            while i < n and TABLE_ROW_RE.match(lines[i].strip()):
                table_rows.append(_parse_table_row(lines[i].strip()))
                i += 1
            if len(table_rows) >= 2:
                blocks.append(_build_table(table_rows))
                continue
            else:
                # Not enough rows, treat as paragraph
                blocks.append({
                    'type': 'paragraph',
                    'content': ' '.join(' '.join(r) for r in table_rows),
                })
                continue

        # Unordered list
        m = UL_RE.match(line)
        if m:
            items = _parse_list_items(lines, i, n, ordered=False)
            i += sum(len(it['raw_lines']) for it in items)
            blocks.append({
                'type': 'list',
                'ordered': False,
                'start': 1,
                'items': items,
            })
            continue

        # Ordered list
        m = OL_RE.match(line)
        if m:
            items = _parse_list_items(lines, i, n, ordered=True)
            i += sum(len(it['raw_lines']) for it in items)
            start = int(OL_RE.match(items[0]['raw_lines'][0]).group(2)) if items else 1
            blocks.append({
                'type': 'list',
                'ordered': True,
                'start': start,
                'items': items,
            })
            continue

        # Paragraph: collect consecutive text lines
        para_lines = []
        while i < n and lines[i].strip() != '':
            ln = lines[i]
            if (HEADING_RE.match(ln) or FENCE_RE.match(ln.strip()) or
                BQ_RE.match(ln) or UL_RE.match(ln) or OL_RE.match(ln) or
                TABLE_ROW_RE.match(ln.strip()) or
                (HR_RE.match(ln.strip()) and '|' not in ln.strip())):
                break
            para_lines.append(ln)
            i += 1

        if para_lines:
            blocks.append({
                'type': 'paragraph',
                'content': ' '.join(para_lines),
            })

    return blocks


def _parse_table_row(line):
    """Split a |...| table row into cells."""
    inner = line.strip()[1:-1]  # remove leading | and trailing |
    return [c.strip() for c in inner.split('|')]


def _is_table_sep(cell):
    """Check if a cell is a separator like ---, :---, :---:"""
    c = cell.strip()
    c = c.lstrip(':').rstrip(':')
    return len(c) > 0 and all(ch == '-' for ch in c)


def _build_table(rows):
    """Build a table block from raw rows, detecting separator and alignments."""
    # Find separator row
    sep_idx = None
    for idx, row in enumerate(rows):
        if all(_is_table_sep(c) for c in row):
            sep_idx = idx
            break

    if sep_idx is None:
        return {'type': 'paragraph', 'content': ' '.join(' | '.join(r) for r in rows)}

    # Parse alignments
    aligns = []
    for cell in rows[sep_idx]:
        c = cell.strip()
        left = c.startswith(':')
        right = c.endswith(':')
        if left and right:
            aligns.append('center')
        elif right:
            aligns.append('right')
        else:
            aligns.append('left')

    # Header + data rows
    header = rows[:sep_idx]
    data = rows[sep_idx + 1:]

    return {
        'type': 'table',
        'header': header,
        'rows': data,
        'aligns': aligns,
    }


def _parse_list_items(lines, start, end, ordered=False):
    """Parse consecutive list items starting at line `start`."""
    item_re = OL_RE if ordered else UL_RE
    items = []
    i = start

    while i < end:
        line = lines[i]
        if line.strip() == '':
            i += 1
            continue

        m = item_re.match(line)
        if not m:
            break

        raw_content = m.group(3)
        todo = False
        done = False
        # GFM todo: - [ ] item  or  - [x] item
        if re.match(r'\[ \]\s+', raw_content):
            todo, done = True, False
            raw_content = re.sub(r'^\[ \]\s+', '', raw_content)
        elif re.match(r'\[[xX]\]\s+', raw_content):
            todo, done = True, True
            raw_content = re.sub(r'^\[[xX]\]\s+', '', raw_content)

        raw_lines = [line]
        content_lines = [raw_content]
        i += 1

        # Continuation lines
        while i < end and lines[i].strip() != '':
            ln = lines[i]
            if UL_RE.match(ln) or OL_RE.match(ln):
                break
            if HEADING_RE.match(ln) or FENCE_RE.match(ln.strip()):
                break
            raw_lines.append(ln)
            content_lines.append(ln)
            i += 1

        items.append({
            'raw_lines': raw_lines,
            'content': ' '.join(content_lines),
            'todo': todo,
            'done': done,
        })

    return items


# ═══════════════════════════════════════════════════════════════════════
# Renderer
# ═══════════════════════════════════════════════════════════════════════

def render_inline(tokens):
    """Render parsed inline tokens to a string with ANSI codes."""
    parts = []
    for typ, text, url in tokens:
        if typ == 'text':
            parts.append(text)
        elif typ in ('bold', 'italic', 'bold_italic', 'code', 'strikethrough'):
            parts.append(style(text, typ))
        elif typ == 'link':
            parts.append(style(text, 'link'))
            if url and url != text:
                parts.append(' ' + style(f'({url})', 'dim'))
        elif typ == 'image':
            alt = text or url
            parts.append(style(f'[IMG: {alt}]', 'image'))
    return ''.join(parts)


def get_term_width():
    """Detect terminal width, defaulting to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def visible_len(s):
    """Display width excluding ANSI escape sequences. CJK chars count as 2."""
    w = 0
    in_esc = False
    i = 0
    while i < len(s):
        if in_esc:
            if s[i] == 'm':
                in_esc = False
            i += 1
            continue
        if s[i] == '\033' and i + 1 < len(s) and s[i + 1] == '[':
            in_esc = True
            i += 2
            continue
        cp = ord(s[i])
        w += 2 if _is_wide(cp) else 1
        i += 1
    return w


def _is_wide(cp):
    """Check if a Unicode codepoint is East Asian Wide or Fullwidth."""
    return (
        (0x1100 <= cp <= 0x115F) or   # Hangul Jamo
        (0x2329 <= cp <= 0x232A) or   # Angle brackets
        (0x2E80 <= cp <= 0xA4CF) or   # CJK Radicals .. Yi
        (0xA960 <= cp <= 0xA97C) or   # Hangul Extended
        (0xAC00 <= cp <= 0xD7A3) or   # Hangul Syllables
        (0xF900 <= cp <= 0xFAFF) or   # CJK Compat
        (0xFE10 <= cp <= 0xFE19) or   # Vertical forms
        (0xFE30 <= cp <= 0xFE6F) or   # CJK Compat Forms
        (0xFF01 <= cp <= 0xFF60) or   # Fullwidth Forms
        (0xFFE0 <= cp <= 0xFFE6) or   # Fullwidth Signs
        (0x1F300 <= cp <= 0x1F64F) or # Misc Symbols / Emoji
        (0x1F900 <= cp <= 0x1F9FF) or # Supplemental Symbols
        (0x20000 <= cp <= 0x3FFFF)    # CJK Extension B+
    )


def wrap_text(text, width, indent=0, first_indent=0):
    """Word-wrap text to `width`, returning lines. Handles ANSI codes."""
    avail = width - first_indent
    if avail <= 0:
        avail = width

    lines = []
    cur = ''
    cur_vis = 0
    target = avail

    # Split into words but keep ANSI sequences attached
    words = []
    buf = ''
    in_esc = False
    for ch in text:
        if in_esc:
            buf += ch
            if ch == 'm':
                in_esc = False
            continue
        if ch == '\033':
            in_esc = True
            buf += ch
            continue
        if ch == ' ':
            if buf:
                words.append(buf)
                buf = ''
        else:
            buf += ch
    if buf:
        words.append(buf)

    for word in words:
        w_vis = visible_len(word)
        if cur == '':
            if w_vis > target:
                # Single word too long, let it overflow
                lines.append(' ' * first_indent + word)
                target = avail
            else:
                cur = word
                cur_vis = w_vis
                target = avail
        elif cur_vis + 1 + w_vis > target:
            lines.append(' ' * first_indent + cur)
            cur = word
            cur_vis = w_vis
            first_indent = indent
            target = width - indent
        else:
            cur += ' ' + word
            cur_vis += 1 + w_vis

    if cur:
        lines.append(' ' * first_indent + cur)

    return lines or ['']


def _balance_ansi_lines(lines):
    """Close and reopen ANSI codes across line boundaries."""
    if len(lines) <= 1:
        return lines

    def _active_codes_at_end(s):
        """Return the ANSI prefix string that represents open codes at end of s."""
        in_esc = False
        current = ''  # last full escape sequence seen
        depth = 0
        for i, ch in enumerate(s):
            if in_esc:
                if ch == 'm':
                    in_esc = False
                    seq = s[esc_start:i+1]
                    if seq == '\033[0m':
                        current = ''
                    else:
                        current = seq
                continue
            if ch == '\033' and i+1 < len(s) and s[i+1] == '[':
                esc_start = i
                in_esc = True
        return current

    result = [lines[0]]
    for i in range(1, len(lines)):
        prev = result[-1]
        active = _active_codes_at_end(prev)
        curr = lines[i]
        # Close previous line's open codes
        if active:
            result[-1] = prev + '\033[0m'
        # Reopen codes on continuation line
        if active and not curr.startswith('\033'):
            curr = active + curr
        result.append(curr)
    return result


def render_block(block, width):
    """Render a single block to a list of lines (with ANSI)."""
    typ = block['type']

    if typ == 'heading':
        level = block['level']
        content = block['content']
        tokens = parse_inline(content)
        text = render_inline(tokens)
        name = f'h{level}'
        marker = '■' if level == 1 else '▸'
        lines = [style(marker + ' ' + text, name)]
        return lines

    elif typ == 'paragraph':
        tokens = parse_inline(block['content'])
        text = render_inline(tokens)
        return wrap_text(text, width)

    elif typ == 'code_block':
        code_lines = block['lines']
        lang = block['language']
        max_len = max((visible_len(l.expandtabs(4)) for l in code_lines), default=0)
        content_w = min(max_len + 4, width - 2)
        content_w = max(content_w, 20)

        result = []
        if lang:
            label = f' {lang} '
            result.append(style('┌' + label + '─' * (content_w - 2 - len(label)), 'table_border'))
        else:
            result.append(style('┌' + '─' * (content_w - 2), 'table_border'))

        for line in code_lines:
            display = line.expandtabs(4)
            vl = visible_len(display)
            if vl > content_w - 4:
                display = display[:content_w - 5] + '…'
                vl = visible_len(display)
            pad = content_w - 4 - vl
            result.append(
                style('│', 'table_border') +
                ' ' + display + ' ' * max(pad, 0) + ' '
            )

        result.append(style('└' + '─' * (content_w - 2), 'table_border'))
        return result

    elif typ == 'blockquote':
        avail = width - 4
        if avail < 20:
            avail = 20
        result = []
        for line in block['lines']:
            if line == '':
                result.append(style('▎', 'bq_bar'))
                continue
            tokens = parse_inline(line)
            text = render_inline(tokens)
            wrapped = _balance_ansi_lines(wrap_text(text, width, indent=2, first_indent=2))
            for wl in wrapped:
                # Prefix with colored bar
                result.append(style('▎', 'bq_bar') + ' ' + style(wl.strip(), 'bq_text'))
        return result

    elif typ == 'list':
        result = []
        indent = '  '
        bullet_indent = 2
        avail = width - 4
        if avail < 20:
            avail = 20

        for idx, item in enumerate(block['items']):
            tokens = parse_inline(item['content'])
            text = render_inline(tokens)

            if item.get('todo'):
                if item.get('done'):
                    bullet = style('●', 'h4')  # green filled circle
                else:
                    bullet = style('○', 'dim')  # gray empty circle
            elif block['ordered']:
                num = block['start'] + idx
                bullet = style(f'{num}.', 'list_num')
            else:
                bullet = style('•', 'bullet')

            wrapped = wrap_text(text, width, indent=4, first_indent=2)
            if wrapped:
                result.append(indent + bullet + ' ' + wrapped[0][bullet_indent:].strip())
                for wl in wrapped[1:]:
                    result.append(indent + '   ' + wl.strip())
            else:
                result.append(indent + bullet)
        return result

    elif typ == 'table':
        header = block['header']
        rows = block['rows']
        aligns = block.get('aligns', [])

        # Render all cells with inline formatting
        def render_cell(cell_text):
            tokens = parse_inline(cell_text)
            return render_inline(tokens)

        hdr_rendered = [[render_cell(c) for c in h] for h in header] if header else []
        data_rendered = [[render_cell(c) for c in row] for row in rows]

        ncols = max(
            (len(r) for r in (hdr_rendered + data_rendered)),
            default=0
        )
        if ncols == 0:
            return ['']

        # Pad rows to ncols
        for r in hdr_rendered:
            while len(r) < ncols:
                r.append('')
        for r in data_rendered:
            while len(r) < ncols:
                r.append('')

        # Min column width = 4
        min_w = 4
        # Border overhead: 1 (leading │) + ncols*1 (trailing │ + inner │)
        overhead = 1 + ncols + 1
        avail_total = width - overhead
        if avail_total < ncols * min_w:
            avail_total = ncols * min_w

        # Step 1: compute desired width per column (max visible line width)
        def max_line_width(text, limit=None):
            """Max visible width of any line in text after wrapping at limit."""
            if limit:
                wrapped = wrap_text(text, limit)
                return max((visible_len(l) for l in wrapped), default=0)
            return visible_len(text)

        desired = [min_w] * ncols
        for row in hdr_rendered + data_rendered:
            for j, cell in enumerate(row):
                w = max_line_width(cell)
                if w > desired[j]:
                    desired[j] = w

        # Step 2: allocate column widths — compact by default, shrink only if needed
        col_widths = list(desired)
        total_desired = sum(col_widths)
        if total_desired > avail_total:
            # Scale down proportionally, but give wider columns more
            remaining = avail_total
            # First pass: cap each column at its desired width, assign min
            for j in range(ncols):
                col_widths[j] = min_w
                remaining -= min_w
            # Second pass: distribute remaining by desired ratio
            if remaining > 0:
                excess_desired = [max(0, desired[j] - min_w) for j in range(ncols)]
                total_excess = sum(excess_desired)
                if total_excess > 0:
                    for j in range(ncols):
                        if excess_desired[j] > 0:
                            extra = int(remaining * excess_desired[j] / total_excess)
                            col_widths[j] = min_w + extra
                    # Distribute any rounding remainder
                    leftover = avail_total - sum(col_widths)
                    for j in range(ncols):
                        if leftover <= 0:
                            break
                        if col_widths[j] < desired[j]:
                            col_widths[j] += 1
                            leftover -= 1

        # Step 3: wrap each cell to column width
        def wrap_cell(text, cw):
            """Wrap text to column width, return list of lines with balanced ANSI."""
            if cw <= 0:
                return [text]
            raw_lines = wrap_text(text, cw)
            return _balance_ansi_lines(raw_lines)

        def pad_line(text, cw, align):
            """Pad a single line to exact column width."""
            vl = visible_len(text)
            if vl >= cw:
                return text
            pad = cw - vl
            if align == 'center':
                return ' ' * (pad // 2) + text + ' ' * (pad - pad // 2)
            elif align == 'right':
                return ' ' * pad + text
            else:
                return text + ' ' * pad

        # Wrap all cells
        hdr_wrapped = []
        for row in hdr_rendered:
            hdr_wrapped.append([wrap_cell(c, col_widths[j]) for j, c in enumerate(row)])
        data_wrapped = []
        for row in data_rendered:
            data_wrapped.append([wrap_cell(c, col_widths[j]) for j, c in enumerate(row)])

        def hline(left, mid, right):
            parts = [left]
            for j in range(ncols):
                parts.append('─' * col_widths[j])
                parts.append(mid if j < ncols - 1 else right)
            return style(''.join(parts), 'table_border')

        def render_wrapped_rows(wrapped_rows, row_style=None):
            lines = []
            for row_cells in wrapped_rows:
                max_lines = max((len(l) for l in row_cells), default=1)
                for line_idx in range(max_lines):
                    parts = [style('│', 'table_border')]
                    for j in range(ncols):
                        cell_lines = row_cells[j]
                        text = cell_lines[line_idx] if line_idx < len(cell_lines) else ''
                        align = aligns[j] if j < len(aligns) else 'left'
                        cell = pad_line(text, col_widths[j], align)
                        if row_style:
                            cell = style(cell, row_style)
                        parts.append(cell)
                        parts.append(style('│', 'table_border'))
                    lines.append(''.join(parts))
            return lines

        result = [hline('┌', '┬', '┐')]

        if header:
            for h in hdr_wrapped:
                result.extend(render_wrapped_rows([h], 'table_head'))
        elif data_wrapped:
            result.extend(render_wrapped_rows([data_wrapped[0]], 'table_head'))
            data_wrapped = data_wrapped[1:]

        if data_wrapped or (header and not data_wrapped):
            result.append(hline('├', '┼', '┤'))

        result.extend(render_wrapped_rows(data_wrapped))

        result.append(hline('└', '┴', '┘'))
        return result

    elif typ == 'hr':
        return [style('─' * width, 'hr')]

    return ['']


def render(blocks, width=None):
    """Render all blocks to a string with proper spacing."""
    if width is None:
        width = get_term_width()

    lines = []
    prev_type = None

    for block in blocks:
        typ = block['type']

        # Add blank line between different block types for readability
        if prev_type is not None:
            same_type = (prev_type == typ)
            if not same_type or typ in ('paragraph', 'heading'):
                lines.append('')

        rendered = render_block(block, width)
        lines.extend(rendered)
        prev_type = typ

    if lines:
        lines.append('')
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f'pmd: {path}: file not found', file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f'pmd: {path}: {e}', file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print('Usage: pmd <file.md>', file=sys.stderr)
        sys.exit(1)

    blocks = parse_blocks(text)
    output = render(blocks)
    sys.stdout.write(output)


if __name__ == '__main__':
    main()
