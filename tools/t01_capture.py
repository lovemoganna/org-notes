#!/usr/bin/env python3
"""One-article-at-a-time source capture; never loops over a fixture manifest."""
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen,Request
import hashlib, json
ID="T01"
REPO="lovemoganna/Prompts"
REF="0fdfdde53854523a9bd8704a1ac2c2c785702072"
PATH="Major/1.什么是提示词.md"
BLOB="1c9ed5231580eb25d96e75da70ed5981dc5a877c"
url=f"https://raw.githubusercontent.com/{REPO}/{REF}/{quote(PATH,safe='/')}"
with urlopen(Request(url,headers={"User-Agent":"OrgMuseum-SingleNote-T01"}),timeout=30) as r:
    data=r.read()
sha=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
assert sha==BLOB,(sha,BLOB)
target=Path("_single_t01");target.mkdir(exist_ok=True)
(target/"source.md").write_bytes(data)
(target/"source.json").write_text(json.dumps({
"id":ID,"sourceRepo":REPO,"ref":REF,"path":PATH,"blob":sha,
"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),
"scope":"T01 ONLY; not a batch test"},ensure_ascii=False,indent=2),encoding="utf-8")
print("SINGLE_T01_SOURCE_VERIFIED",sha,len(data))
