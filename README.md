# 歯科ドクターズ

全国の歯科医院を **院長インタビュー** で紹介する情報サイト。
公開URL: https://shin3578-oss.github.io/shika-doctors/

診療時間とアクセスだけでは、自分に合う歯医者かどうかは分からない。
「その先生が何を大事にして治療しているか」まで分かるようにする、というのがこのサイトの狙い。

## 仕組み

`data/` の JSON を読んで `docs/` に HTML を書き出すだけの静的サイト。
サーバもデータベースも要らないので、GitHub Pages で無料のまま運用できる。

```
python build.py     # data/ → docs/ を再生成
python shot.py      # 主要ページをPC幅で撮って _shots/ に置く（目視確認用）
```

Python は標準ライブラリのみ。追加インストール不要（`shot.py` だけ playwright を使う）。

## 医院を1件増やす手順

1. `data/clinics/<slug>.json` を1つ足す（既存の `osaki-ovalcourt-dental.json` をコピーして書き換える）
2. `python build.py`
3. commit して push → GitHub Pages が自動で反映（1〜2分）

`published: false` にすると、ファイルを残したまま非公開にできる。

## ファイル

| パス | 中身 |
|---|---|
| `data/site.json` | サイト名・説明・公開URL・連絡先 |
| `data/features.json` | 「土曜診療」「矯正歯科」などの条件タグの定義 |
| `data/clinics/*.json` | 医院1件＝1ファイル |
| `build.py` | 静的サイトビルダー |
| `assets/style.css` | 見た目 |
| `docs/` | **生成物。手で編集しない**（build.py が毎回作り直す） |

## 生成されるページ

トップ／都道府県別／市区町村別／条件別（16種）／医院詳細／掲載のご案内／このサイトについて／掲載方針・免責事項
＋ `sitemap.xml`・`robots.txt`・JSON-LD（`Dentist`・`BreadcrumbList`）

## 独自ドメインに移すとき

`data/site.json` の `base_url` を書き換えて `python build.py` するだけ。
サイト内リンクは全部そこから組み立てているので、他は触らなくていい。
あわせて `docs/CNAME` を置き、GitHub の Pages 設定でカスタムドメインを指定する。

## 守っているルール（医療広告ガイドライン）

医院から掲載料を受け取ると、そのページは医療広告に該当しうる。そのため次を設計として守っている。
`docs/policy/` にも同じ内容を明示している。

- 患者の体験談・口コミは載せない
- 「名医」「地域No.1」などの比較優良広告に当たる表現を使わない
- 治療効果を断定・保証しない
- 自由診療に触れる場合は、費用・期間・リスクが分かるようにする
- 掲載順を掲載料で変えない
- **リンク掲載を目的とした有償取引はしない**（Googleのリンクスパムポリシーに当たるため）
