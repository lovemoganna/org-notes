#!/usr/bin/env python3
"""Org Museum Release V1: source-fidelity fixtures and pre-merge HTML Review.

No LLM/image generation, no external side effects on publishing and no auto-merge.
Only the existing pinned Org Museum builder may attest real rendering.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
FIELDS = ("TITLE", "WIKI_ID", "CATEGORY", "FILETAGS", "DATE", "SOURCE", "INGEST_ID", "WIKI_STATUS")
KEEP = ("notes/knowledge/", "notes/programming/", "notes/reading/", "notes/ideas/")
ASSETS = "note-assets/"

def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return p.stdout.strip()

def blob_sha(data: bytes):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def slug_id(i):
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "org-museum-release-v1-heldout-"+i))

def load_manifest(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    ids=[x["id"] for x in obj["cases"]]
    if len(ids)!=5 or len(set(ids))!=5:
        raise ValueError("fixture manifest must have exactly five distinct cases")
    return obj

def stage_fixtures(args):
    m=load_manifest(args.manifest)
    out=[]
    for case in m["cases"]:
        url=("https://raw.githubusercontent.com/"+m["sourceRepository"]+"/"
             +m["sourceCommit"]+"/"+urllib.parse.quote(case["path"],safe="/"))
        req=urllib.request.Request(url,headers={"User-Agent":"org-museum-v1-fidelity-fixture"})
        with urllib.request.urlopen(req,timeout=40) as f:
            original=f.read()
        actual=blob_sha(original)
        if actual!=case["sha"]:
            raise ValueError(case["id"]+": source git blob mismatch "+actual)
        raw=original.decode("utf-8")
        # Wrap the exact original bytes in an inert Org block. This is a source-fidelity
        # and renderer fixture, never an AI reforge quality pass.
        if re.search(r"(?im)^#\+end_example\s*$",raw):
            raise ValueError(case["id"]+": original closes the example block")
        ident=slug_id(case["id"])
        note=ROOT/"notes"/"knowledge"/("qa-"+case["slug"])/(ident+".org")
        if note.exists():
            raise ValueError("fixture path unexpectedly exists "+str(note))
        note.parent.mkdir(parents=True,exist_ok=True)
        source_url="https://github.com/"+m["sourceRepository"]+"/blob/"+m["sourceCommit"]+"/"+urllib.parse.quote(case["path"],safe="/")
        body=[
          "#+TITLE: "+case["title"]+"（仅构建压测）",
          "#+WIKI_ID: "+ident,
          "#+CATEGORY: 发布质量测试",
          "#+FILETAGS: :orgmuseum:qa:fixture:",
          "#+DATE: 2026-10-12",
          "#+SOURCE: "+source_url,
          "#+INGEST_ID: "+ident,
          "#+WIKI_STATUS: draft",
          "",
          "* 定位问题",
          case["question"],
          "",
          "本文件仅验证真实原料的完整保存、Org 格式与发布器导出；不宣称已完成知识炼化，也不宣称有绘制头图。",
          "",
          "* 冻结原文（完整且不执行）",
          "#+begin_example",
          raw.rstrip("\n"),
          "#+end_example",
          ""
        ]
        note.write_text("\n".join(body),encoding="utf-8")
        out.append({"id":case["id"],"source_blob":actual,"source_bytes":len(original),
                    "note":note.relative_to(ROOT).as_posix(),"original":raw,
                    "sha256":hashlib.sha256(original).hexdigest(),"kind":case["kind"]})
    output=ROOT/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    # Do not duplicate user/private input content into JSON/CI logs.
    output.write_text(json.dumps([{k:v for k,v in x.items() if k!="original"} for x in out],ensure_ascii=False,indent=2),encoding="utf-8")
    print("V1_SOURCE_FIXTURES_OK",len(out),str(output))
    for x in out:
        saved=(ROOT/x["note"]).read_text(encoding="utf-8")
        assert x["original"].rstrip("\n") in saved
        print("SOURCE_BLOB_VERIFIED",x["id"],x["source_blob"],x["source_bytes"])
    return out

def headings(data):
    return re.findall(r"(?m)^\*{1,3} (.+)$",data)

def parse_header(text):
    return dict((k.upper(),v.strip()) for k,v in re.findall(r"(?m)^#\+([A-Z_]+):\s*(.*)$",text,re.I))

def source_fingerprint(source: str) -> str | None:
    """Identify a single pinned GitHub source document across revision/URL encoding.

    Deliberately ignore generic prose references: they do not establish an
    unambiguous source identity and must not be treated as the same document.
    """
    match = re.search(r"https://github\.com/[^ \t\n<>]+", source, re.I)
    if not match:
        return None
    parsed=urllib.parse.urlsplit(match.group(0).rstrip(".,;)]"))
    parts=[urllib.parse.unquote(x) for x in parsed.path.strip("/").split("/")]
    if len(parts)<5 or parts[2]!="blob":
        return None
    owner, repository, _, commit = parts[:4]
    if not re.fullmatch(r"[0-9a-f]{40}", commit, re.I):
        return None
    return "github:"+owner.lower()+"/"+repository.lower()+"/"+"/".join(parts[4:])


def find_published_source_collisions(root: Path, added: list[str], candidates: list[dict]) -> list[dict]:
    """New pages sharing a previously published exact source file need review.

    Existing pages updated in place are not new pages; drafts are not published.
    """
    if not added:
        return []
    previous={}
    for p in (root/"notes").rglob("*.org"):
        relative=p.relative_to(root).as_posix()
        if relative in added:
            continue
        meta=parse_header(p.read_text(encoding="utf-8"))
        if meta.get("WIKI_STATUS","published")!="published":
            continue
        key=source_fingerprint(meta.get("SOURCE",""))
        if key:
            previous.setdefault(key,[]).append(relative)
    collisions=[]
    for note in candidates:
        if note["path"] not in added:
            continue
        key=source_fingerprint(note.get("source",""))
        if key and previous.get(key):
            collisions.append({"candidate":note["path"],"sourceFingerprint":key,
                               "alreadyPublished":sorted(previous[key])})
    return collisions


def audit(args):
    base=args.base
    if not re.fullmatch(r"[0-9a-f]{40}",base):
        raise ValueError("base must be an exact full git commit SHA")
    head=git("rev-parse","HEAD")
    changes=git("diff","--name-only",base,head).splitlines()
    added=git("diff","--diff-filter=A","--name-only",base,head).splitlines()
    notes=[f for f in changes if f.endswith(".org") and f.startswith(KEEP)]
    assets=[f for f in changes if f.startswith(ASSETS)]
    infra=[f for f in changes if f not in notes and f not in assets]
    fixture_data=[]
    if args.fixtures:
        fixture_data=json.loads((ROOT/args.fixtures).read_text(encoding="utf-8"))
        if len(fixture_data)!=5 or len({x["id"] for x in fixture_data})!=5:
            raise ValueError("exactly five distinct fixtures required")
        paths=[x["note"] for x in fixture_data]
        if len(set(paths))!=5 or any(not x.startswith(KEEP) for x in paths):
            raise ValueError("fixture scope mismatch")
        notes=paths
    allowed_infra={"tools/org_museum_release_v1.py","tools/release-v1-fixtures.json",
                   "tools/org-museum-release-v1.md","tools/test_org_museum_release_v1.py",
                   ".github/workflows/org-museum-release-v1.yml"}
    outside=[f for f in infra if f not in allowed_infra]
    if fixture_data:
        status="FIXTURE_PENDING"
    elif notes and not infra:
        status="PASS"
    elif not notes and not assets and not outside:
        status="INFRA_ONLY"
    else:
        status="BLOCK"
    report={"schemaVersion":1,"commit":head,"base":base,
      "gate":status,
      "notes":[],"assets":assets,"infra":infra,
      "contentQuality":"REQUIRES_HUMAN_REVIEW","imageQuality":"REQUIRES_HUMAN_REVIEW"}
    if notes:
        allowed=all(f.startswith(KEEP) and f.count("/")>=3 for f in notes)
        if not allowed:report["gate"]="BLOCK"
        if infra: report["gate"]="BLOCK"
        for rel in notes:
            path=ROOT/rel
            if not path.is_file():raise ValueError("deleted/absent changed note: "+rel)
            data=path.read_text(encoding="utf-8")
            meta=parse_header(data)
            for key in FIELDS:
                if not meta.get(key): raise ValueError(rel+": missing "+key)
            if meta["WIKI_ID"]!=path.stem:raise ValueError(rel+": identity/filename mismatch")
            if meta["WIKI_STATUS"] not in {"published","draft"}:raise ValueError(rel+": invalid status")
            body_assets=re.findall(r"\[\[file:([^]\n]+)\]\]",data)
            for target in body_assets:
                dest=(path.parent/urllib.parse.unquote(target.split("::",1)[0])).resolve()
                if not dest.is_file() or not dest.is_relative_to(ROOT/"note-assets"):
                    raise ValueError(rel+": broken/misplaced attachment "+target)
            report["notes"].append({"path":rel,"id":meta["WIKI_ID"],"title":meta["TITLE"],
              "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
              "source":meta["SOURCE"],"assets":len(body_assets),"sections":headings(data)})
    if not args.fixtures and report["notes"]:
        report["sourceCollisions"]=find_published_source_collisions(ROOT, added, report["notes"])
        if report["sourceCollisions"]:
            report["gate"]="BLOCK"
            for found in report["sourceCollisions"]:
                print("V1_SOURCE_COLLISION",json.dumps(found,ensure_ascii=False))
    if args.fixtures:
        for x in fixture_data:
            p=ROOT/x["note"]
            if not (p.exists() and x["sha256"] and x["source_blob"]):
                raise ValueError("unverified fixture: "+x["id"])
        report["fixtures"]=fixture_data
        # Integration of five real source files is not a release approval.
        report["gate"]="FIXTURE_PASS" if len(report["notes"])==5 else "BLOCK"
    if args.site:
        report["_site"]=args.site
        relobj=ROOT/args.site/"museum-release.json"
        if not relobj.is_file():raise ValueError("canonical publisher did not create museum-release.json")
        release=json.loads(relobj.read_text(encoding="utf-8"))
        byid={n["id"]:n for n in release.get("notes",[])}
        for note in report["notes"]:
            emitted=byid.get(note["id"])
            if not emitted or emitted["sha256"]!=note["sha256"]:
                raise ValueError("export/source checksum mismatch for "+note["id"])
            export=ROOT/args.site/emitted["href"]
            if not export.is_file() or note["title"] not in export.read_text(encoding="utf-8"):
                raise ValueError("canonical article HTML absent or wrong title")
            note["export"]=emitted["href"]
            note["exportVerified"]=True
        report["realOrgExporter"]="PASS"
        report["publisherCommit"]=release.get("sourceCommit")
    folder=ROOT/args.output
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    generate_html(report,folder)
    print("V1_AUDIT",report["gate"],len(report["notes"]),"notes",len(report.get("fixtures",[])),"sources")
    # Never call the content quality passed: it remains a separate human/model gate.
    if report["gate"]=="BLOCK":
        raise SystemExit(1)
    if args.fixtures and (len(report["notes"])!=5 or any(not x.get("exportVerified") for x in report["notes"])):
        raise ValueError("five fixture files have not been independently matched to the exported HTML")

def generate_html(report,folder):
    # No external scripts, styles or networks. Full Org source and actual exported HTML
    # are both visible; the latter is inert srcdoc to avoid executing user scripts.
    menu=[];panels=[]
    for i,entry in enumerate(report["notes"]):
        path=ROOT/entry["path"]
        org=path.read_text(encoding="utf-8")
        img=""
        match=re.search(r"\[\[file:([^]\n]+\.(?:png|jpe?g|webp))\]\]",org,re.I)
        if match:
            src=(path.parent/urllib.parse.unquote(match.group(1))).resolve()
            if src.is_relative_to(ROOT/"note-assets") and src.stat().st_size<2500000:
                ext=src.suffix.lower()
                mime="image/webp" if ext==".webp" else ("image/png" if ext==".png" else "image/jpeg")
                img="<img class='header' alt='实测源图片' src='data:"+mime+";base64,"+base64.b64encode(src.read_bytes()).decode()+"'>"
        exported=""
        if entry.get("export"):
            page=ROOT/report.get("_site","_site")/entry["export"]
            if page.is_file():
                exported=page.read_text(encoding="utf-8")
        tag="p"+str(i)
        menu.append("<button onclick=\"show('"+tag+"')\">"+html.escape(entry["title"])+"</button>")
        sections="<p class='small'>"+html.escape(" · ".join(entry["sections"]))+"</p>"
        preview=("<details><summary>正式导出 HTML（只读源代码）</summary><pre>"+html.escape(exported[:350000])+"</pre></details>") if exported else ""
        panels.append("<section id='"+tag+"' class='panel'>"+img+"<h2>"+html.escape(entry["title"])+"</h2>"+sections+
          "<p><b>源码：</b>"+html.escape(entry["path"])+"</p><p><b>SHA256：</b><code>"+entry["sha256"]+"</code></p>"+
          "<details open><summary>Org 正文</summary><pre>"+html.escape(org)+"</pre></details>"+preview+"</section>")
    data=json.dumps(report,ensure_ascii=False)
    app="""<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Org Museum 发布流水线 V1 · Review</title>
<style>body{font:15px/1.7 system-ui,'Noto Sans SC',sans-serif;color:#243142;background:#f6f5f1;margin:0}
header{background:#102c37;color:white;padding:36px max(18px,calc((100vw - 1150px)/2))}
h1{font-size:32px;letter-spacing:-.025em;margin:0}header p{opacity:.8}main{max-width:1150px;margin:auto;padding:28px 18px}
nav{display:flex;gap:9px;flex-wrap:wrap;margin:20px 0}button{border:1px solid #cad5d9;background:white;color:#20323b;cursor:pointer;border-radius:9px;padding:10px 15px;font-size:14px}
.panel{display:none;background:white;border:1px solid #e1e5e8;border-radius:16px;padding:25px;margin:18px 0;box-shadow:0 4px 18px #102c370b}
.panel:first-of-type{display:block}.header{width:100%;max-height:420px;object-fit:contain;border-radius:8px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #e6e6e6;background:#f8f9fa;padding:18px;border-radius:10px;font:13px/1.65 ui-monospace,monospace;max-height:680px;overflow:auto}
summary{cursor:pointer;font-weight:600;margin:13px 0}code{overflow-wrap:anywhere;word-break:break-word}section p.small{color:#67757a;font-size:13px}
.cards{display:flex;gap:12px;flex-wrap:wrap}.cards div{padding:16px;background:#fff;border:1px solid #dce2e4;border-radius:12px;min-width:160px;flex:1}
footer{color:#62727a;margin:35px 0}@media(max-width:600px){header{padding:22px 16px}h1{font-size:23px}.panel{padding:13px}pre{font-size:12px}}
</style><header><h1>Org Museum · 发布流水线 V1</h1><p>真实 Emacs 预览 / 来源快照 / 人工内容放行严格分离</p></header>
<main><div class="cards"><div><strong>发布门禁</strong><p>__GATE__</p></div><div><strong>源码候选</strong><p>__COUNT__</p></div>
<div><strong>内容评价</strong><p>待独立 Review</p></div><div><strong>自动公开发布</strong><p>禁止</p></div></div>
<p>这份 Review 只能证明结构、来源与真实导出，不能证明文章优于原文，也不能代替图片审稿。测试样本不会合并到公开站点。</p>
<nav>__BUTTONS__</nav>__PANELS__<footer>基线 <code>__BASE__</code>　当前 <code>__HEAD__</code>。请在合并前进行人工内容与图片审核。</footer></main>
<script>function show(id){document.querySelectorAll('.panel').forEach(x=>x.style.display=x.id===id?'block':'none')}
</script></html>"""
    app=app.replace("__GATE__",html.escape(report["gate"])).replace("__COUNT__",str(len(report["notes"]))).replace("__BUTTONS__","".join(menu)).replace("__PANELS__","".join(panels)).replace("__BASE__",report["base"][:12]).replace("__HEAD__",report["commit"][:12])
    (folder/"review.html").write_text(app,encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    f=sub.add_parser("fixtures")
    f.add_argument("--manifest",default="tools/release-v1-fixtures.json")
    f.add_argument("--output",default="_review/fixtures.json")
    a=sub.add_parser("audit")
    a.add_argument("--base",required=True)
    a.add_argument("--output",default="_review")
    a.add_argument("--fixtures",default="")
    a.add_argument("--site",default="")
    args=p.parse_args()
    if args.cmd=="fixtures":stage_fixtures(args)
    else:audit(args)
if __name__=="__main__":main()
