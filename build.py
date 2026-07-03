#!/usr/bin/env python3
"""
最小の静的サイトジェネレータ。

posts/ にある Markdown ファイル(*.md)を読み、
_site/posts/<名前>.html に1ページずつ変換し、
記事一覧つきのトップページ _site/index.html を作る。

使い方:
    python3 build.py        # _site/ を生成
依存:
    markdown   (pip install markdown)

デザインの方針: 記事の文体（静かな内省）に合わせた「読みもの」の見た目。
  生成り色の背景 / 明朝体 / ゆったりした行間。ダークモードにも対応。
"""

import re
import shutil
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "_site"
SITE_TITLE = "はたと"
SITE_TAGLINE = "ふと立ち止まった瞬間の、記録。"

# ---- ページ共通の HTML ひな形 ------------------------------------------------
PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="{og_type}">
<style>
  :root {{
    --paper: #f7f4ee;      /* 生成り（和紙） */
    --paper-deep: #f0ece2; /* 少し沈んだ生成り */
    --ink: #3a372f;        /* 墨色 */
    --ink-faint: #8f8a7d;  /* 薄墨 */
    --accent: #b5452a;     /* 朱（落款の赤） */
    --accent-pale: #f2ddd3;
    --line: #e2dcce;       /* 罫線 */
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --paper: #201e1a;
      --paper-deep: #262420;
      --ink: #d6d0c2;
      --ink-faint: #7d786c;
      --accent: #d97e5a;
      --accent-pale: #4a2e22;
      --line: #38352e;
    }}
  }}
  * {{ box-sizing: border-box; }}
  html {{ background: var(--paper); }}
  body {{
    font-family: "Hiragino Mincho ProN", "Yu Mincho", "YuMincho",
                 "Noto Serif JP", serif;
    /* ごく薄い横罫を敷いて、便箋の気配を出す */
    background:
      repeating-linear-gradient(
        to bottom,
        transparent 0, transparent 2.05rem,
        color-mix(in srgb, var(--line) 42%, transparent) 2.05rem,
        color-mix(in srgb, var(--line) 42%, transparent) calc(2.05rem + 1px)
      ),
      var(--paper);
    color: var(--ink);
    max-width: 37rem;
    margin: 0 auto;
    padding: 4rem 1.5rem 5rem;
    line-height: 2.05;
    letter-spacing: 0.03em;
    font-feature-settings: "palt";
    animation: appear 0.7s ease-out both;
  }}
  @keyframes appear {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: none; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    body {{ animation: none; }}
  }}
  ::selection {{ background: var(--accent-pale); }}
  a {{ color: var(--accent); text-decoration-color: var(--line);
       text-underline-offset: 0.3em; transition: text-decoration-color 0.25s; }}
  a:hover {{ text-decoration-color: var(--accent); }}

  /* サイト共通のヘッダ */
  header.site {{ margin-bottom: 4rem; }}
  header.site .site-title {{
    font-size: 1.6rem; font-weight: 600; letter-spacing: 0.5em; margin: 0;
  }}
  header.site .site-title a {{ color: var(--ink); text-decoration: none; }}
  /* 題字の脇に、落款のような朱の小さな印 */
  header.site .site-title a::after {{
    content: ""; display: inline-block; width: 0.42em; height: 0.42em;
    background: var(--accent); border-radius: 2px;
    margin-left: 0.55em; vertical-align: 0.08em;
  }}
  header.site .tagline {{
    color: var(--ink-faint); font-size: 0.8rem; letter-spacing: 0.18em;
    margin: 0.8rem 0 0;
  }}
  /* 記事ページのヘッダは控えめに */
  header.site.small .site-title {{
    font-size: 0.95rem; letter-spacing: 0.4em; font-weight: 400;
  }}
  header.site.small {{ margin-bottom: 3.2rem; }}

  /* 記事ページ */
  .post-meta {{
    color: var(--ink-faint); font-size: 0.78rem; letter-spacing: 0.2em;
    margin: 0 0 1rem;
  }}
  .post-meta .no {{ margin-right: 1.2em; }}
  .no {{ color: var(--accent); }}
  /* note へのリンク（取り込んだ記事に出す） */
  .alsoon {{ margin-top: 3.5rem; font-size: 0.85rem; }}
  .alsoon a {{ color: var(--accent); }}
  h1.post-title {{
    font-size: 1.45rem; font-weight: 600; line-height: 1.9;
    letter-spacing: 0.06em; margin: 0;
  }}
  article {{ margin-top: 3rem; }}
  article p {{ margin: 1.9em 0; }}
  article h1, article h2, article h3 {{
    font-weight: 600; letter-spacing: 0.08em; margin-top: 3em;
  }}
  article h1 {{ font-size: 1.2rem; }}
  article h2 {{ font-size: 1.1rem; }}
  article hr {{
    border: none; text-align: center; margin: 3em 0;
  }}
  article hr::after {{
    content: "＊"; color: var(--accent); letter-spacing: 1em;
  }}
  article blockquote {{
    margin: 2em 0; padding: 0 0 0 1.2em;
    border-left: 2px solid var(--line); color: var(--ink-faint);
  }}
  article code {{
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 0.85em; background: var(--paper-deep);
    padding: 0.15em 0.4em; border-radius: 3px;
  }}
  article pre {{
    background: var(--paper-deep); padding: 1em 1.2em; border-radius: 4px;
    overflow-x: auto; line-height: 1.6;
  }}
  article pre code {{ background: none; padding: 0; }}
  article img {{ max-width: 100%; }}

  /* 記事末尾の 前へ / 次へ */
  nav.adjacent {{
    margin-top: 5rem; padding-top: 1.6rem; border-top: 1px solid var(--line);
    display: flex; flex-direction: column; gap: 0.9rem;
    font-size: 0.9rem; line-height: 1.9;
  }}
  nav.adjacent .dir {{
    color: var(--ink-faint); font-size: 0.72rem; letter-spacing: 0.2em;
    display: block;
  }}
  nav.adjacent a {{ color: var(--ink); text-decoration: none; }}
  nav.adjacent a:hover {{ color: var(--accent); }}

  /* トップの記事一覧 */
  ul.posts {{ list-style: none; padding: 0; margin: 0; }}
  ul.posts li {{
    padding: 2rem 0; border-bottom: 1px solid var(--line); margin: 0;
  }}
  ul.posts li:first-child {{ border-top: 1px solid var(--line); }}
  ul.posts .meta {{
    color: var(--ink-faint); font-size: 0.75rem; letter-spacing: 0.2em;
    display: block; margin-bottom: 0.5rem;
  }}
  ul.posts .meta .no {{ margin-right: 1.2em; }}
  ul.posts a.entry {{
    color: var(--ink); text-decoration: none;
    font-size: 1.08rem; line-height: 1.95; font-weight: 600;
  }}
  ul.posts a.entry:hover {{ color: var(--accent); }}
  ul.posts .excerpt {{
    color: var(--ink-faint); font-size: 0.85rem; line-height: 1.9;
    margin: 0.7rem 0 0;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
  }}

  footer.site {{
    margin-top: 6rem; padding-top: 1.6rem; border-top: 1px solid var(--line);
    color: var(--ink-faint); font-size: 0.75rem; letter-spacing: 0.2em;
    display: flex; justify-content: space-between; align-items: center;
  }}
  footer.site a {{ color: var(--ink-faint); }}
  /* 縦書きの落款（朱印） */
  footer.site .seal {{
    writing-mode: vertical-rl; background: var(--accent); color: var(--paper);
    font-size: 0.68rem; letter-spacing: 0.25em; line-height: 1;
    padding: 0.55em 0.3em; border-radius: 3px; user-select: none;
  }}
</style>
</head>
<body>
{body}
<footer class="site"><span>{tagline}</span><span class="seal">{site_title}</span></footer>
</body>
</html>
"""


def parse_post(md_path: Path):
    """1つの Markdown ファイルを変換し、メタ情報つきの dict を返す。"""
    md = markdown.Markdown(extensions=["meta", "fenced_code", "tables"])
    html_body = md.convert(md_path.read_text(encoding="utf-8"))
    meta = md.Meta  # {'title': ['...'], 'date': ['...']} の形

    title = meta.get("title", [md_path.stem])[0]
    date = meta.get("date", [""])[0]
    source = meta.get("source", [""])[0]  # note から取り込んだ記事は元URL

    # 連載番号: no: メタ → ファイル名の -001- 形式 の順で拾う
    number = meta.get("no", [""])[0]
    if not number:
        m = re.search(r"-(\d{3})-", md_path.stem)
        number = m.group(1) if m else ""

    # 冒頭の一文を抜粋にする（HTMLタグを剥がして最初の80字）
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html_body)).strip()
    excerpt = text[:80].replace('"', "”")

    return {
        "title": title,
        "date": date,
        "number": number,
        "source": source,
        "excerpt": excerpt,
        "slug": md_path.stem,
        "html": html_body,
    }


def render_meta_row(post: dict) -> str:
    """『#001  2026-06-28』の行を作る（番号や日付が無ければ省く）。"""
    parts = []
    if post["number"]:
        parts.append(f'<span class="no">#{post["number"]}</span>')
    if post["date"]:
        parts.append(f'<span class="date">{post["date"]}</span>')
    return "".join(parts)


def write_post(post: dict, prev: dict | None, next_: dict | None):
    """記事1本を _site/posts/<slug>.html として書き出す。"""
    nav_items = []
    if next_:  # 新しい記事側
        nav_items.append(
            '<a href="{slug}.html"><span class="dir">次の記事</span>{title}</a>'.format(**next_)
        )
    if prev:  # 古い記事側
        nav_items.append(
            '<a href="{slug}.html"><span class="dir">前の記事</span>{title}</a>'.format(**prev)
        )
    nav = (
        '<nav class="adjacent">\n' + "\n".join(nav_items) + "\n</nav>"
        if nav_items
        else ""
    )

    alsoon = (
        f'<p class="alsoon"><a href="{post["source"]}">note でも読む →</a></p>\n'
        if post["source"]
        else ""
    )
    body = (
        '<header class="site small">\n'
        f'  <p class="site-title"><a href="../index.html">{SITE_TITLE}</a></p>\n'
        "</header>\n"
        f'<p class="post-meta">{render_meta_row(post)}</p>\n'
        f'<h1 class="post-title">{post["title"]}</h1>\n'
        f"<article>\n{post['html']}\n</article>\n"
        f"{alsoon}"
        f"{nav}"
    )
    out = OUT_DIR / "posts" / f"{post['slug']}.html"
    out.write_text(
        PAGE.format(
            title=f"{post['title']} | {SITE_TITLE}",
            description=post["excerpt"],
            og_type="article",
            body=body,
            site_title=SITE_TITLE,
            tagline=SITE_TAGLINE,
        ),
        encoding="utf-8",
    )


def write_index(posts: list):
    """記事一覧のトップページを書き出す。"""
    items = []
    for p in posts:
        items.append(
            "<li>\n"
            f'  <span class="meta">{render_meta_row(p)}</span>\n'
            f'  <a class="entry" href="posts/{p["slug"]}.html">{p["title"]}</a>\n'
            f'  <p class="excerpt">{p["excerpt"]}</p>\n'
            "</li>"
        )
    body = (
        '<header class="site">\n'
        f'  <h1 class="site-title"><a href="index.html">{SITE_TITLE}</a></h1>\n'
        f'  <p class="tagline">{SITE_TAGLINE}</p>\n'
        "</header>\n"
        '<ul class="posts">\n' + "\n".join(items) + "\n</ul>"
    )
    (OUT_DIR / "index.html").write_text(
        PAGE.format(
            title=SITE_TITLE,
            description=SITE_TAGLINE,
            og_type="website",
            body=body,
            site_title=SITE_TITLE,
            tagline=SITE_TAGLINE,
        ),
        encoding="utf-8",
    )


def main():
    # 出力フォルダを作り直す
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "posts").mkdir(parents=True)

    posts = [parse_post(p) for p in sorted(POSTS_DIR.glob("*.md"))]
    # 日付の新しい順に並べる（日付が無いものは末尾）
    posts.sort(key=lambda p: p["date"], reverse=True)

    for i, post in enumerate(posts):
        next_ = posts[i - 1] if i > 0 else None          # ひとつ新しい記事
        prev = posts[i + 1] if i + 1 < len(posts) else None  # ひとつ古い記事
        write_post(post, prev, next_)
    write_index(posts)

    print(f"生成完了: {len(posts)} 記事 → {OUT_DIR}")


if __name__ == "__main__":
    main()
