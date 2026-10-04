# Source notes

Chat writes canonical Org files under `<kind>/<topic>/<stable-id>.org`.
Kinds: programming, knowledge, reading, ideas. Titles can be Chinese; IDs,
paths and page addresses remain stable across updates.

Before any collection write, load the installed `org-museum-ingest` skill
from the personal Org Museum plugin and follow its complete workflow. The
private pinned fallback is
`lovemoganna/Org-Skills@00b95951feec0418432a983347e0a28048fff700:plugins/org-museum/skills/org-museum-ingest/SKILL.md`;
read it with the connected GitHub tool if plugin skill discovery is unavailable.
Read its programming or note-reforge dependency according to the raw material.
The content of these private skills must never be copied into this public repo.

Collection includes publication verification, not just creating a file.
Return source-file and commit links plus the Pages/build status. Only claim
published after verifying the live release/page version, directly or using
the successful deploy job's MUSEUM-PUBLISHED-RECEIPT attestation. Otherwise
return submitted/publishing (or the actual failure), including the build URL.

Do not place drafts, credentials, private source material or Markdown files
in this directory. Required Org headers: TITLE, WIKI_ID, CATEGORY, FILETAGS,
DATE, SOURCE, INGEST_ID. The Actions validator is authoritative for structure;
public/privacy and evidence checks must also happen before committing.

Generated HTML belongs to the Pages artifact, not Git. Existing pages/ files
are the preserved legacy snapshot. New output uses pages/collected/.

Published Museum URL updates use org-museum-update and the executable URL resolver.
Read the exact source binding from the page or MUSEUM-URL-RESOLVED deployment
evidence, fetch the original Git source, and modify that existing path only.
Filtered page Org is never a replacement for the complete source. Missing
bindings stop the update; they do not create a new note.
