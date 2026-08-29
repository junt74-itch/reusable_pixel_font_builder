import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from build_fonts import (
    Glyph,
    ShelfPage,
    infer_pixel_size,
    load_charset,
    pack_glyphs,
    pack_single_page,
    parse_args,
    slug_for_font,
    write_xml_font,
)


def test_load_charset_preserves_order_and_removes_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "charset.txt"
    path.write_text("BAAB\n", encoding="utf-8")
    assert load_charset(path) == [ord("B"), ord("A")]


def test_default_atlas_size_is_4096() -> None:
    assert parse_args([]).atlas_size == 4096


def test_font_filename_metadata() -> None:
    path = Path("KH-Dot-Kodenmachou-12-Ki.ttf")
    assert infer_pixel_size(path) == 12
    assert slug_for_font(path) == "kh-dot-kodenmachou-12-ki"


def test_added_font_pixel_sizes() -> None:
    assert infer_pixel_size(Path("04B_19_.TTF")) == 14
    assert infer_pixel_size(Path("04b_25_.ttf")) == 12
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


def test_single_page_packer_selects_smallest_power_of_two() -> None:
    glyphs = [
        Glyph(index, chr(65 + index), 30, 30, 0, 0, 30, Image.new("L", (30, 30), 255))
        for index in range(20)
    ]
    assert pack_single_page(glyphs, max_atlas_size=256, padding=1) == 256
    assert {glyph.page for glyph in glyphs} == {0}


def test_phaser_bmfont_xml_uses_single_font_texture(tmp_path: Path) -> None:
    glyph = Glyph(ord("A"), "A", 5, 7, 1, 2, 6, None, x=3, y=4)
    path = tmp_path / "font.xml"
    write_xml_font(path, "Pixel & Font", 8, 7, 1, 64, [glyph])

    root = ET.parse(path).getroot()
    assert root.find("info").attrib["face"] == "Pixel & Font"
    assert root.find("pages/page").attrib == {"id": "0", "file": "font.png"}
    assert root.find("chars/char").attrib["id"] == str(ord("A"))
    assert root.find("chars/char").attrib["page"] == "0"
