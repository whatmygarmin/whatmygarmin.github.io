#!/usr/bin/env python3
"""
note → このサイトへの自動取り込み。

note に投稿済みの記事を note の（非公式）APIから取得し、
posts/ に Markdown として保存する。すでに取り込み済みの記事、
同じタイトルの記事（手元に原本がある記事）はスキップする。

使い方:
    python3 fromnote.py            # NOTE_USERNAME のアカウントから取り込み
    python3 fromnote.py <urlname>  # アカウントを指定して取り込み

urlname は note.com/○○○ の ○○○ の部分。
環境変数 NOTE_USERNAME でも指定できる（GitHub Actions 用）。

依存: 標準ライブラリのみ。
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"

NOTE_USERNAME = "fancy_racoon582"  # note.com/fancy_racoon582

API_LIST = "https://note.com/api/v2/creators/{user}/contents?kind=note&page={page}"
API_NOTE = "https://note.com/api/v3/notes/{key}"
UA = "Mozilla/5.0 (my-media sync; +https://github.com/whatmygarmin)"


def api_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def list_notes(user: str):
    """公開済みのテキスト記事を新しい順に列挙する。"""
    page = 1
    while True:
        data = api_get(API_LIST.format(user=user, page=page))["data"]
        for c in data["contents"]:
            if c.get("type") == "TextNote" and c.get("status") == "published":
                yield c
        if data.get("isLastPage", True):
            break
        page += 1


def html_to_md(html: str) -> str:
    """note の本文HTMLを、このサイト用の素直な Markdown に変換する。"""
    text = html
    # 図（画像）: <figure>…<img src>…<figcaption> → ![caption](src)
    def figure(m):
        src = re.search(r'src="([^"]+)"', m.group(0))
        cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", m.group(0), re.S)
        alt = re.sub(r"<[^>]+>", "", cap.group(1)).strip() if cap else ""
        return f"\n\n![{alt}]({src.group(1)})\n\n" if src else "\n\n"
    text = re.sub(r"<figure[^>]*>.*?</figure>", figure, text, flags=re.S)
    text = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', r"\n\n![](\1)\n\n", text)

    # 見出し・区切り・引用
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n\n## \1\n\n", text, flags=re.S)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n\n### \1\n\n", text, flags=re.S)
    text = re.sub(r"<hr[^>]*>", "\n\n---\n\n", text)
    text = re.sub(
        r"<blockquote[^>]*>(.*?)</blockquote>",
        lambda m: "\n\n"
        + "\n".join("> " + ln for ln in re.sub(r"</?p[^>]*>", "\n", m.group(1)).strip().splitlines() if ln.strip())
        + "\n\n",
        text,
        flags=re.S,
    )

    # 箇条書き（li 内の <p> は改行にせず1行にまとめる）
    text = re.sub(
        r"<li[^>]*>(.*?)</li>",
        lambda m: "\n- " + re.sub(r"\s+", " ", re.sub(r"<(?!/?(strong|b|em|i|a)\b)[^>]+>", " ", m.group(1))).strip(),
        text,
        flags=re.S,
    )
    text = re.sub(r"</?[uo]l[^>]*>", "\n", text)

    # 段落・改行・強調・リンク
    text = re.sub(r"<br\s*/?>", "  \n", text)
    text = re.sub(r"<p[^>]*>", "\n\n", text)
    text = re.sub(r"</p>", "", text)
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.S)
    text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.S)
    text = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.S)

    # 残ったタグは落とし、HTMLエンティティを戻す
    text = re.sub(r"<[^>]+>", "", text)
    for ent, ch in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                    ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")]:
        text = text.replace(ent, ch)

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def existing_keys_and_titles():
    """取り込み済み判定用に、posts/ 内の note キーとタイトルを集める。"""
    keys, titles = set(), set()
    for p in POSTS_DIR.glob("*.md"):
        head = p.read_text(encoding="utf-8")[:600]
        m = re.search(r"^source:.*?/n/(n[0-9a-f]+)", head, re.M)
        if m:
            keys.add(m.group(1))
        m = re.search(r"^title:\s*(.+)$", head, re.M)
        if m:
            titles.add(m.group(1).strip())
    return keys, titles


def import_note(user: str, item: dict) -> bool:
    """記事1本を取り込む。新規に書いたら True。"""
    key = item["key"]
    detail = api_get(API_NOTE.format(key=key))["data"]

    title = detail["name"]
    date = (detail.get("publish_at") or item.get("publishAt", ""))[:10]
    url = f"https://note.com/{user}/n/{key}"
    body = html_to_md(detail.get("body") or "")

    # タイトルの「はたと#002」などから連載番号を拾う
    m = re.search(r"[#＃](\d{1,3})", title)
    no_line = f"no: {int(m.group(1)):03d}\n" if m else ""

    md = (
        f"title: {title}\n"
        f"date: {date}\n"
        f"{no_line}"
        f"source: {url}\n"
        f"\n{body}\n"
    )
    out = POSTS_DIR / f"note-{key}.md"
    out.write_text(md, encoding="utf-8")
    print(f"取り込み: {title} → {out.name}")
    return True


def main():
    user = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("NOTE_USERNAME") or NOTE_USERNAME
    )
    if not user:
        sys.exit(
            "note のアカウント名が未設定です。\n"
            "  fromnote.py の NOTE_USERNAME に書くか、"
            "python3 fromnote.py <urlname> で指定してください。"
        )

    keys, titles = existing_keys_and_titles()
    new = 0
    for item in list_notes(user):
        if item["key"] in keys or item["name"].strip() in titles:
            continue
        if item.get("price", 0) > 0:
            print(f"スキップ（有料記事）: {item['name']}")
            continue
        new += import_note(user, item)

    print(f"完了: 新規 {new} 記事")


if __name__ == "__main__":
    main()
