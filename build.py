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
"""

import shutil
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "_site"
SITE_TITLE = "My Media"

# ---- ページ共通の HTML ひな形（最小の見た目） -------------------------------
PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, -apple-system, "Hiragino Sans", sans-serif;
          max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.7;
          color: #222; }}
  a {{ color: #0b66c3; }}
  h1 {{ border-bottom: 2px solid #eee; padding-bottom: .3rem; }}
  .date {{ color: #888; font-size: .9rem; }}
  ul.posts {{ list-style: none; padding: 0; }}
  ul.posts li {{ margin: .6rem 0; }}
  .home {{ display: inline-block; margin-bottom: 1rem; }}
</style>
</head>
<body>
{body}
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
    return {
        "title": title,
        "date": date,
        "slug": md_path.stem,
        "html": html_body,
    }


def write_post(post: dict):
    """記事1本を _site/posts/<slug>.html として書き出す。"""
    body = (
        '<a class="home" href="../index.html">← トップへ戻る</a>\n'
        f"<h1>{post['title']}</h1>\n"
        f'<p class="date">{post["date"]}</p>\n'
        f"{post['html']}"
    )
    out = OUT_DIR / "posts" / f"{post['slug']}.html"
    out.write_text(PAGE.format(title=post["title"], body=body), encoding="utf-8")


def write_index(posts: list):
    """記事一覧（タイトル＋日付リンク）のトップページを書き出す。"""
    items = []
    for p in posts:
        date = f'<span class="date">{p["date"]}</span> ' if p["date"] else ""
        items.append(
            f'<li>{date}<a href="posts/{p["slug"]}.html">{p["title"]}</a></li>'
        )
    body = (
        f"<h1>{SITE_TITLE}</h1>\n"
        '<ul class="posts">\n' + "\n".join(items) + "\n</ul>"
    )
    (OUT_DIR / "index.html").write_text(
        PAGE.format(title=SITE_TITLE, body=body), encoding="utf-8"
    )


def main():
    # 出力フォルダを作り直す
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "posts").mkdir(parents=True)

    posts = [parse_post(p) for p in sorted(POSTS_DIR.glob("*.md"))]
    # 日付の新しい順に並べる（日付が無いものは末尾）
    posts.sort(key=lambda p: p["date"], reverse=True)

    for post in posts:
        write_post(post)
    write_index(posts)

    print(f"生成完了: {len(posts)} 記事 → {OUT_DIR}")


if __name__ == "__main__":
    main()
