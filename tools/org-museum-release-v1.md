# Org Museum Release V1

A pre-merge quality gate, not another publishing engine. The existing pinned Org Museum exporter stays the sole renderer; the existing `publish.yml` stays the sole public Pages deploy.

## Pre-authoring source identity gate

Before running `note-reforge` or generating a Sketchnote, check the **exact source file**:

```bash
python3 tools/org_museum_release_v1.py preflight --case T01
# Existing published source: exits with code 3 (NO new page).
# A new source: returns NEW_CANDIDATE; this is not permission to publish.
```

You can also pass a pinned GitHub file URL using `--source`. The tool normalizes
the URL-encoded path and exact GitHub blob revision, then compares published and
draft note sources. It prints matching Wiki IDs and paths. Multiple published
pages are flagged for **manual consolidation review**, never deleted or merged
automatically. `--report-only` returns findings without stopping the shell,
but it never authorizes a write.

If any published match exists, choose `UPDATE_OR_NOOP`: inspect its actual
content and performance. Modify the **existing note** only when there is a
demonstrable knowledge gain; preserve its identity, URL and history. A second
page with the same source is not a valid content E2E success case.
This is an additional **early gate**: the original PR collision guard remains.

## Workflow

1. Use the canonical `note-reforge` and `sketchnote-generator` Skills outside GitHub Actions to author the note and its actual illustration. Model generation cannot be faithfully replaced by a deterministic Actions script.
2. Stage only `notes/<kind>/<slug>/<id>.org` and actual `note-assets/<id>/` files. Preserve author, source, timestamps and note identity.
3. Open a PR. The `Org Museum Release V1 · PR Review` check performs the production `museum_pipeline.py validate` and `build` with the pinned Emacs 30.2 / publisher commit, verifies the build output against each note's SHA-256, and generates a single-file Chinese HTML review artifact.
4. Review **source facts and unique source assets, prompt/template exactness, logic, writing quality, picture text and link/identity**. The automation intentionally marks content/image quality as **REQUIRES_HUMAN_REVIEW**; it does not silently promote structural checks to semantic evidence.
5. Merge only after quality approval and a successful preflight. Public deployment is performed separately by the existing `publish.yml`, which checks the live receipt and source commit.

The preflight reports status but cannot force branch protection. Configure GitHub repository rules / required status checks if hard enforcement is desired. Do not grant Actions a write token or enable auto-merge.

## Five-source fixture pressure test

The pinned test set `tools/release-v1-fixtures.json` uses **five new original documents** from `lovemoganna/Prompts`. `python3 tools/org_museum_release_v1.py fixtures` freezes and cryptographically verifies each original Git blob, then stages that original inside an inert Org example block with a problem-based title/entry point. This is a **source-preservation, parser, renderer and report** test, **not** a claim that AI performed meaningful note-reforge or created images for all five. It must never be published.

Testing branch `test/org-museum-release-v1-20261012` runs this case. Full end-to-end quality still needs genuine model-produced output and per-image review; prior 3 published samples provide separate real-image/Pages evidence, not five new independently tested image-generation outputs.

## Exit criteria

- Five original-source SHA checks pass, and five Org fixtures render with source SHA preserved.
- Production renderer validation and exported page SHA/identity checks pass.
- HTML Review generated and downloaded from PR action artifact.
- Known negatives (missing source field, broken asset, unescaped Org macro, corrupted hash, extra/unapproved path) remain blocking.
- No PR action deploys to Pages, edits `main` or treats content/image quality as automatically approved.

## Operations

```bash
python3 tools/org_museum_release_v1.py fixtures
python3 tools/org_museum_release_v1.py audit --base "$(git rev-parse HEAD^)" --fixtures _review/fixtures.json --site _site
```


## Provenance collision gate (2026-10-14)

New Org pages must not silently duplicate a **previously published** page derived from the same full GitHub source file, even when the source commit or URL percent-encoding differs. The PR reviewer compares parsed `#+SOURCE` identity for added note files with already published notes. On a collision it emits `V1_SOURCE_COLLISION`, adds `sourceCollisions` to the JSON, and blocks the candidate. The preferred remediation is to **update the existing wiki ID in place** or explicitly resolve a real series/split instead of manufacturing another ID. Existing updates to the same note path and draft-only sources do not trigger this gate. Only unambiguous pinned GitHub URLs can be matched; generic source text is not proof of identity. A passing gate is not proof of non-duplication across all possible source types.

Regression covers same file across revisions and URL-encoded paths, changed file, draft-only source, and unknown source types. The previously published duplicate pages remain unchanged pending a separate, evidence-based consolidation decision.


## Serial-only hard gate (2026-10-15)

**One article at a time is a mandatory invariant, not a preference.** Work on exactly one ID until its source check, actual note-reforge judgment (including NOOP), optional illustration, real Emacs render, negative checks, and human content review reach an explicit decision. Do not start T02 before T01 reaches a terminal state. A new test case needs a separate run.

- Run exactly one fixture: `python3 tools/org_museum_release_v1.py fixtures --case T01`. Omitting `--case` fails; comma lists or an all-cases mode are unsupported.
- Machine audit rejects PRs with two or more changed Org notes, even if each is individually valid. Asset changes must belong to that one note and may not be used to smuggle in another article.
- Five entries in the manifest are an inventory/queue, **not** permission to execute them as one batch.
- If a pinned original has an already published Wiki ID, do not duplicate it: inspect the existing article; choose the *same-ID original path update* only for a proven material defect, otherwise record NOOP.
- A successfully fetched fixture is not proof of a successful article: the reviewer must verify exactly one real exported HTML and its original SHA.
- Quality claims are scoped per ID. Never use an earlier article's green test to approve the next article.
