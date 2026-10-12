#!/usr/bin/env python3
import json, re, hashlib
from pathlib import Path
release=json.loads(Path("_site/museum-release.json").read_text())
pairs=[
("6e9c2b10-7e84-459e-a5f1-d98019ed0a33","project-operations",["项目闭环","贯穿各环节的风险预防","项目章程","RACI"]),
("a43396bc-3822-4d8d-b0a0-87b637182dad","thinking-reconstruction",["思想重构","整合平衡版","完整详细版","精简实用版"])]
for note_id,topic,tokens in pairs:
 source=Path("notes/knowledge")/topic/(note_id+".org")
 htmlfile=Path("_site/pages/collected/knowledge")/topic/(note_id+".html")
 assert htmlfile.is_file()
 text=htmlfile.read_text(encoding="utf-8")
 for token in tokens: assert token in text,(note_id,token)
 assert "sketchnote-header.webp" in text
 row=next(r for r in release["notes"] if r["id"]==note_id)
 assert row["sha256"]==hashlib.sha256(source.read_bytes()).hexdigest()
 assert row["status"]=="published"
 print("REAL_EMACS_RENDER_PASS",note_id,row["sha256"],len(text))
