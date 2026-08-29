#!/usr/bin/env python3
"""Build deterministic, monochrome bitmap fonts for the Phaser 4 loader."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fontTools.ttLib import TTFont
from PIL import Image, ImageFont


# These releases encode pixel cells as TrueType outlines rather than EBLC/EBDT
# strikes.  Keep the allowlist explicit so ordinary outline fonts are not
# silently accepted as bitmap sources.
OUTLINE_PIXEL_FONT_SIZES = {
    "04b_19_": 14,
    "04b_25_": 12,
    "misaki_gothic": 8,
    "misaki_gothic_2nd": 8,
    "misaki_mincho": 8,
}


@dataclass
class Glyph:
    codepoint: int
    char: str
    width: int
    height: int
    xoffset: int
    yoffset: int
    xadvance: int
    bitmap: Image.Image | None
    x: int = 0
    y: int = 0
    page: int = 0


@dataclass
class ShelfPage:
    size: int
    padding: int
    cursor_x: int = 0
    cursor_y: int = 0
    row_height: int = 0

    def try_place(self, width: int, height: int) -> tuple[int, int] | None:
        cell_width = width + self.padding * 2
        cell_height = height + self.padding * 2
        if cell_width > self.size or cell_height > self.size:
            return None

        cursor_x = self.cursor_x
        cursor_y = self.cursor_y
        row_height = self.row_height
        if cursor_x + cell_width > self.size:
            cursor_x = 0
            cursor_y += row_height
            row_height = 0

        if cursor_y + cell_height > self.size:
            return None

        result = (cursor_x + self.padding, cursor_y + self.padding)
        self.cursor_x = cursor_x + cell_width
        self.cursor_y = cursor_y
        self.row_height = max(row_height, cell_height)
        return result


def load_charset(path: Path) -> list[int]:
    text = path.read_text(encoding="utf-8").rstrip("\r\n")
    seen: set[int] = set()
    result: list[int] = []
    for char in text:
        codepoint = ord(char)
        if codepoint not in seen:
            seen.add(codepoint)
            result.append(codepoint)
    return result


def infer_pixel_size(path: Path, embedded_strikes: list[dict[str, int]] | None = None) -> int:
    if embedded_strikes:
        one_bit_sizes = sorted({strike["ppem_y"] for strike in embedded_strikes if strike["bit_depth"] == 1})
        if len(one_bit_sizes) == 1:
            return one_bit_sizes[0]

    known_size = OUTLINE_PIXEL_FONT_SIZES.get(path.stem.lower())
    if known_size is not None:
        return known_size

    match = re.search(r"x(\d+)\.ttf$", path.name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"mplus(\d+)b?\.ttf$", path.name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"-(\d+)(?:-[^.]+)?\.ttf$", path.name, re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot infer pixel size from filename: {path.name}")
    return int(match.group(1))


def slug_for_font(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def _name_record(font: TTFont, name_id: int) -> str:
    table = font["name"]
    records = [record for record in table.names if record.nameID == name_id]
    records.sort(key=lambda record: (record.langID not in (0, 0x409), record.platformID != 3))
    for record in records:
        try:
            value = record.toUnicode().strip()
        except UnicodeDecodeError:
            continue
        if value:
            return value
    return ""


def inspect_font(path: Path) -> dict:
    with TTFont(path, lazy=False) as font:
        cmap = font.getBestCmap() or {}
        strikes: list[dict[str, int]] = []
        bitmap_glyphs_by_ppem: dict[int, set[str]] = {}
        if "EBLC" in font:
            for strike in font["EBLC"].strikes:
                table = strike.bitmapSizeTable
                ppem_y = int(table.ppemY)
                strikes.append(
                    {
                        "ppem_x": int(table.ppemX),
                        "ppem_y": ppem_y,
                        "bit_depth": int(table.bitDepth),
                    }
                )
                bitmap_glyphs_by_ppem.setdefault(ppem_y, set()).update(
                    name for subtable in strike.indexSubTables for name in subtable.names
                )
        return {
            "family": _name_record(font, 1) or path.stem,
            "full_name": _name_record(font, 4) or path.stem,
            "copyright": _name_record(font, 0),
            "license": _name_record(font, 13),
            "license_url": _name_record(font, 14),
            "cmap": cmap,
            "strikes": strikes,
            "bitmap_glyphs_by_ppem": bitmap_glyphs_by_ppem,
        }


def render_glyphs(path: Path, size: int, codepoints: Iterable[int]) -> tuple[list[Glyph], int, int]:
    font = ImageFont.truetype(str(path), size=size, layout_engine=ImageFont.Layout.BASIC)
    ascent, descent = font.getmetrics()
    glyphs: list[Glyph] = []

    for codepoint in codepoints:
        char = chr(codepoint)
        mask_core, offset = font.getmask2(char, mode="1", anchor="ls")
        mask = Image.frombytes("L", mask_core.size, bytes(mask_core))
        nonzero = mask.getbbox()
        if nonzero is None:
            bitmap = None
            width = 0
            height = 0
            xoffset = 0
            yoffset = 0
        else:
            left, top, right, bottom = nonzero
            bitmap = mask.crop(nonzero)
            extrema = bitmap.getextrema()
            if extrema not in ((255, 255), (0, 255)):
                raise ValueError(f"Non-binary glyph rendered for U+{codepoint:04X} in {path.name}")
            width = right - left
            height = bottom - top
            xoffset = int(offset[0] + left)
            yoffset = int(ascent + offset[1] + top)

        glyphs.append(
            Glyph(
                codepoint=codepoint,
                char=char,
                width=width,
                height=height,
                xoffset=xoffset,
                yoffset=yoffset,
                xadvance=round(font.getlength(char)),
                bitmap=bitmap,
            )
        )

    return glyphs, int(ascent), int(descent)


def pack_glyphs(glyphs: list[Glyph], atlas_size: int, padding: int) -> int:
    pages: list[ShelfPage] = [ShelfPage(atlas_size, padding)]
    drawable = sorted(
        (glyph for glyph in glyphs if glyph.bitmap is not None),
        key=lambda glyph: (-glyph.height, -glyph.width, glyph.codepoint),
    )

    for glyph in drawable:
        placement = None
        page_index = 0
        for page_index, page in enumerate(pages):
            placement = page.try_place(glyph.width, glyph.height)
            if placement is not None:
                break
        if placement is None:
            pages.append(ShelfPage(atlas_size, padding))
            page_index = len(pages) - 1
            placement = pages[-1].try_place(glyph.width, glyph.height)
        if placement is None:
            raise ValueError(
                f"Glyph U+{glyph.codepoint:04X} ({glyph.width}x{glyph.height}) "
                f"does not fit in a {atlas_size}x{atlas_size} atlas"
            )
        glyph.x, glyph.y = placement
        glyph.page = page_index

    return len(pages)


def pack_single_page(glyphs: list[Glyph], max_atlas_size: int, padding: int) -> int:
    atlas_size = 64
    while True:
        page_count = pack_glyphs(glyphs, atlas_size, padding)
        if page_count == 1:
            return atlas_size
        if atlas_size == max_atlas_size:
            raise ValueError(
                f"Glyph set needs {page_count} atlas pages at the {max_atlas_size}px limit; "
                "increase --atlas-size"
            )
        atlas_size = min(atlas_size * 2, max_atlas_size)


def write_atlas(path: Path, glyphs: list[Glyph], atlas_size: int) -> None:
    image = Image.new("RGBA", (atlas_size, atlas_size), (255, 255, 255, 0))
    for glyph in glyphs:
        if glyph.bitmap is None:
            continue
        white = Image.new("RGBA", (glyph.width, glyph.height), (255, 255, 255, 255))
        image.paste(white, (glyph.x, glyph.y), glyph.bitmap)
    image.save(path, format="PNG", compress_level=9, optimize=False)


def bmfont_attributes(
    family: str,
    size: int,
    ascent: int,
    descent: int,
    atlas_size: int,
    glyphs: list[Glyph],
) -> tuple[dict[str, str], dict[str, str], list[dict[str, str]]]:
    info = {
        "face": family,
        "size": str(size),
        "bold": "0",
        "italic": "0",
        "charset": "",
        "unicode": "1",
        "stretchH": "100",
        "smooth": "0",
        "aa": "1",
        "padding": "0,0,0,0",
        "spacing": "0,0",
        "outline": "0",
    }
    common = {
        "lineHeight": str(ascent + descent),
        "base": str(ascent),
        "scaleW": str(atlas_size),
        "scaleH": str(atlas_size),
        "pages": "1",
        "packed": "0",
        "alphaChnl": "0",
        "redChnl": "4",
        "greenChnl": "4",
        "blueChnl": "4",
    }
    chars = [
        {
            "id": str(glyph.codepoint),
            "x": str(glyph.x),
            "y": str(glyph.y),
            "width": str(glyph.width),
            "height": str(glyph.height),
            "xoffset": str(glyph.xoffset),
            "yoffset": str(glyph.yoffset),
            "xadvance": str(glyph.xadvance),
            "page": "0",
            "chnl": "8",
        }
        for glyph in sorted(glyphs, key=lambda item: item.codepoint)
    ]
    return info, common, chars


def write_xml_font(
    path: Path,
    family: str,
    size: int,
    ascent: int,
    descent: int,
    atlas_size: int,
    glyphs: list[Glyph],
) -> None:
    info, common, chars = bmfont_attributes(family, size, ascent, descent, atlas_size, glyphs)
    root = ET.Element("font")
    ET.SubElement(root, "info", info)
    ET.SubElement(root, "common", common)
    pages_element = ET.SubElement(root, "pages")
    ET.SubElement(pages_element, "page", {"id": "0", "file": "font.png"})
    chars_element = ET.SubElement(root, "chars", {"count": str(len(chars))})
    for char in chars:
        ET.SubElement(chars_element, "char", char)
    ET.SubElement(root, "kernings", {"count": "0"})
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    with path.open("a", encoding="utf-8", newline="\n") as output:
        output.write("\n")


def display_character(codepoint: int) -> str:
    char = chr(codepoint)
    if char.isspace():
        return "<SPACE>" if codepoint == 0x20 else f"<{unicodedata.name(char, 'WHITESPACE')}>"
    return char


def write_missing(path: Path, missing: list[int], reasons: dict[int, str]) -> None:
    lines = [
        f"U+{codepoint:04X}\t{display_character(codepoint)}\t"
        f"{unicodedata.name(chr(codepoint), 'UNNAMED')}\t{reasons[codepoint]}"
        for codepoint in missing
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")


def validate_pages(output_dir: Path, pages: list[str], atlas_size: int) -> dict:
    for filename in pages:
        with Image.open(output_dir / filename) as image:
            if image.mode != "RGBA" or image.size != (atlas_size, atlas_size):
                raise ValueError(f"Unexpected image format: {filename}")
            extrema = image.getextrema()
            if extrema[:3] != ((255, 255), (255, 255), (255, 255)):
                raise ValueError(f"RGB channels are not pure white: {filename}")
            if extrema[3][0] not in (0, 255) or extrema[3][1] not in (0, 255):
                raise ValueError(f"Alpha range is invalid: {filename}")
            alpha_values = set(image.getchannel("A").tobytes())
            if not alpha_values.issubset({0, 255}):
                raise ValueError(f"Non-binary alpha values found: {filename}")
    return {"page_dimensions": True, "rgba_white": True, "binary_alpha": True}


def validate_layout(glyphs: list[Glyph], page_count: int, atlas_size: int) -> dict:
    rows = [[bytearray(atlas_size) for _ in range(atlas_size)] for _ in range(page_count)]
    for glyph in glyphs:
        if glyph.bitmap is None:
            continue
        if not (0 <= glyph.page < page_count):
            raise ValueError(f"Invalid page for U+{glyph.codepoint:04X}: {glyph.page}")
        if glyph.x < 0 or glyph.y < 0 or glyph.x + glyph.width > atlas_size or glyph.y + glyph.height > atlas_size:
            raise ValueError(f"Out-of-bounds glyph U+{glyph.codepoint:04X}")
        for y in range(glyph.y, glyph.y + glyph.height):
            occupied = rows[glyph.page][y]
            if any(occupied[glyph.x : glyph.x + glyph.width]):
                raise ValueError(f"Overlapping glyph U+{glyph.codepoint:04X}")
            occupied[glyph.x : glyph.x + glyph.width] = b"\x01" * glyph.width
    return {"glyph_bounds": True, "glyph_overlap": True}


def build_font(font_path: Path, charset: list[int], output_root: Path, atlas_size: int, padding: int) -> dict:
    asset_id = slug_for_font(font_path)
    output_dir = output_root / asset_id
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    metadata = inspect_font(font_path)
    size = infer_pixel_size(font_path, metadata["strikes"])
    matching_strikes = [
        strike for strike in metadata["strikes"] if strike["ppem_y"] == size and strike["bit_depth"] == 1
    ]
    outline_pixel_source = not metadata["strikes"] and font_path.stem.lower() in OUTLINE_PIXEL_FONT_SIZES
    if not matching_strikes and not outline_pixel_source:
        raise ValueError(f"{font_path.name} has no 1-bit embedded bitmap strike at {size}px: {metadata['strikes']}")

    bitmap_glyphs = metadata["bitmap_glyphs_by_ppem"].get(size, set())
    present = [
        codepoint
        for codepoint in charset
        if codepoint in metadata["cmap"]
        and (outline_pixel_source or metadata["cmap"][codepoint] in bitmap_glyphs)
    ]
    missing_cmap = [codepoint for codepoint in charset if codepoint not in metadata["cmap"]]
    missing_bitmap = [
        codepoint
        for codepoint in charset
        if not outline_pixel_source
        and codepoint in metadata["cmap"]
        and metadata["cmap"][codepoint] not in bitmap_glyphs
    ]
    missing_reasons = {codepoint: "missing-cmap" for codepoint in missing_cmap}
    missing_reasons.update({codepoint: "missing-bitmap-strike" for codepoint in missing_bitmap})
    missing = [codepoint for codepoint in charset if codepoint in missing_reasons]
    glyphs, ascent, descent = render_glyphs(font_path, size, present)
    selected_atlas_size = pack_single_page(glyphs, atlas_size, padding)
    page_count = 1
    layout_validation = validate_layout(glyphs, page_count, selected_atlas_size)
    atlas_filename = "font.png"
    write_atlas(output_dir / atlas_filename, glyphs, selected_atlas_size)
    write_xml_font(
        output_dir / "font.xml", metadata["family"], size, ascent, descent, selected_atlas_size, glyphs
    )
    write_missing(output_dir / "missing-characters.txt", missing, missing_reasons)
    validation = validate_pages(output_dir, [atlas_filename], selected_atlas_size)
    validation.update(layout_validation)

    license_text = "\n".join(
        value for value in (metadata["copyright"], metadata["license"], metadata["license_url"]) if value
    )
    (output_dir / "license.txt").write_text(license_text + "\n", encoding="utf-8", newline="\n")

    report = {
        "id": asset_id,
        "source": font_path.name,
        "family": metadata["family"],
        "pixel_size": size,
        "rasterization_mode": "outline-pixel" if outline_pixel_source else "embedded-bitmap",
        "embedded_strikes": metadata["strikes"],
        "selected_strike": matching_strikes[0] if matching_strikes else None,
        "charset_count": len(charset),
        "glyph_count": len(glyphs),
        "missing_count": len(missing),
        "missing_cmap_count": len(missing_cmap),
        "missing_bitmap_count": len(missing_bitmap),
        "page_count": page_count,
        "atlas_size": selected_atlas_size,
        "max_atlas_size": atlas_size,
        "padding": padding,
        "validation": validation,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return report


def safe_clean_output(output_root: Path, project_root: Path, fonts_dir: Path, charset_path: Path) -> None:
    resolved = output_root.resolve()
    protected = {project_root.resolve(), fonts_dir.resolve(), charset_path.parent.resolve()}
    if resolved in protected or resolved.parent == resolved:
        raise ValueError(f"Refusing to clean unsafe output directory: {resolved}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts-dir", type=Path, default=Path("_font_asset"))
    parser.add_argument("--charset", type=Path, default=Path("character_set/game_charset_standard.txt"))
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--atlas-size", type=int, default=4096)
    parser.add_argument("--padding", type=int, default=1)
    parser.add_argument("--font", action="append", help="Only build matching TTF filename (repeatable).")
    parser.add_argument("--clean", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.atlas_size < 64:
        raise ValueError("--atlas-size must be at least 64")
    if args.padding < 0:
        raise ValueError("--padding must be non-negative")

    project_root = Path.cwd()
    fonts_dir = args.fonts_dir.resolve()
    charset_path = args.charset.resolve()
    output_root = args.output_dir.resolve()
    font_paths = sorted(fonts_dir.glob("*.ttf"), key=lambda path: path.name.lower())
    if args.font:
        selected = {name.lower() for name in args.font}
        font_paths = [path for path in font_paths if path.name.lower() in selected]
    if not font_paths:
        raise ValueError(f"No matching TTF files found in {fonts_dir}")

    charset = load_charset(charset_path)
    if args.clean:
        safe_clean_output(output_root, project_root, fonts_dir, charset_path)
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    reports: list[dict] = []
    for index, font_path in enumerate(font_paths, start=1):
        print(f"[{index}/{len(font_paths)}] Building {font_path.name}...", flush=True)
        report = build_font(font_path, charset, output_root, args.atlas_size, args.padding)
        reports.append(report)
        print(
            f"  {report['glyph_count']} glyphs, {report['missing_count']} missing, "
            f"{report['page_count']} atlas page(s)",
            flush=True,
        )

    manifest = {
        "format": "monochrome-bitmap-font-collection-v1",
        "charset": charset_path.name,
        "charset_count": len(charset),
        "font_count": len(reports),
        "fonts": reports,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Built {len(reports)} fonts into {output_root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
