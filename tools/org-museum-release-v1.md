# Org Museum Release V1

A pre-merge quality gate, not another publishing engine. The existing pinned Org Museum exporter stays the sole renderer; the existing `publish.yml` stays the sole public Pages deploy.

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
