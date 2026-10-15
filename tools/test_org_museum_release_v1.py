#!/usr/bin/env python3
"""Mutation/negative gates for Org Museum Release V1. No network required."""
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib

path=Path(__file__).resolve().parent/"org_museum_release_v1.py"
spec=importlib.util.spec_from_file_location("v1",path)
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
BASE="a"*40
HEAD="b"*40
ident="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
rel="notes/knowledge/test/"+ident+".org"
asset="note-assets/"+ident+"/cover.webp"
header=(
    "#+TITLE: 回归样本\n"
    "#+WIKI_ID: "+ident+"\n"
    "#+CATEGORY: 质量回归\n"
    "#+FILETAGS: :test:\n"
    "#+DATE: 2026-10-12\n"
    "#+SOURCE: https://example.org/test\n"
    "#+INGEST_ID: "+ident+"\n"
    "#+WIKI_STATUS: draft\n\n"
    "* 正文\n"
    "保留真实证据。\n"
)
checks=0
def scenario(source=header,paths=None,files=None,expect=None,with_site=False):
    global checks
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        p=root/rel;p.parent.mkdir(parents=True)
        if source is not None:p.write_text(source,encoding="utf-8")
        for name,content in (files or {}).items():
            q=root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(content)
        opts=SimpleNamespace(base=BASE,output="_review",fixtures="",site="_site" if with_site else "")
        if with_site:
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            export="pages/collected/knowledge/test/"+ident+".html"
            e=root/"_site"/export;e.parent.mkdir(parents=True,exist_ok=True)
            e.write_text("<html><h1>回归样本</h1></html>",encoding="utf-8")
            (root/"_site"/"museum-release.json").write_text(json.dumps({"notes":[{"id":ident,"href":export,"sha256":digest}],"sourceCommit":HEAD}),encoding="utf-8")
        def fake_git(*args):
            return HEAD if args[0]=="rev-parse" else "\n".join(paths if paths is not None else [rel])
        with patch.object(v,"ROOT",root),patch.object(v,"git",fake_git):
            try:v.audit(opts)
            except (ValueError,SystemExit):
                if expect!="fail":raise
            else:
                if expect=="fail":raise AssertionError("Expected rejection but candidate passed")
                if not (root/"_review"/"review.html").exists():raise AssertionError("no HTML review")
                report=json.loads((root/"_review"/"audit.json").read_text(encoding="utf-8"))
                if expect and report["gate"]!=expect:raise AssertionError("unexpected gate "+report["gate"])
                if report["contentQuality"]!="REQUIRES_HUMAN_REVIEW" or report["imageQuality"]!="REQUIRES_HUMAN_REVIEW":
                    raise AssertionError("false semantic approval")
    checks+=1

scenario(expect="PASS",with_site=True)
scenario(source=header.replace("#+SOURCE: https://example.org/test\n",""),expect="fail")
scenario(source=header.replace(ident,"11111111-2222-3333-4444-555555555555",1),expect="fail")
scenario(source=header+"[[file:../../../note-assets/"+ident+"/absent.webp]]",expect="fail")
scenario(paths=["note-assets/"+ident+"/orphan.webp"],files={asset:b"safe"},expect="fail")
scenario(paths=[rel,".github/workflows/publish.yml"],expect="fail")
scenario(paths=[".env"],expect="fail")
scenario(paths=["tools/org_museum_release_v1.py"],expect="INFRA_ONLY")
# Deterministic source/object hash regression, without network.
b=b"five independent real records"
assert v.blob_sha(b)==hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
assert v.blob_sha(b)!=v.blob_sha(b"tampered")
checks+=2

# A previously published source is a strong identity signal. Distinct revisions
# or percent-encoding must not allow silent cloning into a fresh WIKI_ID.
a="https://github.com/lovemoganna/Prompts/blob/"+"1"*40+"/Major/1.%E4%BB%80%E4%B9%88%E6%98%AF%E6%8F%90%E7%A4%BA%E8%AF%8D.md"
b="https://github.com/lovemoganna/Prompts/blob/"+"2"*40+"/Major/1.什么是提示词.md"
assert v.source_fingerprint(a)==v.source_fingerprint(b)
assert v.source_fingerprint(a)!=v.source_fingerprint("https://github.com/lovemoganna/Prompts/blob/"+"1"*40+"/Major/2.提示工程.md")
assert v.source_fingerprint("https://example.org/article")==None
assert v.source_fingerprint("anonymous notes")==None
checks+=4

old="notes/knowledge/old-source/11111111-2222-3333-4444-555555555555.org"
published=(
    "#+TITLE: 以前的文章\n"
    "#+SOURCE: "+b+"\n"
    "#+WIKI_STATUS: published\n"
)
draft=published.replace("published","draft")
candidate=header.replace("https://example.org/test",a)
scenario(source=candidate,files={old:published.encode("utf-8")},expect="fail")
scenario(source=candidate,files={old:draft.encode("utf-8")},expect="PASS")
scenario(source=candidate.replace(a,"https://github.com/lovemoganna/Prompts/blob/"+"1"*40+"/Major/another.md"),files={old:published.encode("utf-8")},expect="PASS")
checks+=0


# Regression against current repository state: any existing published page
# with the same source must block another WIKI_ID. No fixed duplicate count.
real_candidate={"path":"notes/knowledge/third-copy/faf7a6d8-bb10-4dde-bbc9-883e7358d199.org",
                "source":a}
real_conflicts=v.find_published_source_collisions(
    v.ROOT,[real_candidate["path"]],[real_candidate])
assert len(real_conflicts)==1, real_conflicts
assert len(real_conflicts[0]["alreadyPublished"])>=1, real_conflicts
assert v.find_published_source_collisions(v.ROOT,[],[real_candidate])==[]
checks+=3


# Serial-only invariant: no implicit iteration over all five manifest entries.
with tempfile.TemporaryDirectory() as tmp:
    manifest=Path(tmp)/"cases.json"
    manifest.write_text(json.dumps({"schemaVersion":1,"sourceRepository":"fixture",
      "sourceCommit":"a"*40,"cases":[{"id":"T01","sha":"abc"},{"id":"T02","sha":"def"}]}),encoding="utf-8")
    picked=v.load_manifest(str(manifest),"T01")
    assert len(picked["cases"])==1 and picked["cases"][0]["id"]=="T01"
    checks+=1
    for invalid in ("",None,"T01,T02","ALL","T99"):
        try:v.load_manifest(str(manifest),invalid)
        except ValueError:checks+=1
        else:raise AssertionError("Batch/invalid selector allowed: "+str(invalid))
second="notes/knowledge/other/22222222-3333-4444-5555-666666666666.org"
scenario(paths=[rel,second],files={second:header.replace(ident,"22222222-3333-4444-5555-666666666666").encode("utf-8")},expect="fail")
checks+=0

# Pre-authoring path: same source at two different published IDs must block a
# third page before any model or image token is spent.
with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    identA="11111111-1111-1111-1111-111111111111"
    identB="22222222-2222-2222-2222-222222222222"
    srcURL="https://github.com/lovemoganna/Prompts/blob/"+"a"*40+"/Major/4.%E6%8F%90%E7%A4%BA%E5%B7%A5%E5%85%B7.md"
    for idx, ident in enumerate((identA,identB)):
        p=root/"notes"/"knowledge"/("sample"+str(idx))/(ident+".org")
        p.parent.mkdir(parents=True)
        p.write_text("#+TITLE: 现有笔记"+str(idx)+"\n#+WIKI_ID: "+ident+"\n"
                     "#+WIKI_STATUS: published\n#+SOURCE: "+srcURL+"\n",encoding="utf-8")
    collision=v.preflight_source(root,srcURL.replace("a"*40,"b"*40))
    assert collision["decision"]=="UPDATE_OR_NOOP",collision
    assert collision["newArticleBlocked"] and collision["needsConsolidationReview"]
    assert len(collision["existingPublished"])==2
    assert all(x["id"] in (identA,identB) for x in collision["existingPublished"])
    assert collision["writeAuthorized"] is False and collision["quality"]=="NOT_EVALUATED"
    checks+=5
    fresh=v.preflight_source(root,srcURL.replace("/Major/4.","/Major/5."))
    assert fresh["decision"]=="NEW_CANDIDATE" and fresh["newArticleBlocked"] is False
    assert fresh["writeAuthorized"] is False
    checks+=2
    unknown=v.preflight_source(root,"https://example.org/unknown")
    assert unknown["decision"]=="SOURCE_UNVERIFIED" and unknown["writeAuthorized"] is False
    checks+=1
    draftPath=root/"notes"/"knowledge"/"draft"/("33333333-3333-3333-3333-333333333333.org")
    draftPath.parent.mkdir(parents=True)
    draftPath.write_text("#+TITLE: 草稿\n#+WIKI_STATUS: draft\n"
                         "#+SOURCE: https://github.com/lovemoganna/Prompts/blob/"
                         +"a"*40+"/Major/6.%E6%8F%90%E7%A4%BA%E8%BF%AD%E4%BB%A3.md\n",encoding="utf-8")
    in_progress=v.preflight_source(root,draftPath.read_text().split("#+SOURCE: ")[1].strip())
    assert in_progress["decision"]=="REUSE_DRAFT_OR_REVIEW" and in_progress["newArticleBlocked"]
    checks+=1

# Real, unmodified knowledge-base check: T01 source was already published,
# so new WIKI_ID is prohibited; no fixed number of existing pages assumed.
manifest=v.load_manifest(str(v.ROOT/"tools/release-v1-fixtures.json"),"T01")
case=manifest["cases"][0]
full="https://github.com/"+manifest["sourceRepository"]+"/blob/"+manifest["sourceCommit"]+"/"+case["path"]
existing=v.preflight_source(v.ROOT,full)
assert existing["decision"]=="UPDATE_OR_NOOP" and existing["existingPublished"]
assert existing["writeAuthorized"] is False
checks+=2


# Real corpus-only preflight (read-only): all five locked source files already
# have at least one published canonical note. Counts may change after an
# approved manual consolidation, so only identity and route are asserted.
real_manifest=json.loads((v.ROOT/"tools/release-v1-fixtures.json").read_text(encoding="utf-8"))
for entry in real_manifest["cases"]:
    source_url=("https://github.com/"+real_manifest["sourceRepository"]+"/blob/"
                +real_manifest["sourceCommit"]+"/"+entry["path"])
    result=v.preflight_source(v.ROOT,source_url)
    assert result["decision"]=="UPDATE_OR_NOOP",(entry["id"],result)
    assert result["existingPublished"],entry["id"]
    assert result["newArticleBlocked"] is True
    assert result["writeAuthorized"] is False
    checks+=1

print("PASS SERIAL_SINGLE_CASE_REGRESSION",checks)

