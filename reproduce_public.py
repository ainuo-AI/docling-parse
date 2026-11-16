"""Reproduce a cited image region using public APIs on any supported platform.

Run this separately in an unmodified-main environment and a patched one:
  python reproduce_public.py manual.pdf --output before
  python reproduce_public.py manual.pdf --output after
The existing corpus equals region uses --page 5 --crop 100 124 114 139.
"""

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import pypdfium2
from docling_core.types.doc.base import BoundingBox, CoordOrigin
from PIL import Image, ImageChops, ImageStat

from docling_parse.pdf_parser import (
    DoclingThreadedPdfParser,
    RenderConfig,
    ThreadedPdfParserConfig,
)


def white(image):
    rgba = image.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("pdf", type=Path)
    args_parser.add_argument("--output", type=Path, required=True)
    args_parser.add_argument("--page", type=int, default=10)
    args_parser.add_argument("--scale", type=float, default=3.0)
    args_parser.add_argument("--crop", nargs=4, type=float, default=(50, 143, 190, 170))
    args = args_parser.parse_args()
    left, top, right, bottom = args.crop
    config = RenderConfig()
    config.scale = args.scale
    parser = DoclingThreadedPdfParser(parser_config=ThreadedPdfParserConfig(threads=1, loglevel="fatal", render_config=config))
    parser.load(args.pdf, page_numbers=[args.page])
    try:
        result = next(parser.iterate_results())
        assert result.success, result.error_message
        actual = white(result.get_image(scale=args.scale, cropbox=BoundingBox(l=left, t=top, r=right, b=bottom, coord_origin=CoordOrigin.TOPLEFT)))
    finally:
        parser.unload_all()
    with pypdfium2.PdfDocument(args.pdf) as document:
        reference = white(document[args.page - 1].render(scale=args.scale).to_pil()).crop(tuple(round(value * args.scale) for value in args.crop))
    assert actual.size == reference.size, (actual.size, reference.size)
    difference = ImageChops.difference(actual.convert("RGBA"), reference.convert("RGBA"))
    means = ImageStat.Stat(difference).mean
    args.output.mkdir(parents=True, exist_ok=True)
    actual.save(args.output / "native.png")
    reference.save(args.output / "pdfium.png")
    report = {
        "source_sha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
        "pypdfium2": version("pypdfium2"), "page": args.page, "scale": args.scale, "crop_points": args.crop,
        "size": actual.size, "native_dark_pixels": sum(actual.convert("L").histogram()[:128]),
        "pdfium_dark_pixels": sum(reference.convert("L").histogram()[:128]),
        "mean_abs_error": sum(means) / len(means),
        "changed_pixels_ratio": difference.convert("L").point(lambda value: 255 if value > 12 else 0).histogram()[255] / (actual.width * actual.height),
    }
    (args.output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
