#!/usr/bin/env python3
"""Regression: originally blocked article cleanup with user-approved exact removal scope."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_publisher" / "tools"))
import museum_update as m
from museum_pipeline import Invalid

PATH = "notes/knowledge/citizen-rights-safety/7fbbd925-3040-46ec-8f86-4cad706eb8ad.org"
ORIGINAL = "5c2307711f370c98548d5608b743b0f724d44598"
FOCUSED = "510d3dea9d6dfc70f0c3518768ca9f5dda74268b"

def git_at(sha):
    return subprocess.check_output(["git", "show", f"{sha}:{PATH}"], encoding="utf-8")

original, focused = git_at(ORIGINAL), git_at(FOCUSED)
scope = {
    "user_directive": "移除 Twitter 等与公民安全防护文章主题无关的内容",
    "heading references": ["隐语不是可靠加密", "表达内容与干预风险不完全等同"],
    "references": [
        "https://aclanthology.org/W18-4203/",
        "https://arxiv.org/abs/2606.27314",
        "https://gking.harvard.edu/files/censored.pdf",
    ]
}
m.validate_update(original, focused, scope)
for attempted in (None, {"user_directive": scope["user_directive"], "heading references": scope["heading references"]}):
    try:
        m.validate_update(original, focused, attempted)
    except Invalid:
        pass
    else:
        raise AssertionError("Unscoped or incomplete cleanup unexpectedly accepted")
print("PASS: real citizen-safety article cleanup with exact user-authorized scope")
