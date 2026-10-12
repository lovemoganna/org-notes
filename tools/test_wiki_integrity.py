#!/usr/bin/env python3
"""Disposable Git E2E and source-contract regressions; never changes public main."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from check_wiki_integrity import validate, INDEX, LOG

BASE = "34b3311c-bec0-4b3b-aa70-091b3b1d9297"
NEW = "afab7b89-c9f3-4f51-862f-04ab3478eaba"
EXTRA = "b78d1fe3-ff4b-44a2-9c0c-3de107ce012e"

def git(path, *args, ok=True):
    proc = subprocess.run(["git", *args], cwd=path, text=True, capture_output=True)
    if ok and proc.returncode:
        raise AssertionError("git failed: " + proc.stderr)
    return proc

def note(identity, body="", title="Fixture"):
    return (f"#+TITLE: {title}\n#+WIKI_ID: {identity}\n#+CATEGORY: QA\n"
            "#+FILETAGS: :wiki:qa:\n#+DATE: 2026-10-12\n"
            "#+SOURCE: synthetic local regression fixture\n"
            "#+INGEST_ID: f923919b-5c75-4e76-9f81-af1ea9c8e990\n"
            "#+WIKI_STATUS: published\n\n" + body + "\n")

def write(root, identity, body="", topic="fixture"):
    path = root / "notes" / "knowledge" / topic / (identity + ".org")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(note(identity, body), encoding="utf-8")
    return path

def setup(root):
    write(root, BASE, "* Main\nInitial verified baseline")
    write(root, INDEX, f"* Index\n[[wiki:{BASE}][Base]]\n[[wiki:{LOG}][Log]]")
    write(root, LOG, "* Event\n:PROPERTIES:\n:CUSTOM_ID: initial\n:END:")
    assert validate(root)["notes"] == 3

def rejected(label, mutate, fragment):
    with tempfile.TemporaryDirectory(prefix="wiki-negative-") as t:
        root = Path(t)
        setup(root)
        mutate(root)
        try:
            validate(root)
        except ValueError as e:
            if fragment not in str(e):
                raise AssertionError(f"{label}: unexpected failure: {e}") from e
        else:
            raise AssertionError(label + ": invalid input passed")
    print("PASS", label)

def add_event_once(root, identity, event):
    index = root / "notes" / "knowledge" / "fixture" / (INDEX + ".org")
    log = root / "notes" / "knowledge" / "fixture" / (LOG + ".org")
    index_text, log_text = index.read_text(), log.read_text()
    if f":CUSTOM_ID: {event}" in log_text or f"[[wiki:{identity}]" in index_text:
        return "NOOP"
    # Controlled fixture: supplement the existing concept, not only a standalone page.
    concept = root / "notes" / "knowledge" / "fixture" / (BASE + ".org")
    prior = concept.read_text()
    write(root, identity, "* Source\nSynthetic supplementary evidence")
    concept.write_text(prior + f"\n* Related evidence\n[[wiki:{identity}][Supplement]]\n")
    index.write_text(index_text + f"\n[[wiki:{identity}][Added]]\n")
    log.write_text(log_text + f"\n* Event\n:PROPERTIES:\n:CUSTOM_ID: {event}\n:END:\n")
    return "CHANGED"

def main():
    with tempfile.TemporaryDirectory(prefix="wiki-disposable-git-") as t:
        root = Path(t)
        remote, alice, bob = root / "remote.git", root / "alice", root / "bob"
        remote.mkdir()
        git(remote, "init", "--bare", "--initial-branch=main")
        alice.mkdir()
        git(alice, "init", "--initial-branch=main")
        git(alice, "config", "user.name", "Wiki test")
        git(alice, "config", "user.email", "wiki@example.invalid")
        setup(alice)
        original = (alice / "notes" / "knowledge" / "fixture" / (BASE + ".org")).read_bytes()
        git(alice, "add", "notes")
        git(alice, "commit", "-m", "seed source")
        git(alice, "remote", "add", "origin", str(remote))
        git(alice, "push", "-u", "origin", "main")
        git(root, "clone", str(remote), str(bob))
        git(bob, "config", "user.name", "Wiki test")
        git(bob, "config", "user.email", "wiki@example.invalid")
        before = git(alice, "rev-parse", "HEAD").stdout.strip()
        assert add_event_once(alice, NEW, "event-new") == "CHANGED"
        assert validate(alice)["notes"] == 4
        revised_concept = (alice / "notes" / "knowledge" / "fixture" / (BASE + ".org")).read_bytes()
        assert revised_concept.startswith(original) and NEW.encode() in revised_concept
        git(alice, "add", "notes")
        git(alice, "commit", "-m", "ingest")
        after = git(alice, "rev-parse", "HEAD").stdout.strip()
        assert after != before
        assert add_event_once(alice, NEW, "event-new") == "NOOP"
        assert git(alice, "status", "--porcelain").stdout.strip() == ""
        assert git(alice, "rev-parse", "HEAD").stdout.strip() == after
        print("PASS T01-fixture/T02/T14: concept appended with linked evidence, second run NOOP")
        assert validate(bob)["notes"] == 3
        assert git(bob, "status", "--porcelain").stdout.strip() == ""
        print("PASS T06-precondition: audit is read-only; answer citations not tested")
        # Bob advances the remote while Alice still holds a commit from old base.
        b_file = bob / "notes" / "knowledge" / "fixture" / (BASE + ".org")
        b_file.write_text(b_file.read_text() + "\n* Bob edit\nIndependent change\n")
        git(bob, "add", "notes")
        git(bob, "commit", "-m", "concurrent remote edit")
        git(bob, "push", "origin", "main")
        remote_winner = git(bob, "rev-parse", "HEAD").stdout.strip()
        result = git(alice, "push", "origin", "HEAD:main", ok=False)
        assert result.returncode != 0 and "rejected" in result.stderr.lower(), result.stderr
        git(alice, "fetch", "origin", "main")
        assert git(alice, "rev-parse", "origin/main").stdout.strip() == remote_winner
        remote_content = git(alice, "show", f"origin/main:notes/knowledge/fixture/{BASE}.org").stdout
        assert "Bob edit" in remote_content
        print("PASS T10: actual competing Git commit rejected; remote winner intact")
    rejected("T07 dangling wiki link", lambda r: write(r, BASE, "[[wiki:missing][Missing]]"),
             "dangling wiki link")
    rejected("T08 duplicate WIKI_ID", lambda r: write(r, BASE, "duplicate", "other-topic"),
             "duplicate WIKI_ID")
    rejected("T12 missing file link", lambda r: write(r, BASE, "[[file:missing.org][Missing]]"),
             "unresolved file link")
    rejected("T18 unsupported fragment", lambda r: write(r, BASE, "[[wiki:" + LOG + "#section][Bad]]"),
             "unverified wiki fragment")
    rejected("G1 identity mismatch", lambda r: write(r, BASE, "").rename(
             r / "notes" / "knowledge" / "fixture" / (EXTRA + ".org")), "does not match filename")
    rejected("G4 index omission", lambda r: write(r, EXTRA, "No index entry"), "index mismatch")
    rejected("G4 repeated log event", lambda r: write(r, LOG,
             "* First\n:PROPERTIES:\n:CUSTOM_ID: duplicate\n:END:\n"
             "* Second\n:PROPERTIES:\n:CUSTOM_ID: duplicate\n:END:"), "duplicated log event")
    rejected("G2 missing SOURCE", lambda r: write(r, BASE, "").write_text(
             note(BASE).replace("#+SOURCE: synthetic local regression fixture\n", "")),
             "missing SOURCE")
    with tempfile.TemporaryDirectory(prefix="wiki-code-block-") as t:
        root = Path(t)
        setup(root)
        write(root, BASE, "* Sample\n#+begin_example\n[[wiki:fake-id][literal]]\n#+end_example")
        assert validate(root)["notes"] == 3
    print("PASS G3: source-code literals are not treated as references")
    print("WIKI_GIT_E2E_PASS: isolated Git + integrity negative tests; T17 live contradiction NOT_TESTED")

if __name__ == "__main__":
    main()
