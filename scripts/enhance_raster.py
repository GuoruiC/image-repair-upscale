#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10.0"]
# ///
"""Conservative raster enlargement and sharpening with a verifiable JSON result."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError as exc:
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc


MODE_SETTINGS = {
    "text": {"radius": 0.9, "percent": 80, "threshold": 2, "contrast": 1.0},
    "illustration": {"radius": 1.15, "percent": 105, "threshold": 3, "contrast": 1.025},
    "photo": {"radius": 1.0, "percent": 85, "threshold": 3, "contrast": 1.015},
}


def parse_target(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError("target must look like WIDTHxHEIGHT") from exc
    if width < 1 or height < 1:
        raise argparse.ArgumentTypeError("target dimensions must be positive")
    return width, height


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enlarge and gently sharpen a raster image without generative rewriting."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    size = parser.add_mutually_exclusive_group(required=True)
    size.add_argument("--scale", type=float, help="positive enlargement multiplier")
    size.add_argument("--target", type=parse_target, help="exact WIDTHxHEIGHT output")
    parser.add_argument("--mode", choices=MODE_SETTINGS, default="illustration")
    parser.add_argument(
        "--allow-distortion",
        action="store_true",
        help="allow --target to change aspect ratio by more than 1 percent",
    )
    parser.add_argument(
        "--max-megapixels",
        type=float,
        default=200.0,
        help="reject larger outputs unless explicitly raised (default: 200)",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing output")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without writing")
    return parser


def output_dimensions(
    source: tuple[int, int],
    scale: float | None,
    target: tuple[int, int] | None,
    allow_distortion: bool,
) -> tuple[int, int]:
    if target is not None:
        if target[0] < source[0] or target[1] < source[1]:
            raise ValueError("target must not shrink either source dimension")
        source_ratio = source[0] / source[1]
        target_ratio = target[0] / target[1]
        if abs(target_ratio / source_ratio - 1) > 0.01 and not allow_distortion:
            raise ValueError(
                "target changes aspect ratio by more than 1%; choose a matching target "
                "or pass --allow-distortion"
            )
        return target
    if scale is None or scale < 1:
        raise ValueError("scale must be at least 1")
    return max(1, round(source[0] * scale)), max(1, round(source[1] * scale))


def enhance_rgb(image: Image.Image, size: tuple[int, int], mode: str) -> Image.Image:
    settings = MODE_SETTINGS[mode]
    resized = image.resize(size, Image.Resampling.LANCZOS)
    if settings["contrast"] != 1.0:
        resized = ImageEnhance.Contrast(resized).enhance(settings["contrast"])
    return resized.filter(
        ImageFilter.UnsharpMask(
            radius=settings["radius"],
            percent=settings["percent"],
            threshold=settings["threshold"],
        )
    )


def enhance(image: Image.Image, size: tuple[int, int], mode: str) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if "A" not in image.getbands():
        return enhance_rgb(image.convert("RGB"), size, mode)
    rgba = image.convert("RGBA")
    rgb = enhance_rgb(rgba.convert("RGB"), size, mode)
    alpha = rgba.getchannel("A").resize(size, Image.Resampling.LANCZOS)
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def save_options(suffix: str) -> dict[str, object]:
    if suffix in {".jpg", ".jpeg"}:
        return {"quality": 95, "subsampling": 0, "optimize": True}
    if suffix == ".png":
        return {"compress_level": 9, "optimize": True}
    if suffix == ".webp":
        return {"quality": 95, "method": 6}
    raise ValueError("output extension must be .png, .jpg, .jpeg, or .webp")


def main() -> int:
    args = build_parser().parse_args()
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"input does not exist: {source}")
    if source == output:
        raise SystemExit("input and output must be different paths")
    if output.exists() and not args.force:
        raise SystemExit(f"output exists; use --force to replace it: {output}")
    if args.max_megapixels <= 0:
        raise SystemExit("--max-megapixels must be positive")

    with Image.open(source) as opened:
        source_size = ImageOps.exif_transpose(opened).size
        try:
            target_size = output_dimensions(
                source_size, args.scale, args.target, args.allow_distortion
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        megapixels = target_size[0] * target_size[1] / 1_000_000
        if megapixels > args.max_megapixels:
            raise SystemExit(
                f"planned output is {megapixels:.1f} MP; raise --max-megapixels explicitly"
            )
        result = {
            "status": "planned" if args.dry_run else "written",
            "input": str(source),
            "input_size": list(source_size),
            "output": str(output),
            "output_size": list(target_size),
            "mode": args.mode,
            "generative": False,
        }
        if args.dry_run:
            print(json.dumps(result, ensure_ascii=False))
            return 0

        options = save_options(output.suffix.lower())
        output.parent.mkdir(parents=True, exist_ok=True)
        rendered = enhance(opened.copy(), target_size, args.mode)
        if output.suffix.lower() in {".jpg", ".jpeg"} and rendered.mode != "RGB":
            rendered = rendered.convert("RGB")
        handle = tempfile.NamedTemporaryFile(
            prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent, delete=False
        )
        temporary = Path(handle.name)
        handle.close()
        try:
            rendered.save(temporary, **options)
            with Image.open(temporary) as check:
                check.verify()
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)

    with Image.open(output) as check:
        if check.size != target_size:
            raise SystemExit(f"verification failed: expected {target_size}, got {check.size}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
