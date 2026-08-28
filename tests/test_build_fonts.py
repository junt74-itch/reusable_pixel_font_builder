from pathlib import Path

from PIL import Image

from build_fonts import Glyph, ShelfPage, infer_pixel_size, load_charset, pack_glyphs, slug_for_font


def test_load_charset_preserves_order_and_removes_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "charset.txt"
    path.write_text("BAAB\n", encoding="utf-8")
    assert load_charset(path) == [ord("B"), ord("A")]


def test_font_filename_metadata() -> None:
    path = Path("KH-Dot-Kodenmachou-12-Ki.ttf")
    assert infer_pixel_size(path) == 12
    assert slug_for_font(path) == "kh-dot-kodenmachou-12-ki"


def test_added_font_pixel_sizes() -> None:
    assert infer_pixel_size(Path("JF-Dot-k12x10.ttf")) == 10
    assert infer_pixel_size(Path("JF-Dot-MPlus10B.ttf")) == 10
    assert infer_pixel_size(Path("JF-Dot-MPlus12.ttf")) == 12
    assert infer_pixel_size(Path("misaki_gothic.ttf")) == 8


def test_single_embedded_strike_takes_priority() -> None:
    strikes = [{"ppem_x": 10, "ppem_y": 10, "bit_depth": 1}]
    assert infer_pixel_size(Path("unexpected-name.ttf"), strikes) == 10


def test_shelf_page_wraps_rows() -> None:
    page = ShelfPage(size=10, padding=1)
    assert page.try_place(3, 3) == (1, 1)
    assert page.try_place(3, 3) == (6, 1)
    assert page.try_place(3, 3) == (1, 6)
    assert page.try_place(6, 6) is None


def test_pack_glyphs_adds_pages() -> None:
    glyphs = [
        Glyph(index, chr(65 + index), 6, 6, 0, 0, 6, Image.new("L", (6, 6), 255))
        for index in range(3)
    ]
    assert pack_glyphs(glyphs, atlas_size=8, padding=1) == 3
    assert [glyph.page for glyph in glyphs] == [0, 1, 2]
