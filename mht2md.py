#!/usr/bin/env python3
"""mht2md - Convert a saved Claude conversation (.mht / .mhtml) into Markdown.

An MHT (MHTML) file is a MIME "multipart/related" web-page archive. When you
save a Claude.ai conversation from your browser as a "Web Page, Single File",
the entire chat ends up bundled in one .mht file. This tool unpacks that
archive, finds the conversation, and writes a clean Markdown transcript.

Usage:
    python3 mht2md.py chat.mht                  # -> chat.md
    python3 mht2md.py chat.mht -o out.md        # explicit output path
    python3 mht2md.py ./saved_chats/            # convert every .mht in a folder
    python3 mht2md.py chat.mht --raw            # dump full page, skip turn split

Standard library only - no third-party dependencies.
"""

from __future__ import annotations

import argparse
import email
import html
import os
import re
import sys
from email import policy
from html.parser import HTMLParser


# --------------------------------------------------------------------------- #
# 1. MHT -> HTML                                                              #
# --------------------------------------------------------------------------- #
def extract_html_from_mht(path: str) -> str:
    """Read an .mht/.mhtml file and return its main HTML document as text."""
    with open(path, "rb") as fh:
        msg = email.message_from_binary_file(fh, policy=policy.default)

    html_parts: list[str] = []
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                text = payload.decode("utf-8", errors="replace")
            html_parts.append(text)

    if not html_parts:
        # Not a multipart archive (maybe a plain .html saved with .mht ext).
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()

    # A page may carry several HTML fragments; the real document is the largest.
    return max(html_parts, key=len)


# --------------------------------------------------------------------------- #
# 2. HTML -> Markdown                                                         #
# --------------------------------------------------------------------------- #
SKIP_TAGS = {"script", "style", "head", "noscript", "svg", "button"}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer",
              "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "table", "tr"}
# Void elements never have children/closing tags, so they aren't stacked.
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "area", "base",
             "col", "embed", "source", "track", "wbr"}


def _is_hidden_chrome(tag: str, attrs: dict) -> bool:
    """True for Claude.ai UI chrome that should not appear in the transcript.

    Covers screen-reader-only duplicates (the "You said:" / "Claude responded:"
    headings and aria-live status spans), the per-message action toolbar
    (copy/retry buttons plus the timestamp), the "Claude can make mistakes"
    disclaimer, and hidden/inactive panels (e.g. the collapsed artifact
    preview, marked with opacity-0 + pointer-events-none)."""
    cls = attrs.get("class") or ""
    if "sr-only" in cls:
        return True
    if "opacity-0" in cls and "pointer-events-none" in cls:
        return True
    if attrs.get("aria-label") == "Message actions":
        return True
    if attrs.get("data-disclaimer") == "true":
        return True
    return False


class HTMLToMarkdown(HTMLParser):
    """A small, forgiving HTML -> Markdown converter."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.tag_stack: list[bool] = []   # one bool per open element: is it a skip trigger?
        self.skip_count = 0               # open skip-trigger elements; >0 means suppress
        self.in_pre = False
        self.pre_buffer: list[str] = []    # raw text collected inside a <pre>
        self.pre_lang = ""
        self.list_stack: list[dict] = []   # {"type": "ul"/"ol", "n": int}
        self.href: str | None = None
        self.link_text: list[str] = []
        self.blockquote_depth = 0

    # -- output helpers ----------------------------------------------------- #
    def _emit(self, text: str) -> None:
        if self.href is not None:
            self.link_text.append(text)
        else:
            self.out.append(text)

    def _newline(self, count: int = 1) -> None:
        # Collapse so we never stack more than `count` blank lines.
        existing = 0
        for chunk in reversed(self.out):
            if chunk == "":
                continue
            for ch in reversed(chunk):
                if ch == "\n":
                    existing += 1
                else:
                    break
            break
        for _ in range(max(0, count - existing)):
            self.out.append("\n")

    def _list_prefix(self) -> str:
        indent = "  " * (len(self.list_stack) - 1)
        top = self.list_stack[-1]
        if top["type"] == "ol":
            top["n"] += 1
            return f"{indent}{top['n']}. "
        return f"{indent}- "

    # -- tag handlers ------------------------------------------------------- #
    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)

        if tag in VOID_TAGS:
            if self.skip_count:
                return
            self._handle_void(tag, ad)
            return

        is_trigger = tag in SKIP_TAGS or _is_hidden_chrome(tag, ad)
        self.tag_stack.append(is_trigger)
        if is_trigger:
            self.skip_count += 1
        if self.skip_count:
            return

        if tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a":
            self.href = ad.get("href", "")
            self.link_text = []
        elif tag in ("ul", "ol"):
            self.list_stack.append({"type": tag, "n": 0})
            self._newline(1)
        elif tag == "li":
            self._newline(1)
            if self.list_stack:
                self.out.append(self._list_prefix())
        elif tag == "pre":
            self.in_pre = True
            self.pre_buffer = []
            # Language comes from the header label (folded into data-lang during
            # preprocessing); fall back to a language- class on the <code>.
            self.pre_lang = ad.get("data-lang", "") or ""
        elif tag == "code":
            if self.in_pre:
                if not self.pre_lang:
                    cls = ad.get("class", "") or ""
                    m = re.search(r"language-([\w+#-]+)", cls)
                    if m:
                        self.pre_lang = m.group(1)
            else:
                self._emit("`")
        elif tag == "blockquote":
            self.blockquote_depth += 1
            self._newline(2)
        elif re.fullmatch(r"h[1-6]", tag):
            self._newline(2)
            self.out.append("#" * int(tag[1]) + " ")
        elif tag in BLOCK_TAGS:
            self._newline(2)

    def _handle_void(self, tag, ad):
        if tag == "br":
            self._emit("\n")
        elif tag == "hr":
            self._newline(2)
            self.out.append("---")
            self._newline(2)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        was_trigger = self.tag_stack.pop() if self.tag_stack else False
        if was_trigger:
            self.skip_count -= 1
        # Suppress end handling if we're still inside (or just closing) a skip.
        if self.skip_count or was_trigger:
            return

        if tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a":
            text = "".join(self.link_text).strip()
            href = self.href or ""
            self.href = None
            self.link_text = []
            if href and text:
                self.out.append(f"[{text}]({href})")
            elif text:
                self.out.append(text)
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            if not self.list_stack:
                self._newline(2)
        elif tag == "pre":
            content = "".join(self.pre_buffer).strip("\n")
            # Use a fence longer than any backtick run inside the code, so code
            # that itself contains ``` cannot terminate the block early.
            longest = max((len(r) for r in re.findall(r"`+", content)), default=0)
            fence = "`" * max(3, longest + 1)
            self._newline(2)
            self.out.append(f"{fence}{self.pre_lang}\n")
            self.out.append(content + "\n")
            self.out.append(fence)
            self._newline(2)
            self.in_pre = False
            self.pre_buffer = []
        elif tag == "code" and not self.in_pre:
            self._emit("`")
        elif tag == "blockquote":
            self.blockquote_depth = max(0, self.blockquote_depth - 1)
            self._newline(2)
        elif tag in BLOCK_TAGS:
            self._newline(2)

    def handle_data(self, data):
        if self.skip_count:
            return
        if self.in_pre:
            # Collect all text (a <pre> may hold many <span> lines); the fence
            # is written once, with a safe length, when the <pre> closes.
            self.pre_buffer.append(data)
            return
        # Normalise runs of whitespace in flowing text.
        text = re.sub(r"\s+", " ", data)
        if text.strip() == "" and not text:
            return
        self._emit(text)

    # -- result ------------------------------------------------------------- #
    def markdown(self) -> str:
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)        # trailing spaces
        text = re.sub(r"\n{3,}", "\n\n", text)        # collapse blank runs
        return text.strip()


# Claude.ai shows a code block's language in a small header label just before
# the <pre>. Fold that label into the <pre> as data-lang so it becomes the
# fence's language hint instead of leaking into the text as a stray line.
_LANG_LABEL_RE = re.compile(
    r'<div class="[^"]*\btext-text-500\b[^"]*\bfont-small\b[^"]*">'
    r'([A-Za-z0-9+#.-]{1,20})</div>'
    r'(\s*<div[^>]*>\s*)?'      # optional scroll wrapper
    r'\s*<pre\b',
    re.IGNORECASE)


def _fold_code_language(fragment: str) -> str:
    return _LANG_LABEL_RE.sub(
        lambda m: f'{m.group(2) or ""}<pre data-lang="{m.group(1)}"', fragment)


def html_to_markdown(fragment: str) -> str:
    parser = HTMLToMarkdown()
    parser.feed(_fold_code_language(fragment))
    parser.close()
    return parser.markdown()


# --------------------------------------------------------------------------- #
# 3. Conversation turn detection                                              #
# --------------------------------------------------------------------------- #
# Claude.ai marks turns in the DOM. These substrings flag the start of a turn.
USER_MARKERS = [
    'data-testid="user-message"',
    'data-testid=user-message',
    'class="font-user-message"',
]
ASSISTANT_MARKERS = [
    "font-claude-message",
    'data-testid="claude-message"',
    'data-is-streaming',
]


def find_turn_boundaries(html_doc: str) -> list[tuple[int, str]]:
    """Return sorted (position, role) boundaries found in the raw HTML."""
    boundaries: list[tuple[int, str]] = []
    lowered = html_doc.lower()
    for marker in USER_MARKERS:
        start = 0
        while (idx := lowered.find(marker.lower(), start)) != -1:
            boundaries.append((idx, "user"))
            start = idx + 1
    for marker in ASSISTANT_MARKERS:
        start = 0
        while (idx := lowered.find(marker.lower(), start)) != -1:
            boundaries.append((idx, "assistant"))
            start = idx + 1
    boundaries.sort()

    # De-duplicate near-identical positions (overlapping markers on one node).
    deduped: list[tuple[int, str]] = []
    for pos, role in boundaries:
        if deduped and pos - deduped[-1][0] < 40 and role == deduped[-1][1]:
            continue
        deduped.append((pos, role))
    return deduped


# The per-message date sits in the action toolbar (which we strip from the
# body); pull it out separately so it can be shown on the turn heading.
_TIMESTAMP_RE = re.compile(
    r'<span class="text-text-500 text-xs[^"]*"[^>]*>([^<]+)</span>')


def extract_timestamp(segment: str) -> str:
    m = _TIMESTAMP_RE.search(segment)
    return html.unescape(m.group(1)).strip() if m else ""


def split_into_turns(html_doc: str) -> list[tuple[str, str, str]]:
    """Split the document into (role, date, markdown) turns. [] if none."""
    boundaries = find_turn_boundaries(html_doc)
    if not boundaries:
        return []

    turns: list[tuple[str, str, str]] = []
    for i, (pos, role) in enumerate(boundaries):
        # Back up to the opening "<" of the tag carrying the marker.
        tag_start = html_doc.rfind("<", 0, pos)
        if tag_start == -1:
            tag_start = pos
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(html_doc)
        end = html_doc.rfind("<", 0, end) if i + 1 < len(boundaries) else end
        segment = html_doc[tag_start:end]
        md = html_to_markdown(segment)
        if md.strip():
            turns.append((role, extract_timestamp(segment), md))
    return turns


def extract_title(html_doc: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html_doc,
                  re.IGNORECASE | re.DOTALL)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
        # Strip a trailing " - Claude" style suffix for a cleaner heading.
        return re.sub(r"\s*[-|]\s*Claude\s*$", "", title) or title
    return ""


def body_only(html_doc: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html_doc,
                  re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else html_doc


# --------------------------------------------------------------------------- #
# 4. Assemble the Markdown document                                           #
# --------------------------------------------------------------------------- #
ROLE_HEADINGS = {"user": "## 👤 User", "assistant": "## 🤖 Claude"}


def render_turns(html_doc: str, raw: bool = False) -> str:
    """Render just the conversation body (no document title)."""
    lines: list[str] = []
    turns = [] if raw else split_into_turns(html_doc)

    if turns:
        for role, date, md in turns:
            heading = ROLE_HEADINGS.get(role, f"## {role.title()}")
            if date:
                heading += f" — {date}"
            lines.append(heading)
            lines.append("")
            lines.append(md)
            lines.append("")
    else:
        # Fallback: no turn markers recognised - convert the whole body so the
        # content is preserved even if we can't separate speakers.
        if not raw:
            sys.stderr.write(
                "  note: no Claude turn markers found - writing full-page "
                "Markdown.\n")
        lines.append(html_to_markdown(body_only(html_doc)))

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def convert(html_doc: str, raw: bool = False) -> str:
    title = extract_title(html_doc)
    body = render_turns(html_doc, raw)
    parts = [f"# {title}"] if title else []
    parts.append(body)
    text = "\n\n".join(p for p in parts if p)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def slugify(text: str, seen: dict[str, int]) -> str:
    """GitHub-style heading anchor, with -1/-2 suffixes for duplicates."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def convert_combined(paths: list[str], raw: bool = False) -> str:
    """Combine several conversations into one Markdown file: a table of
    contents followed by each conversation as a numbered `# N. Title` section."""
    sections: list[str] = []
    toc: list[str] = []
    seen: dict[str, int] = {}

    for n, path in enumerate(paths, 1):
        html_doc = extract_html_from_mht(path)
        title = (extract_title(html_doc)
                 or os.path.splitext(os.path.basename(path))[0])
        body = render_turns(html_doc, raw)
        heading_text = f"{n}. {title}"
        anchor = slugify(heading_text, seen)
        toc.append(f"{n}. [{title}](#{anchor})")
        sections.append(f"# {heading_text}\n\n{body}")

    header = (f"# Claude Conversations\n\n"
              f"_{len(paths)} conversations combined._\n\n"
              f"## Contents\n\n" + "\n".join(toc))
    doc = header + "\n\n---\n\n" + "\n\n---\n\n".join(sections)
    return re.sub(r"\n{3,}", "\n\n", doc).strip() + "\n"


# --------------------------------------------------------------------------- #
# 5. CLI                                                                      #
# --------------------------------------------------------------------------- #
def convert_file(in_path: str, out_path: str | None, raw: bool) -> str:
    html_doc = extract_html_from_mht(in_path)
    md = convert(html_doc, raw=raw)
    if out_path is None:
        base, _ = os.path.splitext(in_path)
        out_path = base + ".md"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    return out_path


def _expand_inputs(inputs: list[str]) -> list[str]:
    """Expand any directories into their .mht/.mhtml files, preserving order."""
    files: list[str] = []
    for item in inputs:
        if os.path.isdir(item):
            files.extend(sorted(
                os.path.join(item, f) for f in os.listdir(item)
                if f.lower().endswith((".mht", ".mhtml"))))
        else:
            files.append(item)
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert saved Claude .mht/.mhtml conversations to Markdown.")
    ap.add_argument("input", nargs="+",
                    help="One or more .mht/.mhtml files, or folders of them.")
    ap.add_argument("-o", "--output",
                    help="Output path. With multiple inputs this becomes a "
                         "single combined file (one numbered section per chat).")
    ap.add_argument("--combine", action="store_true",
                    help="Force combined output even for a single input. "
                         "Requires -o.")
    ap.add_argument("--raw", action="store_true",
                    help="Skip turn detection; convert the whole page.")
    args = ap.parse_args(argv)

    files = _expand_inputs(args.input)
    missing = [f for f in files if not os.path.isfile(f)]
    if missing:
        print("Not found:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    if not files:
        print("No .mht/.mhtml files found.", file=sys.stderr)
        return 1

    combine = args.combine or (args.output and len(files) > 1)

    if combine:
        if not args.output:
            ap.error("combined output requires -o/--output.")
        print(f"Combining {len(files)} conversation(s) -> {args.output}")
        md = convert_combined(files, raw=args.raw)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Wrote {args.output}")
        return 0

    if args.output and len(files) == 1:
        out = convert_file(files[0], args.output, args.raw)
        print(f"Wrote {out}")
        return 0

    # Multiple inputs, no -o: write a sibling .md for each.
    for f in files:
        print(f"Converting {f} ...")
        out = convert_file(f, None, args.raw)
        print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
