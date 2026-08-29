このリポジトリは、ttfを基に、収録文字セットに応じたビットマップフォントアトラスを作成するためのものです。

## 完成済みアセットを利用する場合

ゲームなどの別プロジェクトからこのリポジトリを参照する場合、ビルド済みの完成品は
リポジトリ直下の `dist/` フォルダにあります。アセットを利用するだけであれば、
`_font_asset/` のTTFやビルドスクリプトではなく、`dist/` 内のファイルを使用してください。

まず `dist/manifest.json` を参照すると、収録されている全フォントと、各フォントの
アセットディレクトリ、ピクセルサイズ、アトラス枚数、欠落文字数を確認できます。
各ディレクトリには、ゲームへ組み込めるPNGアトラスとBMFont/JSON形式の
メトリクスがまとまっています。

```text
dist/
  manifest.json       # 完成済みアセット全体の索引
  <font-id>/
    atlas-0.png       # ゲームで使用するフォントアトラス
    font.fnt          # AngelCode BMFont形式のメトリクス
    font.json         # JSON形式のメトリクス
    report.json       # ビルド・検証結果
    missing-characters.txt
    license.txt
```

作成するビットマップフォントは、もととなるttfもビットマップフォントであることに鑑み、1ビットカラー、つまり白黒二値で表現できることを目指します。

truetypeフォントは _font_asset の中に配置されています。
全てのフォントを一括して、個別のアセットとして作成することを期待します。

収録文字セットは character_set の中に配置されています。
まずはstandardの文字セットを使うことを期待します。

## 必要なもの

- [uv](https://docs.astral.sh/uv/)
- Python 3.11以降（uvが自動的に用意する環境でも可）

依存関係は `pyproject.toml` と `uv.lock` で固定します。

## 生成方法

リポジトリのルートで次を実行します。

```powershell
uv sync
uv run python build_fonts.py
```

`_font_asset/*.ttf` が自動的に列挙され、フォントごとに独立したアセットが
`dist/` 以下へ生成されます。既定の文字集合は
`character_set/game_charset_standard.txt` です。

既定では、アトラスは2048x2048ピクセル、グリフ間の余白は1ピクセルです。
1枚に収まらない場合は、フォントごとに必要な数だけアトラスを生成します。

```text
dist/
  manifest.json
  kh-dot-dougenzaka-16/
    atlas-0.png
    atlas-1.png
    font.fnt
    font.json
    missing-characters.txt
    report.json
    license.txt
```

## 主なオプション

```powershell
# 1024x1024のアトラスで生成
uv run python build_fonts.py --atlas-size 1024

# 1フォントだけ生成し、既存の他フォントの出力を残す
uv run python build_fonts.py --font KH-Dot-Hibiya-32.ttf --no-clean

# Extended文字集合を使用
uv run python build_fonts.py --charset character_set/game_charset_extended.txt

# 別の出力先を使用
uv run python build_fonts.py --output-dir output/fonts
```

`--font` は複数回指定できます。`--padding 0` も指定できますが、ゲームでの
テクスチャサンプリング時のにじみを防ぐため、既定値の1を推奨します。

## 出力仕様

- PNGはRGBA形式で、RGBは白固定、アルファは0または255だけを使用します。
- TTF内に1-bit埋め込みビットマップがある場合は、そのストライクのピクセルサイズを優先して使用します。
- 埋め込みビットマップを持たない2019年版の美咲フォント3種は、既知の8pxピクセルアウトラインとして二値ラスタライズします。通常のアウトラインフォントへの暗黙のフォールバックは行いません。
- グリフは回転せず、配置とページ分割は常に決定的です。
- `font.fnt` はAngelCode BMFontテキスト形式です。グリフの `page` が対応するPNGを示します。
- `font.json` は同じメトリクスをJSONで格納します。
- 文字集合に存在してTTF側にない文字は、代替フォントで補わず `missing-characters.txt` に理由とともに記録します。
- `report.json` にはストライク情報、文字数、ページ数、二値性・境界・重複の検証結果を記録します。
- `license.txt` にはTTFのnameテーブルに収録された著作権・ライセンス情報を転記します。

## テスト

```powershell
uv run pytest -q
```
