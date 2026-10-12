#!/usr/bin/env python3
import re, hashlib, urllib.request, urllib.parse
from pathlib import Path
REV="0fdfdde53854523a9bd8704a1ac2c2c785702072"
tests=[
("Original/Work/Project/3-过程.md","6fe5b54d5248b9eff2cc704ef9e156c73f8093cc","notes/knowledge/project-operations/6e9c2b10-7e84-459e-a5f1-d98019ed0a33.org"),
("Original/Meta/deconstruct_ideas.org","793df789bdf5a0f5f131436351b296ddf13069b7","notes/knowledge/thinking-reconstruction/a43396bc-3822-4d8d-b0a0-87b637182dad.org")
]
for i,(source,sha,path) in enumerate(tests):
 url="https://raw.githubusercontent.com/lovemoganna/Prompts/"+REV+"/"+urllib.parse.quote(source,safe="/")
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"OrgMuseumTwoTypeRegression/1.0"}),timeout=35) as resp: data=resp.read()
 actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
 assert actual==sha,(source,"SOURCE_DRIFT",actual)
 text=data.decode("utf-8").replace("\r\n","\n").strip()
 cand=Path(path).read_text(encoding="utf-8")
 if i==0:
  raw=[x.strip().replace("**","") for x in text.splitlines() if re.match(r"^\s*-\s+",x)]
  actual=[x.strip().replace("*","") for x in cand.splitlines() if re.match(r"^\s*-\s+",x)]
  assert len(raw)==35 and raw==actual,("PROJECT_BULLET_LOSS",len(raw),len(actual))
  assert "不是第五个顺序阶段" in cand
 else:
  lines=[];inblock=False
  for line in text.splitlines():
   if re.match(r"^#\+begin_src",line,re.I):inblock=True
   if not inblock and re.match(r"^#\+(?:TITLE|AUTHOR|DATE|STARTUP|TODO|TAGS):",line):continue
   lines.append(line)
   if re.match(r"^#\+end_src",line,re.I):inblock=False
  original="\n".join(lines).strip()
  start=cand.index("#+begin_src markdown")
  end=cand.index("\n* 使用边界",start)
  body=cand[start:end].strip()
  body="\n".join(x for x in body.splitlines() if not re.match(r"^\s*:CUSTOM_ID: (?:quick|deep|balanced)\s*$",x)).strip()
  assert original==body,("ORIGINAL_6K_TEMPLATE_NOT_VERBATIM",len(original),len(body))
  assert body.count("#+begin_src")==body.count("#+end_src")
  assert len(re.findall(r"(?m)^\s*-\s+\[ \]",body))==32
 print("SOURCE_FIDELITY_PASS",source,actual)
for path,expected in [
 ("note-assets/6e9c2b10-7e84-459e-a5f1-d98019ed0a33/sketchnote-header.webp","049630bd8ac2b2915175a3e23287e7a60f60b262ee0d31cab29ec5d51277efc9"),
 ("note-assets/a43396bc-3822-4d8d-b0a0-87b637182dad/sketchnote-header.webp","c87ab3cae0dedc9510029581d9bcae237b0a946d330c05adb12464719ef8fa2a")]:
 b=Path(path).read_bytes()
 assert b.startswith(b"RIFF") and b[8:12]==b"WEBP"
 assert hashlib.sha256(b).hexdigest()==expected
 print("IMAGE_HASH_PASS",path,len(b))
print("TWO_TYPES_SOURCE_AND_IMAGE_PASS")
