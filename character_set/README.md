# BMFont Charset Sets

HTML5 / Phaser / PixiJS / Canvas/WebGL 等のゲーム用ビットマップフォント作成を想定した
UTF-8文字セットです。

## ファイル

- game_charset_lite.txt
  - 643 文字
  - ASCII、ひらがな、カタカナ、日本語約物、ゲームUI記号、頻出UI漢字
  - 小容量UI、短文中心のゲーム向け

- game_charset_standard.txt
  - 3,971 文字
  - Lite + 全角英数 + CP932/JIS系非漢字 + 漢字約3,200字
  - 一般的な日本語ゲームでの標準セットを想定
  - まずはこれを推奨

- game_charset_extended.txt
  - 7,516 文字
  - CP932で表現可能な漢字・記号を広く収録
  - 人名、地名、長文、ADV/RPG向け

- game_charset_wide.txt
  - 8,188 文字
  - Extended + Latin-1 + Latin Extended-A + Greek + Cyrillic + 追加記号
  - 多言語UIを視野に入れた広域セット

## 運用上の推奨

共通文字セット + 実際のゲーム内テキストから抽出した固有文字、
という運用が最も確実です。

例:
  charset = game_charset_standard.txt + script_extracted_chars.txt

BMFont CLI / msdf-bmfont-cli 等で charset-file を指定できる場合、
各 txt をそのまま入力できます。

## 注意

このセットの漢字部分は Python の CP932 コーデックから機械的に取得した
実用上の Shift-JIS/Windows日本語文字レパートリを基礎にしています。
「JIS第1水準・第2水準の公式配列そのもの」を転記したファイルではありません。

フォント側に対象グリフが存在しない場合、その文字はアトラスに生成できません。
