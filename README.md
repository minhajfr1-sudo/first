# mht2md

Convert a saved **Claude conversation** (`.mht` / `.mhtml`) into clean **Markdown**.

When you save a Claude.ai chat from your browser as **"Web Page, Single File"**,
the whole conversation is bundled into a single `.mht` (MHTML) archive. This tool
unpacks that archive, separates the **user** and **Claude** turns, and writes a
tidy Markdown transcript.

No third-party dependencies — pure Python standard library (Python 3.10+).

## Usage

```bash
# Single file  ->  chat.md (next to the source)
python3 mht2md.py chat.mht

# Choose the output path
python3 mht2md.py chat.mht -o transcript.md

# Convert every .mht / .mhtml in a folder
python3 mht2md.py ./saved_chats/

# Combine many chats into ONE file (numbered sections + table of contents)
python3 mht2md.py a.mht b.mht c.mht -o Combined.md
python3 mht2md.py ./saved_chats/ -o Combined.md

# Combine and drop re-saved duplicates (same conversation saved twice)
python3 mht2md.py ./saved_chats/ -o Combined.md --dedupe

# Skip turn detection and dump the whole page as Markdown
python3 mht2md.py chat.mht --raw
```

When combining, each conversation becomes a `# N. Title` section, preceded by
a linked table of contents. `--dedupe` skips any conversation whose body is
identical to one already included.

## What it produces

```markdown
# My conversation title

## 👤 User

Hello Claude, can you give me a **Python** snippet?

## 🤖 Claude

Sure! Here is a quick example:

​```python
def greet(name):
    print(f"Hello, {name}")
​```
```

## How it works

1. **Unpack the MHTML** — the `.mht` file is a MIME `multipart/related` archive;
   the tool reads it with Python's `email` module and pulls out the main HTML
   document.
2. **Find the turns** — it looks for the DOM markers Claude.ai uses
   (`data-testid="user-message"` for you, `font-claude-message` for Claude) to
   split the page into individual messages.
3. **Convert to Markdown** — each message's HTML is converted to Markdown,
   preserving headings, code blocks (with language hints), lists, bold/italic,
   links, and blockquotes. `<script>`/`<style>` and other noise is stripped.

If no Claude turn markers are found (e.g. the page came from somewhere else),
it falls back to converting the entire page body so no content is lost.

## Notes / limitations

- Markers are based on Claude.ai's current DOM. If the site's markup changes,
  turn detection may need updating — the `--raw` fallback still captures the
  text in the meantime.
- Inline images embedded in the MHT are not exported; only text/markup content
  is converted.
