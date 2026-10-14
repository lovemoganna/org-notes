#!/usr/bin/env python3
from urllib.request import Request,urlopen
from urllib.parse import quote
from pathlib import Path
import hashlib,json
repo="lovemoganna/Prompts"
ref="0fdfdde53854523a9bd8704a1ac2c2c785702072"
path="Major/5.提示原则.md"
sha="2dc4284cccfda0b51f6e41b2eae715c8d3798e9a"
url=f"https://raw.githubusercontent.com/{repo}/{ref}/{quote(path,safe='/')}"
with urlopen(Request(url,headers={"User-Agent":"single-article-principles"}),timeout=40) as resp:body=resp.read()
actual=hashlib.sha1(b"blob "+str(len(body)).encode()+b"\0"+body).hexdigest()
assert actual==sha,(actual,sha)
out=Path("_single_principles")
out.mkdir(exist_ok=True)
(out/"original.md").write_bytes(body)
(out/"manifest.json").write_text(json.dumps({"case":"Major/5 only","blob":sha,"sha256":hashlib.sha256(body).hexdigest(),"source":url,"bytes":len(body)},ensure_ascii=False,indent=2),encoding="utf-8")
print("SINGLE_PRINCIPLES_BLOB_VERIFIED",actual,len(body))
