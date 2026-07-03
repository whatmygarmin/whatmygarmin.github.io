#!/usr/bin/env python3
"""
note 納品用ツール。

posts/ の Markdown を「note にそのまま貼れるテキスト」に変換して
クリップボードにコピーする。note には投稿APIが無いため、
ここが最短の同時納品フロー:

    1. posts/ に .md を書く（原本はいつもこのリポジトリ）
    2. python3 tonote.py posts/記事.md   ← 本文がクリップボードに入る
    3. note の新規記事に貼り付けて公開（タイトルは画面に表示される）
    4. git push                          ← 自分のHPにも公開

使い方:
    python3 tonote.py posts/hatato-001-must-sleep.md
    python3 tonote.py                    # 引数なし → いちばん新しい記事
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"


def split_meta(text: str):
    """先頭の title:/date: 行を取り出し、(meta辞書, 本文) を返す。"""
    meta = {}
    lines = text.splitlines()
    i = 0
    for i, line in enumerate(lines):
        m = re.match(r"^(title|date):\s*(.+)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
        elif line.strip() == "" and meta:
            i += 1
            break
        else:
            break
    return meta, "\n".join(lines[i:]).strip()


def md_to_note_text(md: str) -> str:
    """Markdown を note 貼り付け用のプレーンテキストに変換する。

    note のエディタは Markdown 記法を解釈しないので、
    記号を残さず「読める素のテキスト」に落とす。
    """
    text = md
    # コードフェンスは中身だけ残す
    text = re.sub(r"^```.*$", "", text, flags=re.M)
    # 見出し記号・引用記号を落とす
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^>\s?", "", text, flags=re.M)
    # 水平線は「＊」に
    text = re.sub(r"^(-{3,}|\*{3,})\s*$", "＊", text, flags=re.M)
    # リンク [text](url) → text（url）
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1（\2）", text)
    # 強調・コードの記号を落とす
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # 3行以上の空行は1行に
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    if len(sys.argv) > 1:
        md_path = Path(sys.argv[1])
    else:
        # 引数なしなら、いちばん新しい .md（更新時刻順）
        candidates = sorted(
            POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not candidates:
            sys.exit("posts/ に記事がありません")
        md_path = candidates[0]

    if not md_path.exists():
        sys.exit(f"ファイルが見つかりません: {md_path}")

    meta, body_md = split_meta(md_path.read_text(encoding="utf-8"))
    body = md_to_note_text(body_md)

    subprocess.run("pbcopy", input=body.encode("utf-8"), check=True)

    print(f"クリップボードにコピーしました: {md_path.name}")
    print(f"  タイトル（noteに手で入力）: {meta.get('title', md_path.stem)}")
    print("  → note の新規記事を開いて、本文に貼り付けてください。")


if __name__ == "__main__":
    main()
