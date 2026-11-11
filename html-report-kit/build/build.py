#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KunPeng Report Kit · 构建脚本
把 kit.css / kit.js 内联进每个模板，产出可独立分发、可邮件归档的单文件 HTML。

用法：
    python build.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

CSS_TAG = re.compile(r'<link\s+rel="stylesheet"\s+href="kit\.css"\s*/?>')
JS_TAG = re.compile(r'<script\s+src="kit\.js"\s*>\s*</script>')


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
