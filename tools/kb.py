#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb.py — 以 HTML 为本体的最小可跑版

三态：active（摊桌上）/ archived（收抽屉）/ tombstone（贴条）
真相：blocks/ 下的块文件 + meta/blocks.json 清单
派生：index.html（看板）与 dist/<proj>.html（合成品）都由清单生成，可随时重建

用法：
    python kb.py scan                 # 扫块 → 更新清单 → 重建看板与合成品
    python kb.py status               # 看当前三态
    python kb.py touch k-03 --back 10 # 记一次引用；--back N 把时间倒推 N 天（演示用）
    python kb.py archive              # 按规则收抽屉（默认 7 天未引用）
    python kb.py restore k-03         # 从抽屉取回
    python kb.py tomb k-05 --why "..."  # 贴条：删正文，只留理由
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / "projects" / "demo"
BLOCKS = PROJ / "blocks"
ARCHIVED = PROJ / "archived"
META = PROJ / "meta" / "blocks.json"
TOMBS = PROJ / "meta" / "tombs.json"
DIST = PROJ / "dist"

ACTIVE_CAP = 40     # 桌上最多放多少块（经验值，不是算出来的）
STALE_DAYS = 7      # 超过几天没动就收抽屉


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def parse_block(path: Path):
    """从块文件里提取 id 与标题。id 来自 data-block，不可改。"""
    html = path.read_text(encoding="utf-8")
    m = re.search(r'data-block="([^"]+)"', html)
    if not m:
        return None, None, html
    bid = m.group(1)
    t = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    title = re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else bid
    return bid, title, html


def gist_of(html: str, limit: int = 46) -> str:
    """取块的第一句像样的话，做目录里的一句话摘要。"""
    body = re.sub(r"<h2[^>]*>.*?</h2>", "", html, flags=re.S)
    texts = re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
    for t in texts:
        plain = re.sub(r"<[^>]+>", "", t).strip()
        plain = re.sub(r"\s+", "", plain)
        if len(plain) >= 12:
            return plain[:limit] + ("…" if len(plain) > limit else "")
    return ""


# ---------------------------------------------------------------- scan
def cmd_scan(args) -> int:
    META.parent.mkdir(parents=True, exist_ok=True)
    old = {b["id"]: b for b in load(META, {"blocks": []})["blocks"]}
    found, seen = [], set()

    for path in sorted(BLOCKS.glob("*.html")):
        bid, title, html = parse_block(path)
        if not bid:
            print(f"  ! 跳过（无 data-block）：{path.name}")
            continue
        seen.add(bid)
        prev = old.get(bid, {})
        found.append({
            "id": bid,
            "file": path.name,
            "title": title,
            "gist": gist_of(html),
            "state": prev.get("state", "active"),
            "created": prev.get("created", now()),
            "lastUsed": prev.get("lastUsed", now()),
            "hash": digest(html),
        })

    lost = set(old) - seen
    for bid in lost:
        print(f"  ! 清单里有、磁盘上没有：{bid}（可能是被贴条或误删）")

    save(META, {"project": "demo", "updated": now(),
                "cap": ACTIVE_CAP, "staleDays": STALE_DAYS, "blocks": found})

    render()
    act = sum(1 for b in found if b["state"] == "active")
    arc = sum(1 for b in found if b["state"] == "archived")
    print(f"✓ 扫描完成：{len(found)} 块（摊桌上 {act} · 抽屉 {arc}）")
    print("  → 已重建 index.html（看板）与 dist/demo.html（合成品）")
    return 0


# ---------------------------------------------------------------- status
def cmd_status(args) -> int:
    data = load(META, {"blocks": []})
    tombs = load(TOMBS, {"tombs": []})
    if not data["blocks"]:
        print("清单是空的，先跑 python kb.py scan")
        return 1

    print(f"\n项目：{data['project']}    更新：{data.get('updated','—')}")
    print(f"阈值：桌上上限 {data.get('cap')} 块 · {data.get('staleDays')} 天未动即收\n")

    for state, label in [("active", "摊桌上"), ("archived", "收抽屉")]:
        rows = [b for b in data["blocks"] if b["state"] == state]
        print(f"【{label}】{len(rows)} 块")
        for b in rows:
            days = (datetime.now() - datetime.strptime(b["lastUsed"], "%Y-%m-%d")).days
            print(f"  {b['id']:<6} {b['title'][:20]:<22} 最后用到 {days} 天前")
        print()

    print(f"【贴条】{len(tombs.get('tombs', []))} 条")
    for t in tombs.get("tombs", []):
        print(f"  {t['id']:<6} {t['title'][:18]:<20} ← {t['why']}")
    print()
    return 0


# ---------------------------------------------------------------- touch
def cmd_touch(args) -> int:
    data = load(META, {"blocks": []})
    for b in data["blocks"]:
        if b["id"] == args.id:
            if args.back:
                b["lastUsed"] = (datetime.now() - timedelta(days=args.back)).strftime("%Y-%m-%d")
            else:
                b["lastUsed"] = now()
            save(META, data)
            print(f"✓ {b['id']} 的最后引用时间 → {b['lastUsed']}")
            return 0
    print(f"✗ 找不到 {args.id}")
    return 1


# ---------------------------------------------------------------- archive
def cmd_archive(args) -> int:
    data = load(META, {"blocks": []})
    ARCHIVED.mkdir(parents=True, exist_ok=True)
    moved = []

    for b in data["blocks"]:
        if b["state"] != "active":
            continue
        days = (datetime.now() - datetime.strptime(b["lastUsed"], "%Y-%m-%d")).days
        if days >= (args.days or data.get("staleDays", STALE_DAYS)):
            src = BLOCKS / b["file"]
            if src.exists():
                shutil.move(str(src), str(ARCHIVED / b["file"]))
                b["state"] = "archived"
                moved.append((b["id"], b["title"], days))

    if not moved:
        print("✓ 没有需要收的块（都还在用）")
        return 0

    save(META, data)
    render()
    print(f"✓ 已收进抽屉 {len(moved)} 块：")
    for bid, title, days in moved:
        print(f"  {bid}  {title}（{days} 天没动）")
    print("  正文仍在 archived/，说一声就能取回")
    return 0


# ---------------------------------------------------------------- restore
def cmd_restore(args) -> int:
    data = load(META, {"blocks": []})
    for b in data["blocks"]:
        if b["id"] == args.id:
            if b["state"] != "archived":
                print(f"  {b['id']} 本来就在桌上")
                return 0
            src = ARCHIVED / b["file"]
            if not src.exists():
                print(f"✗ 抽屉里找不到文件 {b['file']}")
                return 1
            shutil.move(str(src), str(BLOCKS / b["file"]))
            b["state"] = "active"
            b["lastUsed"] = now()
            save(META, data)
            render()
            print(f"✓ {b['id']} 已从抽屉取回，放回桌上")
            return 0
    print(f"✗ 找不到 {args.id}")
    return 1


# ---------------------------------------------------------------- tomb
def cmd_tomb(args) -> int:
    if not args.why:
        print("✗ 必须写 --why：「为什么不行」是贴条唯一值钱的地方")
        return 1
    data = load(META, {"blocks": []})
    tombs = load(TOMBS, {"tombs": []})
    for b in data["blocks"]:
        if b["id"] == args.id:
            for d in (BLOCKS, ARCHIVED):
                f = d / b["file"]
                if f.exists():
                    f.unlink()          # 正文不存，只留理由
            data["blocks"] = [x for x in data["blocks"] if x["id"] != args.id]
            tombs["tombs"].append({
                "id": b["id"], "title": b["title"], "why": args.why, "at": now(),
            })
            save(META, data)
            save(TOMBS, tombs)
            render()
            print(f"✓ {b['id']} 已贴条：{args.why}")
            print("  正文已删，理由留下——将来 AI 再提同样方案，翻这条")
            return 0
    print(f"✗ 找不到 {args.id}")
    return 1


# ---------------------------------------------------------------- render
CSS = """
:root{--bg:#0b0910;--panel:#191521;--panel2:#15111c;--line:#2c2538;--line2:#443a55;
--txt:#eae4f0;--txt2:#ab9fbb;--txt3:#77708a;--jade:#6fd6c4;--cu:#e0a878;--vi:#b892d4;--red:#e88a8a;
--sans:"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
--serif:"Noto Serif SC","Songti SC",Georgia,serif;
--mono:"JetBrains Mono",Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:var(--sans);line-height:1.75;
background-image:radial-gradient(900px 500px at 85% -10%,rgba(184,146,212,.12),transparent 55%),radial-gradient(700px 400px at 5% 5%,rgba(111,214,196,.07),transparent 50%)}
.wrap{max-width:1040px;margin:0 auto;padding:0 26px}
header{padding:58px 0 26px}
.kick{font-family:var(--mono);font-size:11px;letter-spacing:.2em;color:var(--cu);margin-bottom:14px}
h1{font-family:var(--serif);font-size:clamp(26px,3.6vw,38px);margin:0 0 12px;line-height:1.25}
h1 em{font-style:normal;color:var(--jade)}
.lead{color:var(--txt2);font-size:15.5px;max-width:640px;margin:0 0 18px}
.meta{display:flex;gap:14px;flex-wrap:wrap;font-family:var(--mono);font-size:11.5px;color:var(--txt3)}
.pill{display:inline-block;font-family:var(--mono);font-size:10.5px;padding:2px 8px;border-radius:99px;border:1px solid;line-height:1.7}
.p-jade{color:var(--jade);border-color:rgba(111,214,196,.4);background:rgba(111,214,196,.09)}
.p-cu{color:var(--cu);border-color:rgba(224,168,120,.4);background:rgba(224,168,120,.09)}
.p-vi{color:var(--vi);border-color:rgba(184,146,212,.4);background:rgba(184,146,212,.09)}
.p-gray{color:var(--txt3);border-color:var(--line2);background:var(--panel2)}
main{padding:10px 0 70px}
h2.sec{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--txt3);text-transform:uppercase;
margin:26px 0 14px;font-weight:400;display:flex;align-items:center;gap:12px}
h2.sec::after{content:"";flex:1;height:1px;background:var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:13px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:17px 19px;
transition:.24s;position:relative;overflow:hidden;display:block;text-decoration:none;color:inherit}
.card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--jade);opacity:0;transition:.24s}
.card:hover{transform:translateY(-2px);border-color:var(--line2);background:var(--panel2)}
.card:hover::before{opacity:1}
.card.dim{opacity:.55}
.card .id{font-family:var(--mono);font-size:10.5px;color:var(--txt3);margin-bottom:7px;display:flex;gap:8px;align-items:center}
.card h3{font-family:var(--serif);font-size:16.5px;margin:0 0 8px;line-height:1.4}
.card p{font-size:13px;color:var(--txt2);margin:0 0 11px;line-height:1.65}
.card .foot{font-family:var(--mono);font-size:10.5px;color:var(--txt3);border-top:1px solid var(--line);padding-top:9px}
footer{border-top:1px solid var(--line);padding:22px 0 44px;font-family:var(--mono);font-size:11px;color:var(--txt3);line-height:1.9}
footer a{color:var(--jade);text-decoration:none;border-bottom:1px solid rgba(111,214,196,.3)}
/* 连读视图 */
article{padding-top:8px}
article section{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin:14px 0}
article h2{font-family:var(--serif);font-size:20px;margin:0 0 12px}
article p{color:var(--txt2);font-size:14.5px;margin:0 0 12px}
article b{color:var(--txt)}
article table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}
article th,article td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
article th{font-family:var(--mono);font-size:10.5px;color:var(--txt3);font-weight:400;text-transform:uppercase}
"""


def render() -> None:
    data = load(META, {"blocks": []})
    tombs = load(TOMBS, {"tombs": []}).get("tombs", [])
    blocks = data["blocks"]
    act = [b for b in blocks if b["state"] == "active"]
    arc = [b for b in blocks if b["state"] == "archived"]

    # ---------- 看板 ----------
    def card(b, dim=False):
        days = (datetime.now() - datetime.strptime(b["lastUsed"], "%Y-%m-%d")).days
        tag = ('<span class="pill p-jade">摊桌上</span>' if b["state"] == "active"
               else '<span class="pill p-gray">收抽屉</span>')
        return (f'<a class="card{" dim" if dim else ""}" href="dist/demo.html#{b["id"]}">'
                f'<div class="id">{b["id"]} {tag}</div>'
                f'<h3>{b["title"]}</h3><p>{b["gist"] or "（无摘要）"}</p>'
                f'<div class="foot">最后用到 {days} 天前 · {b["hash"]}</div></a>')

    tomb_html = "".join(
        f'<div class="card dim"><div class="id">{t["id"]} <span class="pill p-cu">贴条</span></div>'
        f'<h3>{t["title"]}</h3><p>为什么不行：{t["why"]}</p>'
        f'<div class="foot">正文已删 · 理由保留</div></div>' for t in tombs)

    board = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>demo 项目 · 看板</title><style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <div class="kick">KunPeng-Ops / 项目看板</div>
  <h1>demo 项目 · <em>看板</em></h1>
  <p class="lead">这是开发态：每块内容一张卡，标着它在哪一态。点卡片跳到合成品的对应位置。
  正式交付看 <a href="dist/demo.html" style="color:var(--jade)">连读版</a>。</p>
  <div class="meta">
    <span>摊桌上 {len(act)}</span><span>收抽屉 {len(arc)}</span><span>贴条 {len(tombs)}</span>
    <span class="pill p-jade">上限 {data.get('cap')} 块</span>
    <span class="pill p-gray">{data.get('staleDays')} 天未动即收</span>
  </div>
</header>
<main>
  <h2 class="sec">摊桌上 · {len(act)}</h2>
  <div class="grid">{''.join(card(b) for b in act) or '<p style="color:var(--txt3)">没有内容块</p>'}</div>
  {'<h2 class="sec">收抽屉 · ' + str(len(arc)) + '</h2><div class="grid">' + ''.join(card(b, True) for b in arc) + '</div>' if arc else ''}
  {'<h2 class="sec">贴条 · ' + str(len(tombs)) + '</h2><div class="grid">' + tomb_html + '</div>' if tombs else ''}
</main>
<footer>由 <code>tools/kb.py scan</code> 生成 · 不手写 · 真相在 blocks/ 与 meta/blocks.json</footer>
</div></body></html>"""

    # ---------- 合成品（只含 active，连读） ----------
    parts = []
    for b in act:
        raw = (BLOCKS / b["file"]).read_text(encoding="utf-8")
        raw = re.sub(r"^<!--.*?-->\s*", "", raw, flags=re.S)
        parts.append(raw)

    toc = "".join(f'<a href="#{b["id"]}">{b["title"]}</a>' for b in act)
    dist = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>demo 项目 · 连读</title><style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <div class="kick">KunPeng-Ops / 交付态</div>
  <h1>demo 项目 · <em>连读版</em></h1>
  <p class="lead">这是交付态：<b>只含摊在桌上的 {len(act)} 块</b>，抽屉里的和已贴条的不进来。
  合成发生在发布这一刻，产物是单个文件。</p>
  <div class="meta"><span class="pill p-jade">单文件 · 可发可归档</span><span>{data.get('updated','—')} 生成</span></div>
  <div class="meta" style="margin-top:10px">{toc}</div>
</header>
<main><article>{''.join(parts)}</article></main>
<footer>由 <code>tools/kb.py scan</code> 合成 · 回到 <a href="../index.html">看板</a></footer>
</div></body></html>"""

    (PROJ / "index.html").write_text(board, encoding="utf-8")
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "demo.html").write_text(dist, encoding="utf-8")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="以 HTML 为本体的最小可跑版")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("scan", help="扫块、更新清单、重建看板与合成品").set_defaults(fn=cmd_scan)
    sub.add_parser("status", help="看当前三态").set_defaults(fn=cmd_status)
    p = sub.add_parser("archive", help="按规则收抽屉")
    p.add_argument("--days", type=int)
    p.set_defaults(fn=cmd_archive)

    p = sub.add_parser("touch", help="记一次引用"); p.add_argument("id"); p.add_argument("--back", type=int)
    p.set_defaults(fn=cmd_touch)
    p = sub.add_parser("restore", help="从抽屉取回"); p.add_argument("id"); p.set_defaults(fn=cmd_restore)
    p = sub.add_parser("tomb", help="贴条"); p.add_argument("id"); p.add_argument("--why")
    p.set_defaults(fn=cmd_tomb)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
