#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KunPeng Report Kit · 构建脚本
把 kit.css / kit.js 内联进每个模板，产出可独立分发、可邮件归档的单文件 HTML。

用法：
    python build.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

CSS_TAG = re.compile(r'<link\s+rel="stylesheet"\s+href="kit\.css"\s*/?>')
JS_TAG = re.compile(r'<script\s+src="kit\.js"\s*>\s*</script>')


LEDGER_SRC = OUT.parent / "annotations" / "report-2026-11-11.json"

TYPE_MAP = {
    "note": ("补充", "p-blue"), "reject": ("否决", "p-red"),
    "delegate": ("代议", "p-vi"), "agree": ("认可", "p-jade"),
}
STATE_MAP = {
    "done": ("已处理", "p-jade"), "pending": ("待补充", "p-cu"),
    "deferred": ("转后续", "p-gray"),
}


def build_ledger() -> str:
    """由批注 JSON 生成台账表格。台账不手写，避免与批注脱节。"""
    if not LEDGER_SRC.exists():
        return ""
    data = json.loads(LEDGER_SRC.read_text(encoding="utf-8"))
    rows = []
    for a in data.get("annotations", []):
        t, tc = TYPE_MAP.get(a.get("type", ""), ("其他", "p-gray"))
        dp = a.get("disposition") or {}
        st, sc = STATE_MAP.get(dp.get("status", "pending"), ("待定", "p-gray"))
        note = re.sub(r"\s+", " ", a.get("note", "")).strip()
        if len(note) > 42:
            note = note[:42] + "…"
        rows.append(
            '<tr><td style="white-space:nowrap"><code>%s</code></td>'
            '<td style="white-space:nowrap"><span class="pill %s">%s</span></td>'
            '<td>%s</td>'
            '<td style="white-space:nowrap"><span class="pill %s">%s</span></td>'
            '<td>%s</td></tr>'
            % (a.get("id", ""), tc, t, note, sc, st, dp.get("target", "—"))
        )
    return ('<div class="tbl"><table style="table-layout:fixed;min-width:640px">'
            '<colgroup><col style="width:62px"><col style="width:62px"><col>'
            '<col style="width:74px"><col style="width:150px"></colgroup>'
            '<thead><tr><th>编号</th><th>类型</th><th>你的意见</th><th>状态</th><th>落在哪</th></tr></thead>'
            '<tbody>' + "".join(rows) + '</tbody></table></div>')


def build_anno_marks(html: str) -> str:
    """给被批注过的块打上痕迹：编号 + 数量 + 轮次深浅（近三轮可见，越旧越淡）。"""
    if not LEDGER_SRC.exists():
        return html
    data = json.loads(LEDGER_SRC.read_text(encoding="utf-8"))
    agg = {}
    for a in data.get("annotations", []):
        agg.setdefault(a["block"], []).append(a)
    if not agg:
        return html

    maxr = max(a.get("round", 1) for a in data["annotations"])
    for block, items in agg.items():
        newest = max(i.get("round", 1) for i in items)
        gap = maxr - newest
        o = "1" if gap == 0 else ("0.55" if gap == 1 else "0.3")
        ids = ",".join(i["id"] for i in items)
        old = 'data-block="%s"' % block
        new = ('data-block="%s" data-anno="%s" data-anno-n="%d" data-anno-o="%s" title="被批注 %d 次：%s"'
               % (block, ids, len(items), o, len(items), ids))
        html = html.replace(old, new, 1)
    return html


def main() -> int:
    css = (HERE / "kit.css").read_text(encoding="utf-8")
    js = (HERE / "kit.js").read_text(encoding="utf-8")

    if "</style>" in css:
        print("!! kit.css 含 </style>，无法安全内联", file=sys.stderr)
        return 1
    if "</script>" in js:
        print("!! kit.js 含 </script>，无法安全内联", file=sys.stderr)
        return 1

    pages = sorted(HERE.glob("*.html"))
    if not pages:
        print("!! build/ 下没有 HTML", file=sys.stderr)
        return 1

    total = 0
    for p in pages:
        html = p.read_text(encoding="utf-8")
        n_css = len(CSS_TAG.findall(html))
        n_js = len(JS_TAG.findall(html))

        html = CSS_TAG.sub(lambda _m: "<style>\n" + css + "\n</style>", html)
        html = JS_TAG.sub(lambda _m: "<script>\n" + js + "\n</script>", html)

        # 批注台账：由 annotations/*.json 生成后注入占位区间
        if p.name == "report-html-native.html":
            ledger = build_ledger()
            if ledger:
                html = re.sub(
                    r"<!-- LEDGER:BEGIN -->[\s\S]*?<!-- LEDGER:END -->",
                    lambda _m: "<!-- LEDGER:BEGIN -->\n" + ledger + "\n      <!-- LEDGER:END -->",
                    html)
                print(f"     ↳ 台账已注入：{ledger.count('<tr>') - 1} 条")
            marked = len(re.findall(r'data-anno="', build_anno_marks(html)))
            html = build_anno_marks(html)
            print(f"     ↳ 批注痕迹：{marked} 个块")

        # 自检：内联后不应再有外部依赖
        stray = re.findall(r'(?:href|src)="(?!https?://|#|mailto:)([^"]+\.(?:css|js))"', html)
        if stray:
            print(f"!! {p.name} 仍有外部资源：{stray}", file=sys.stderr)
            return 1

        dest = OUT / p.name
        dest.write_text(html, encoding="utf-8")
        size = dest.stat().st_size
        total += 1
        print(f"  ✓ {p.name:<22} {size/1024:6.1f} KB   (css×{n_css} js×{n_js} 已内联)")

    # 需要在工作区根目录额外发布一份的成品：源名 → (根目录文件名, 链接改写表)
    ROOT_PUBLISH = {
        "tpl-paradigm-v2.html": (
            "HTML交互范式-研究报告-KIT版.html",
            {'href="../HTML交互范式-研究报告.html"': 'href="HTML交互范式-研究报告.html"'},
        ),
        "plan-html-native.html": (
            "HTML本体计划书.html",
            {'href="../HTML交互范式-研究报告-KIT版.html"':
             'href="HTML交互范式-研究报告-KIT版.html"'},
        ),
        "report-html-native.html": (
            "HTML本体-正式报告.html",
            # 全局替换会把 index.html 指向 kit 目录；报告首页要指根目录的
            # 报告库，所以这里再改回来。
            {'href="html-report-kit/index.html"': 'href="index.html"'},
        ),
    }
    for src_name, (dest_name, rewrites) in ROOT_PUBLISH.items():
        src = OUT / src_name
        if not src.exists():
            continue
        html = src.read_text(encoding="utf-8")
        html = html.replace('href="index.html"', 'href="html-report-kit/index.html"')
        for old, new in rewrites.items():
            html = html.replace(old, new)
        dest = OUT.parent / dest_name
        dest.write_text(html, encoding="utf-8")
        print(f"  ✓ 根目录发布        {dest_name:<26} {dest.stat().st_size/1024:6.1f} KB")

    print(f"\n完成：{total} 个单文件 HTML → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
