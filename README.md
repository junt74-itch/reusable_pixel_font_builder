このリポジトリは、TTF を基に収録文字セットに応じたビットマップフォントアトラスを作成します。再利用方針は [`docs/REPOSITORY_POLICY.md`](docs/REPOSITORY_POLICY.md) です。

提供価値は二本立てです。

- **(A) 既製アセットをすぐ使う。** `dist/` をコピーするだけでよく、ビルダーもソース TTF も不要です。
- **(B) 必要文字だけの同等アセットを自前ビルドする。** 単一ページ PNG、BMFont XML、`report.json`、`missing-characters.txt`、`license.txt` を同形式で生成できます。欠落の代替補完はしません。PNG のバイト一致は保証しません。

## 完成済みアセットを利用する場合（導線 A）

ゲームなどの別プロジェクトから参照する場合は、`dist/` を使ってください。まず `dist/manifest.json` で font-id、ピクセルサイズ、アトラス枚数、欠落文字数を確認します。

```text
dist/
  manifest.json       # 完成済みアセット全体の索引
  <font-id>/
    font.png          # ゲームで使用する単一ページのフォントアトラス
    font.xml          # AngelCode BMFont XML（Phaser 4推奨）
    report.json       # ビルド・検証結果
    missing-characters.txt
    license.txt
```

次の事実は隠さない前提です。

- 既製 `dist/` の文字集合は `game_charset_standard.txt`（ユニーク 7,150 文字）です。
- `04b-19` と `04b-25` は 97 グリフ、欠落 7,053 です。日本語用ではありません。
- `kh-dot-hibiya-24` と `kh-dot-hibiya-32` のアトラスは 4,096 ピクセルで、既定上限ちょうどです。
- 欠落は契約条件であり、代替フォントでは補完しません。必要文字が足りるかは `missing-characters.txt` で判断してください。
- 再配布するときは各 `license.txt` をセットに含めます。`license.txt` は TTF の name テーブル転記であり、原典の代替ではありません。

Phaser 4 では PNG と XML を標準ローダーへ渡します。

```javascript
preload() {
  this.load.bitmapFont(
    "kh-dot-hibiya-32",
    "assets/fonts/kh-dot-hibiya-32/font.png",
    "assets/fonts/kh-dot-hibiya-32/font.xml",
  );
}
```

## 必要文字だけで自前ビルドする場合（導線 B）

同等アセットとは、単一ページの白色 RGBA・二値アルファ PNG、BMFont XML、report / missing / license のセットです。代替補完はしません。

KH-Dot、JF-Dot、美咲の TTF は `_font_asset/` に収録しています。04B（`04B_19_.TTF` / `04b_25_.ttf`）はライセンスを確認できないため Git 非収録です。04B をビルドする場合は、利用者が入手して `_font_asset/` へ置きます。

既定の `--clean` は出力ディレクトリ全体を削除します。既製 `dist/` を消さないよう、カスタムビルドでは `--output-dir` で `dist/` 以外を指定してください。

```powershell
uv sync
uv run pytest -q
uv run python build_fonts.py --charset <txt> --font <TTF名> --output-dir <dist以外>
```

成功条件は、終了コード 0、`page_count == 1`、および `report.json` の `validation` がすべて真であることです。

- `page_dimensions`
- `rgba_white`
- `binary_alpha`
- `glyph_bounds`
- `glyph_overlap`

## 必要なもの

- [uv](https://docs.astral.sh/uv/)
- Python 3.11以降（uvが自動的に用意する環境でも可）

依存関係は `pyproject.toml` と `uv.lock` で固定します。

## 既製 dist を再生成する場合

リポジトリのルートで次を実行します。既定では `dist/` 全体を削除してから作り直します。

```powershell
uv sync
uv run python build_fonts.py
```

`_font_asset/` の収録 TTF が列挙されます。04B を置いていない場合、その 2 フォントは生成されません。既定の文字集合は `character_set/game_charset_standard.txt` です。

既定のアトラス上限は 4096x4096 ピクセル、グリフ間の余白は 1 ピクセルです。64x64 から上限まで段階的に試し、単一ページに収まる最小の正方形サイズを使用します。1 枚に収まらない場合はビルドを停止します。その場合は `--atlas-size` を大きくしてください。

## 主なオプション

```powershell
# アトラスサイズの上限を1024x1024にして生成
uv run python build_fonts.py --atlas-size 1024

# 1フォントだけ生成し、既存の他フォントの出力を残す
uv run python build_fonts.py --font KH-Dot-Hibiya-32.ttf --no-clean

# Extended文字集合を使用
uv run python build_fonts.py --charset character_set/game_charset_extended.txt

# 別の出力先を使用（カスタムビルドで推奨）
uv run python build_fonts.py --output-dir output/fonts
```

`--font` は複数回指定できます。`--padding 0` も指定できますが、ゲームでの
テクスチャサンプリング時のにじみを防ぐため、既定値の 1 を推奨します。

## 出力仕様

- PNG は RGBA 形式で、RGB は白固定、アルファは 0 または 255 だけを使用します。
- TTF 内に 1-bit 埋め込みビットマップがある場合は、そのストライクのピクセルサイズを優先して使用します。
- 埋め込みビットマップを持たない 2019 年版の美咲フォント 3 種は、既知の 8px ピクセルアウトラインとして二値ラスタライズします。通常のアウトラインフォントへの暗黙のフォールバックは行いません。
- グリフは回転せず、配置は常に決定的です。成果物は Phaser 4 標準ローダーに合わせて単一ページです。
- `font.xml` は AngelCode BMFont XML 形式です。
- 文字集合に存在して TTF 側にない文字は、代替フォントで補わず `missing-characters.txt` に理由とともに記録します。
- `report.json` にはストライク情報、文字数、ページ数、二値性・境界・重複の検証結果を記録します。
- `license.txt` には TTF の name テーブルに収録された著作権・ライセンス情報を転記します。

再現性は手続き再現です。同一の TTF 内容、charset、CLI、`uv.lock`、Python 3.11 以降を前提に、font-id、glyph / missing、atlas、validation、単一ページが一致します。OS を超える PNG バイト一致は保証しません。

## ライセンス

ビルダーコードとリポジトリ独自の文書は MIT License です（`LICENSE`）。
第三者フォント、生成アセット、文字セットの扱いは `THIRD_PARTY_NOTICES.md`
に分離しています。MIT ライセンスが第三者フォントを再ライセンスするものではありません。

各 `dist/<font-id>/license.txt` は生成元 TTF から転記した情報です。再配布時は対象フォントの
`license.txt` と `THIRD_PARTY_NOTICES.md` を併せて含めてください。04B の生成物はライセンスを
確認できないため収録していません。

## テスト

```powershell
uv run pytest -q
```
