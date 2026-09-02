# リポジトリ再利用方針

本書は、援用者と保守者が「何が保証され、何が保証されないか」を判断するための方針書です。操作手順そのものの正は `README.md`、実装仕様の正は `build_fonts.py` と `dist/manifest.json` です。本書は、それらを再利用可能な資産として提供・保守する際の原則と将来要件を定めます。

現状の確認日は 2026-09-02 です。04B の元 TTF と生成物は、ライセンスを確認できないため除外します。Must はリポジトリが満たすべき保証です。Should と Could は将来作業です。

## 対象読者と文書の位置づけ

対象読者は次の三者です。

1. `dist/` の完成済みフォントアセットをゲームへコピーして使う援用者
2. 必要文字だけを収録した同等アセットを自前ビルドする援用者
3. このリポジトリの保守者

第一保証のランタイムは Phaser 4 の標準ビットマップフォントローダーです。AngelCode BMFont XML を読める他環境での利用は派生利用であり、第一保証ではありません。本書は新しい CLI やディレクトリ規約を発明せず、現行実装と将来要件の境界を示します。

## 目的と提供価値

提供価値は二本立てです。

- **(A) 既製アセットをすぐ使えること。** クローン直後に `dist/` を参照し、ビルダーもソース TTF も使わず、必要なファイルをゲームへコピーできます。
- **(B) 必要文字だけの同等アセットを自前ビルドできること。** 利用者が用意した文字集合と、権利確認済みのソース TTF から、既製 `dist/` と同形式の成果物を再現可能な手続きで生成できます。

ここで「同等」とは、次を満たすことを指します。

- 単一ページの PNG アトラス `font.png`
- AngelCode BMFont XML の `font.xml`
- `report.json`、`missing-characters.txt`、`license.txt` がセットで付くこと
- PNG は RGBA 形式で、RGB は白固定、アルファは 0 または 255 の二値であること
- 文字集合にあって TTF にない文字を、代替フォントで補完しないこと

OS や Pillow の版をまたぐ PNG のバイト単位の完全一致までは保証しません。

## 現状（As-Is）

本節は確認できた事実のみを記します。

### 構成

- `dist/` は Git 追跡済みの完成品です。索引は `dist/manifest.json`、フォント数は 23、既定文字集合は `game_charset_standard.txt` のユニーク 7,150 文字です。各 `dist/<font-id>/` に `font.png`、`font.xml`、`report.json`、`missing-characters.txt`、`license.txt` があります。
- `_font_asset/` はソース TTF の配置場所です。KH-Dot、JF-Dot、美咲の 23 本は Git 収録済みです。04B の元 TTF はライセンス確認不可のため収録しません。公開クローンでは 23 本の自前ビルド入力が揃います。
- 文字集合は `character_set/`、ビルダーは `build_fonts.py`、依存定義は `pyproject.toml` と `uv.lock` にあります。Python 3.11 以降が必要です。
- テストは `tests/test_build_fonts.py` のユニットテスト 9 件です。実 TTF を使う結合テストと CI はありません。
- リポジトリ直下にビルダーコード用の `LICENSE` はありません。`pyproject.toml` のプロジェクト名は `ts-making-pixel-font` であり、リポジトリ名と一致していません。

### 既定ビルド契約

`build_fonts.py` の既定値は次のとおりです。

| 項目 | 既定値 |
|---|---|
| `--charset` | `character_set/game_charset_standard.txt` |
| `--output-dir` | `dist` |
| `--atlas-size` | `4096` |
| `--padding` | `1` |
| `--clean` | `true` |
| `--fonts-dir` | `_font_asset` |
| `--font` | 未指定。`_font_asset/*.ttf` を列挙 |

アトラスは 64 から上限まで二倍し、単一ページに収まる最小の正方形を使います。上限に収まらない場合は失敗します。

出力は RGBA・RGB 白固定・アルファ 0/255 です。埋め込み 1-bit ストライクがあればそれを優先します。埋め込みを持たない美咲 2019 年版 3 種と 04b 2 種は、許可リスト上の `outline-pixel` として二値ラスタライズします。通常のアウトラインフォントへの暗黙フォールバックはありません。グリフは回転せず、欠落は `missing-characters.txt` に理由とともに記録します。`license.txt` は TTF の name テーブルからの転記です。

### 利用上の事実

- `04b-19` と `04b-25` は `glyph_count` が 97、`missing_count` が 7,053 です。standard 7,150 文字の大半を欠き、日本語用ではありません。
- `kh-dot-hibiya-24` と `kh-dot-hibiya-32` の `atlas_size` は 4,096 で、既定上限ちょうどです。
- 欠落は隠さず、代替補完しないことが現行ビルダーの契約です。
- 既定の clean 動作は出力ディレクトリ全体を削除します。既定出力先のまま実行すると、既製 `dist/` を作り直す操作になります。

## 目標（To-Be）

援用者はライセンスと欠落を理解したうえで `dist/` を直ちに使え、必要な入力を用意できる環境では、同一手続きでカスタム文字集合の同等アセットを再現できる状態を目指します。

「再利用しやすい」とは、導線 A がビルドなしで成立し、導線 B が TTF 取得を前提に手続き再現でき、保守者が配布・除外・検証・変更管理の原則を本書一枚でたどれる状態です。

## 配布単位

| 単位 | 役割 | 現状 |
|---|---|---|
| Git リポジトリ（`dist/` を含む） | 第一配布単位 | 成立 |
| `dist/<font-id>/` | ゲームへコピーする最小単位 | 成立 |
| `_font_asset/` の KH / JF / 美咲 TTF | 自前ビルドの入力。確認できた家族のみ Git 収録 | 23 本を収録 |
| `_font_asset/` の 04B TTF / 生成物 | ライセンス未確認のため非収録 | 公開物から除外 |
| GitHub Releases / zip | 将来の補助配布 | 未整備 |

完成品だけを使う援用者は、TTF やビルダーを成果物として扱いません。カスタムビルドの成果は既定 `dist/` を上書きせず、`--output-dir` で別ディレクトリへ出します。`character_set/` の txt はビルド入力であり、ゲーム実行時アセットではありません。

ソース TTF をすべて Git に入れることは Must ではありません。確認できた KH-Dot、JF-Dot、美咲のみを収録し、確認できない 04B とその生成物は除外します。04B の収録是非は、原典が確認できるまで再判断しません。

## ライセンス

ライセンスは三層に分けます。本節は観察事実と確認事項までとし、利用可否の法的結論は出しません。

### 1. ビルダーコード

ビルダーコードとリポジトリ独自文書は直下の `LICENSE` にある MIT License です。第三者フォントと文字セットの条件は `THIRD_PARTY_NOTICES.md` に分離し、MIT の対象外とします。

### 2. ソース TTF

各 `license.txt` は TTF の name テーブルの転記であり、原典の代替ではありません。利用前に各フォントの公式配布元で条文を確認します。現状の観察は次のとおりです。

- KH-Dot、JF-Dot、美咲は `_font_asset/` に収録しています。04B の元 TTF と生成物は収録していません。
- KH-Dot: name テーブルに SIL Open Font License Version 1.1 と Keitarou Hiraki / Font Silo の著作権表示があります。
- JF-Dot M+: M+ FONTS PROJECT の自由利用文言と URL があります。
- JF-Dot k12x10: 配布・形式変換・組込み・修正に関する日本語文言があります。
- 美咲 3 種: 著作権行のみが転記されています。
- 04b 2 種: 不完全な name 記録で、制御文字も含まれるため除外しました。

OFL の Reserved Font Name など、転記に現れない条項は確認事項です。代替補完や再ライセンスはしません。

### 3. 生成アセット

PNG、XML および付属テキストはソースフォントの派生物です。再配布時は各 `license.txt` をセットに含めます。転記から欠落した条文を本書が補充するものではありません。

## 文字集合

既製 `dist/` の正は standard 7,150 文字です。証跡は `dist/manifest.json` の `charset` と `charset_count` です。

| ファイル | ユニーク文字数 | 位置づけ |
|---|---:|---|
| `game_charset_lite.txt` | 643 | 小容量 UI、短文 |
| `game_charset_standard.txt` | 7,150 | 日本語ゲームの標準、既製 `dist/` の正 |
| `game_charset_extended.txt` | 7,516 | CP932 寄りの広域漢字・記号 |
| `game_charset_wide.txt` | 8,188 | Extended に多言語文字を加えた広域 |

必要文字だけを収録する場合は、共通セットにゲームテキスト由来の文字を足した txt を利用者が用意し、`--charset` で渡します。結合ヘルパーは現状未実装です。

欠落は失敗ではなく、代替フォントで補完しません。04b を standard でビルドしても日本語は収録されません。文字集合の由来と用途は `character_set/README.md` を参照しますが、ビルダーの正は `build_fonts.py` です。

## 再現性

保証するのは手続き再現であり、ビット一致ではありません。

同一の TTF ファイル名と内容、charset ファイル、CLI フラグ、`uv.lock` で解決される依存、Python 3.11 以降を前提に、次が一致することを再現性の基準とします。

- font-id
- `glyph_count` と `missing_count`
- `atlas_size`
- validation の全項目が真であること
- 単一の `font.png` と `font.xml`、かつ `page_count == 1`

次は Must にしません。

- OS や Pillow 版を超えた PNG のバイト一致
- TTF のないクローンからの 04B 再ビルド
- 成果物ハッシュによるゴールデン比較

自前ビルドの基本手続きは次のとおりです。操作の正は `README.md` です。

```powershell
uv sync
uv run pytest -q
uv run python build_fonts.py --charset <txt> --font <TTF名> --output-dir <dist以外>
```

既定の clean 動作は出力先を全削除するため、既製 `dist/` を出力先にしません。`--font` は TTF ファイル名を指定し、複数回指定できます。許可リスト外のアウトラインフォントを暗黙にラスタライズしません。

## 検証

成功条件は、ビルダーの終了コードが 0 で、`report.json` の次の検証値がすべて真、かつ `page_count == 1` であることです。

- `validation.page_dimensions`
- `validation.rgba_white`
- `validation.binary_alpha`
- `validation.glyph_bounds`
- `validation.glyph_overlap`

既製 `dist/` を使う援用者は、`manifest.json` の `missing_count` と対象フォントの `missing-characters.txt` を確認し、必要文字が足りるか判断します。自前ビルドでも同じ契約を用います。単一ページに収まらない場合は失敗とし、`--atlas-size` の拡大は利用者判断です。Hibiya 24/32 は standard で既に 4,096 です。

`pytest` はビルダー回帰用です。実フォント結合テストは Could であり、Must ではありません。04B は引き続き Git 非収録です。

## リリース

現状、デフォルトブランチ上の追跡済み `dist/` が既製アセットの「今の正」です。タグ、GitHub Releases、変更履歴はありません。本書の作成自体はリリース行為ではありません。

文字集合、収録フォント、パッキング規則の変更は既製アセットを破壊的に変え得ます。将来はバージョンと変更理由を残します（Should）。

## 保守

- 生成物の正はビルダー出力です。`font.png` と `font.xml` を手編集しません。
- フォント追加の条件は、1-bit 埋め込みストライクがあること、または `outline-pixel` の許可リストに載ることです。ピクセルサイズ推論規則の正は `build_fonts.py` です。
- charset の変更は全 `dist/` の再生成を意味します。本書作成のためには再生成しません。
- `missing_count` の変動は、フォントまたは charset が変わった合図として扱います。
- 保守者のソース TTF 配置は `_font_asset/` です。04B のみ `.gitignore` で除外します。
- パッケージ名 `ts-making-pixel-font` の是正は Should です。
- 既存ファイルの既知の不整合を、本書との見た目の整合だけを目的に修正しません。

## 利用者導線

### 導線 A: 既製 `dist/` を使う

入口は `README.md` の「完成済みアセットを利用する場合」です。TTF もビルダーも不要です。

1. `dist/manifest.json` で font-id、pixel size、atlas size、missing count を確認します。
2. 対象の `missing-characters.txt` と `license.txt` を確認します。04b は日本語用ではなく、Hibiya 24/32 はアトラス上限 4,096 です。
3. `dist/<font-id>/font.png` と `font.xml` をゲーム側へコピーします。再配布時は `license.txt` もセットにします。
4. Phaser 4 の `this.load.bitmapFont` に PNG と XML を渡します。例の正は `README.md` です。

`_font_asset/` や `build_fonts.py` を完成品の代わりに使いません。欠落文字が別フォントで補完されるとも想定しません。

### 導線 B: 必要文字だけで自前ビルドする

入口は必要文字の UTF-8 txt です。KH-Dot、JF-Dot、美咲の TTF はクローンで `_font_asset/` に揃います。04B は Git 非収録のため、ビルドする場合は利用者が入手して同ディレクトリへ置きます。

1. 必要文字の txt を用意します。
2. 収録済みの KH / JF / 美咲はそのまま使います。04B または独自 TTF は、権利を確認したうえで `_font_asset/` へ置きます。
3. `uv sync` の後、`uv run pytest -q` を実行します。
4. `uv run python build_fonts.py --charset <txt> --font <TTF名> --output-dir <dist以外>` を実行します。
5. `missing-characters.txt` と `report.json` を確認します。validation がすべて真で、`page_count == 1`、終了コードが 0 であることを確認します。

既定の clean 動作のまま `dist/` へ出力して既製アセットを消さないようにします。許可リスト外のアウトラインフォントを黙って通そうとせず、欠落も代替補完しません。

### 導線 C: 独自 TTF を使う

埋め込み 1-bit ストライク、または `outline-pixel` 許可リストの条件を満たすフォントだけが対象です。満たさないフォントは対象外です。

## 優先順位（Must / Should / Could）

本節はリポジトリが満たすべき保証（Must）と、将来の拡張（Should / Could）を分けます。Must は利用者向け README と本書の両方で確認できる状態を指します。コード用 LICENSE、CI、公式入手先 URL の一覧は Should であり、Must には含めません。

### Must

- 提供価値の二本立てが文書化されていること。
- 第一配布単位が `dist/` を含む Git リポジトリであること。
- ライセンスを三層で扱い、コード用 LICENSE は未決、フォントは原典確認、成果物は `license.txt` とセットで再配布すること。
- 既製 `dist/` の文字集合は standard、カスタムは `--charset` とすること。
- 欠落を代替せず、04b の高欠落と Hibiya の 4,096 上限を隠さないこと。
- 自前ビルドは、収録済み TTF（KH / JF / 美咲）または利用者が置いた 04B を入力とし、出力先は既定 `dist/` 以外を推奨すること。
- 検証契約を validation 全真、`page_count == 1`、終了コード 0 とすること。
- 再現性は手続き再現までとし、PNG バイト一致を必須にしないこと。

### Should（将来）

- 各フォント家族の公式入手先 URL と条文を `THIRD_PARTY_NOTICES.md` で維持すること。
- 各フォント家族の公式入手先を、確認済み URL だけで一覧化すること。
- charset 結合の推奨手順を具体化すること。
- `manifest.json` や `report.json` にツールチェーン情報を記録すること。
- `pytest` を CI で実行すること。
- パッケージ名を是正すること。
- アセット変更時に changelog とタグを残すこと。

### Could

- GitHub Releases を補助配布に使うこと。
- 成果物ハッシュやビット一致 CI を用意すること。
- 結合テスト用の最小 TTF フィクスチャを用意すること。
- Phaser デモを用意すること。
- フォント追加許可リストの拡張手続きを自動化すること。
- wide / extended の既製 `dist/` を併配すること。

## ロードマップ

1. **今:** 方針書と Must の充足。確認できた TTF の収録、導線 A/B の明示、04b / Hibiya / 検証契約を隠さないこと。
2. **次:** コードのライセンス表示、各 TTF の公式入手先。法的確認を伴います。
3. **その次:** CI、manifest のツールチェーン情報、破壊的変更のバージョン方針を整備します。
4. **任意:** Releases、デモ、成果物ゴールデンを整備します。

実フォント CI は、04B を Git 除外のままにする場合、再配布可能なフィクスチャまたは意図的な skip の設計に依存します。

## 完了条件

### 本方針書の受け入れ条件

- 日本語で、現状（As-Is）と目標（To-Be）が別節であること。
- 提供価値、同等の定義、配布単位、ライセンス三層、文字集合、再現性、検証、リリース、保守、利用者導線、優先順位、ロードマップ、未充足ギャップがそろっていること。
- 数値が README、manifest、コードと矛盾しないこと。
- 法的結論、PNG バイト一致の Must、04B を含む全 TTF の Git 必須化を書いていないこと。

### リポジトリが再利用可能とみなせる条件（Must 充足）

- 導線 A として、ビルドなしで Phaser に載るファイル一式と、欠落・ライセンス情報がそろうこと。
- 導線 B として、収録 TTF または利用者が置いた 04B と charset から、ロックされた依存で同等形式を再現できる手順が README と本書に書かれていること。
- 保守者が、配布対象、Git 除外対象（04B のみ）、検証項目、変更管理の原則を本書でたどれること。
- Should 以降の未充足ギャップが残留リストとして明示されていること。

## 現状の未充足ギャップ

- 04B のソース TTF が Git 非収録で、04B の自前ビルドには入手が必要です。KH / JF / 美咲は収録済みです。
- ビルダーコード用 MIT `LICENSE` と第三者告知書があります。
- CI がありません。
- 実 TTF を使う結合テストがありません。
- 再現用ハッシュや成果物ゴールデンがありません。
- `pyproject.toml` の名前がリポジトリ名と一致しません。
- 04b は standard 7,150 文字に対して 7,053 文字が欠落し、日本語既製フォントとしては使えません。
- `license.txt` は name テーブル転記に留まり、美咲は著作権行のみ、04b は不完全です。原典確認が必要です。

## 付録: 既製 `dist/` の要約

`dist/manifest.json` に基づく、standard 7,150 文字・25 フォントの要約です。

| 家族 | rasterization mode | glyph / missing | atlas size |
|---|---|---:|---:|
| 04b-19 / 04b-25 | outline-pixel | 97 / 7,053 | 128 |
| JF-Dot k12x10 | embedded-bitmap | 7,036 / 114 | 1,024 |
| JF-Dot M+ 10 / 10B | embedded-bitmap | 7,122 / 28 | 1,024 |
| JF-Dot M+ 12 / 12B | embedded-bitmap | 7,122 / 28 | 2,048 |
| KH-Dot 多数 | embedded-bitmap | 7,001 / 149 または 7,033 / 117 | 主に 2,048 |
| KH-Dot Hibiya 24 / 32 | embedded-bitmap | 7,033 / 117 | 4,096 |
| 美咲 3 種 | outline-pixel (8px) | 7,043 / 107 | 1,024 |

04b のソースファイル名は `04B_19_.TTF` と `04b_25_.ttf`、slug は `04b-19` と `04b-25` です。
