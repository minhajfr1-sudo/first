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


class HTMLToMarkdown(HTMLParser):
    """A small, forgiving HTML -> Markdown converter."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip_depth = 0
        self.in_pre = False
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
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        ad = dict(attrs)

        if tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "br":
            self._emit("\n")
        elif tag == "hr":
            self._newline(2)
            self.out.append("---")
            self._newline(2)
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
            self.pre_lang = ""
            self._newline(2)
        elif tag == "code":
            if self.in_pre:
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

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
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
            # Close the fenced block that handle_data opened.
            body = "".join(self.out)
            if not body.endswith("\n"):
                self.out.append("\n")
            self.out.append("```")
            self._newline(2)
            self.in_pre = False
        elif tag == "code" and not self.in_pre:
            self._emit("`")
        elif tag == "blockquote":
            self.blockquote_depth = max(0, self.blockquote_depth - 1)
            self._newline(2)
        elif tag in BLOCK_TAGS:
            self._newline(2)

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.in_pre:
            # Open the fence lazily so we can grab the language hint first.
            if not (self.out and self.out[-1].startswith("```")):
                self.out.append(f"```{self.pre_lang}\n")
            self.out.append(data)
            return
        # Normalise runs of whitespace in flowing text.
        text = re.sub(r"\s+", " ", data)
        if text.strip() == "" and not text:
            return
        self._emit(text)

    # -- result ------------------------------------------------------------- #
    def markdown(self) -> str:
        text = "".join(self.out)
        if self.blockquote_depth or "\n>" in text:
            pass
        text = re.sub(r"[ \t]+\n", "\n", text)        # trailing spaces
        text = re.sub(r"\n{3,}", "\n\n", text)        # collapse blank runs
        return text.strip()


def html_to_markdown(fragment: str) -> str:
    parser = HTMLToMarkdown()
    parser.feed(fragment)
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


def split_into_turns(html_doc: str) -> list[tuple[str, str]]:
    """Split the document into (role, markdown) turns. Empty list if none."""
    boundaries = find_turn_boundaries(html_doc)
    if not boundaries:
        return []

    turns: list[tuple[str, str]] = []
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
            turns.append((role, md))
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


def convert(html_doc: str, raw: bool = False) -> str:
    title = extract_title(html_doc)
    lines: list[str] = []
    if title:
        lines.append(f"# {title}\n")

    turns = [] if raw else split_into_turns(html_doc)

    if turns:
        for role, md in turns:
            lines.append(ROLE_HEADINGS.get(role, f"## {role.title()}"))
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

    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert a saved Claude .mht/.mhtml conversation to Markdown.")
    ap.add_argument("input", help="An .mht/.mhtml file, or a folder of them.")
    ap.add_argument("-o", "--output",
                    help="Output .md path (single-file input only).")
    ap.add_argument("--raw", action="store_true",
                    help="Skip turn detection; convert the whole page.")
    args = ap.parse_args(argv)

    if os.path.isdir(args.input):
        if args.output:
            ap.error("--output cannot be used with a directory input.")
        files = sorted(
            os.path.join(args.input, f) for f in os.listdir(args.input)
            if f.lower().endswith((".mht", ".mhtml")))
        if not files:
            print(f"No .mht/.mhtml files found in {args.input}", file=sys.stderr)
            return 1
        for f in files:
            print(f"Converting {f} ...")
            out = convert_file(f, None, args.raw)
            print(f"  -> {out}")
        return 0

    if not os.path.isfile(args.input):
        print(f"Not found: {args.input}", file=sys.stderr)
        return 1

    out = convert_file(args.input, args.output, args.raw)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
