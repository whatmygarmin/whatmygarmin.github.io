# My Media

Markdown ファイルを置くと記事として公開される、最小の静的サイトです。

## 仕組み

```
my-media/
├── posts/            ← ここに記事を .md で置く
│   └── hello.md
├── build.py          ← MD → HTML 変換 + 記事一覧の生成
├── requirements.txt  ← 依存ライブラリ (markdown)
├── _site/            ← 生成物（自動生成。Git管理しない）
└── .github/workflows/deploy.yml  ← GitHub Pages 自動公開
```

なぜ Python 構成か: このPCには Node が無く、Ruby は古いため、
**すでに入っている Python だけで動く**のが最短だから。

## 記事の書き方

`posts/` に `.md` を追加するだけ。ファイル名がURL名になる（例 `hello.md` → `/posts/hello.html`）。
先頭にタイトルと日付を書く:

```markdown
title: 記事のタイトル
date: 2026-06-27

# 本文の見出し
ここから本文（Markdown）。
```

（`title:` `date:` の後に **空行を1つ**入れてから本文を書く）

## ローカルで確認する

```bash
# 初回だけ依存をインストール
pip install -r requirements.txt

# ビルド（_site/ を生成）
python3 build.py

# プレビュー（ブラウザで http://localhost:8000 を開く）
python3 -m http.server 8000 -d _site
```

## GitHub Pages で公開する

1. このフォルダを GitHub リポジトリにする（初回のみ）:

   ```bash
   git init
   git add .
   git commit -m "first post"
   git branch -M main
   git remote add origin https://github.com/whatmygarmin/whatmygarmin.github.io.git
   git push -u origin main
   ```

   ※ リポジトリ名を `whatmygarmin.github.io` にすると、公開URLが
   `https://whatmygarmin.github.io/` になります。

2. GitHub のリポジトリ画面で **Settings → Pages** を開き、
   **Build and deployment → Source** を **「GitHub Actions」** に設定する。

3. これ以降は `git push` するたびに、`.github/workflows/deploy.yml` が
   自動でビルドして公開します。Actions タブで進行状況を確認できます。

## 記事を増やす流れ

```bash
# 1. posts/ に新しい .md を作る
# 2. 確認したければローカルでビルド & プレビュー
# 3. push すれば自動公開
git add posts/新しい記事.md
git commit -m "add: 新しい記事"
git push
```
