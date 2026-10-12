#!/usr/bin/env python3
"""Read-only Org Wiki source integrity gate; HTML validation stays in museum_pipeline."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

INDEX = "a4b7cf91-5db8-4a2f-90e2-89f3ea14bcd5"
LOG = "71e02e9d-80ff-4a75-a7aa-092532c14fd0"
FIELDS = ("TITLE", "WIKI_ID", "CATEGORY", "FILETAGS", "DATE", "SOURCE", "INGEST_ID")
META = re.compile(r"^#\+([A-Z_]+):\s*(.+?)\s*$", re.M | re.I)
WIKI = re.compile(r"\[\[wiki:([^\]\n]+)\](?:\[[^\]\n]*\])?\]")
FILE = re.compile(r"\[\[file:([^\]\n]+)\](?:\[[^\]\n]*\])?\]")
EVENT = re.compile(r"^:CUSTOM_ID:\s*(\S+)", re.M)
BEGIN = re.compile(r"^\s*#\+begin_(src|example|export|comment)\b", re.I)
END = re.compile(r"^\s*#\+end_(src|example|export|comment)\b", re.I)

def visible(text):
    rows, active = [], None
    for line in text.splitlines():
        a, b = BEGIN.match(line), END.match(line)
        if active:
            if b and b.group(1).lower() == active:
                active = None
        elif a:
            active = a.group(1).lower()
        else:
            rows.append(line)
    return "\n".join(rows)

def validate(root):
    root = root.resolve()
    notes = root / "notes"
    if not notes.is_dir():
        raise ValueError("notes directory missing")
    pages, published, refs, index_links, events = {}, set(), [], [], set()
    paths = sorted(notes.rglob("*.org"))
    if not paths:
        raise ValueError("no Org source pages")
    files = 0
    for path in paths:
        rel = path.relative_to(root).as_posix()
        parts = path.relative_to(notes).parts
        if len(parts) != 3 or parts[0] not in {"knowledge", "programming", "reading", "ideas"}:
            raise ValueError("illegal source path: " + rel)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[1]) or path.is_symlink():
            raise ValueError("illegal slug or symlink: " + rel)
        text = path.read_text(encoding="utf-8-sig")
        meta = {k.upper(): v for k, v in META.findall(text)}
        for field in FIELDS:
            if not meta.get(field):
                raise ValueError(f"{rel}: missing {field}")
        page_id = meta["WIKI_ID"]
        if page_id != path.stem:
            raise ValueError(f"{rel}: WIKI_ID does not match filename")
        if page_id in pages:
            raise ValueError(f"duplicate WIKI_ID {page_id}: {pages[page_id]}, {rel}")
        pages[page_id] = rel
        status = meta.get("WIKI_STATUS", "published")
        if status not in {"draft", "published"}:
            raise ValueError(f"{rel}: invalid WIKI_STATUS {status}")
        if status == "published":
            published.add(page_id)
        content = visible(text)
        for m in WIKI.finditer(content):
            target = m.group(1)
            if "#" in target:
                raise ValueError(f"{rel}: unverified wiki fragment {target}")
            refs.append((rel, target))
            if page_id == INDEX:
                index_links.append(target)
        for m in FILE.finditer(content):
            target = unquote(m.group(1).split("::", 1)[0])
            dest = (path.parent / target).resolve()
            if not dest.is_relative_to(root) or not dest.is_file():
                raise ValueError(f"{rel}: unresolved file link {target}")
            if not (dest.is_relative_to(notes) or dest.is_relative_to(root / "note-assets")):
                raise ValueError(f"{rel}: out-of-scope file link {target}")
            files += 1
        if page_id == LOG:
            for event in EVENT.findall(content):
                if event in events:
                    raise ValueError(f"{rel}: duplicated log event {event}")
                events.add(event)
    for rel, target in refs:
        if target not in pages:
            raise ValueError(f"{rel}: dangling wiki link {target}")
    if INDEX not in published or LOG not in published:
        raise ValueError("published index and log are required")
    if len(index_links) != len(set(index_links)):
        raise ValueError("duplicate index entry")
    expected = published - {INDEX}
    if set(index_links) != expected:
        raise ValueError(f"index mismatch: missing={sorted(expected-set(index_links))}, extra={sorted(set(index_links)-expected)}")
    return {"notes": len(paths), "published": len(published), "links": len(refs),
            "files": files, "index": len(index_links), "events": len(events)}

if __name__ == "__main__":
    try:
        print("WIKI_INTEGRITY_PASS", validate(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
    except (ValueError, OSError) as e:
        print("WIKI_INTEGRITY_FAIL", e, file=sys.stderr)
        sys.exit(1)
