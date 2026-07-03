# はたと — ジャーナルサイト

Markdown ファイルを置くと記事として公開される、最小の静的サイトです。
ジャーナル「はたと」の置き場。**note に投稿された記事を自動でこちらにも取り込みます。**

## 仕組み

```
my-media/
├── posts/            ← 記事の .md（手書き or note から自動取り込み）
│   └── hatato-001-must-sleep.md
├── build.py          ← MD → HTML 変換 + 記事一覧の生成
├── fromnote.py       ← note の投稿をこのサイトに取り込む
├── tonote.py         ← 逆方向: .md を note 貼り付け用テキストに
├── requirements.txt  ← 依存ライブラリ (markdown)
├── _site/            ← 生成物（自動生成。Git管理しない）
└── .github/workflows/
    ├── deploy.yml    ← push のたびに GitHub Pages へ公開
    └── sync-note.yml ← 毎日 6:00 JST に note を自動取り込み → 公開
```

サイト名・タグラインは `build.py` 冒頭の `SITE_TITLE` / `SITE_TAGLINE` で変えられます。
記事の連載番号（#001 など）は、ファイル名の `-001-` か、noteタイトル中の「#1」「＃001」から自動で拾います。

## note からの自動取り込み

note に記事が公開されると、毎日 6:00 JST の GitHub Actions（`sync-note.yml`）が
自動で取り込んで、このサイトにも公開します。手動でも取り込めます:

```bash
python3 fromnote.py            # fromnote.py の NOTE_USERNAME から取り込み
python3 fromnote.py <urlname>  # アカウント指定（note.com/○○○ の ○○○）
```

- 取り込んだ記事は `posts/note-<key>.md` になり、`source:` に元URLが入る
  （記事ページに「note でも読む →」リンクが出ます）
- 取り込み済みの記事、**同じタイトルの記事は二重に取り込まない**
- 有料記事はスキップ

初期設定（どちらか一方でOK）:
1. `fromnote.py` の `NOTE_USERNAME = ""` に note のアカウント名を書く
2. GitHub リポジトリの Settings → Secrets and variables → Actions → Variables に
   `NOTE_USERNAME` を追加する

なぜ Python 構成か: このPCには Node が無く、Ruby は古いため、
**すでに入っている Python だけで動く**のが最短だから。

## 記事の書き方

`posts/` に `.md` を追加するだけ。ファイル名がURL名になる
（例 `hatato-002-xxx.md` → `/posts/hatato-002-xxx.html`）。
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

## 記事を出す流れ

**ふだんは何もしなくてOK。** note に投稿すれば、翌朝 6:00 JST までに
自動でこのサイトにも載ります。すぐ載せたいときは Actions タブから
`Sync from note` を手動実行（Run workflow）してください。

逆に「このリポジトリで先に書いて note に出す」ときは:

```bash
# 1. posts/ に .md を書く（例 hatato-002-xxx.md）

# 2. note 用のテキストをクリップボードに入れる
python3 tonote.py              # 引数なし = いちばん新しい記事
#    → note の新規記事に貼り付けて公開（同タイトルなので二重取り込みはされない）

# 3. push すれば自分のHPにも公開
git add posts/hatato-002-xxx.md
git commit -m "add: はたと#002"
git push
```
