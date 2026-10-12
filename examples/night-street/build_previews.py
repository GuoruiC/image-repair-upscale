# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10.0"]
# ///
"""Verify the example outputs and rebuild the lightweight README previews."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
cases = [
    ("original.png", (502, 324), "Original", "unmodified test input"),
    ("initial-repair.png", (1561, 1007), "Initial repair", "built-in image editing"),
    ("upscaled-2x.png", (3122, 2014), "EDSR 2x", "EDSR_x2 from initial-repair.png"),
    ("upscaled-4x.png", (6244, 4028), "EDSR 4x", "EDSR_x4 from initial-repair.png"),
]
manifest = {
    "example": "night-street",
    "date": "2026-10-12",
    "scale_reference": "initial-repair.png",
    "transparency": "input is opaque RGB; the full night background is preserved",
    "limitations": "AI reconstructed detail is not verified original information; faces and signs remain indistinct",
    "images": [],
}
comparison = Image.new("RGB", (1600, 1100), "white")
draw = ImageDraw.Draw(comparison)
for index, (name, expected, label, method) in enumerate(cases):
    path = root / name
    with Image.open(path) as opened:
        opened.verify()
    with Image.open(path) as opened:
        assert opened.size == expected, (name, opened.size, expected)
        preview = opened.convert("RGB")
    preview.thumbnail((1200, 900), Image.Resampling.LANCZOS)
    preview_name = path.stem + "-preview.jpg"
    preview.save(root / preview_name, quality=90, subsampling=0)
    manifest["images"].append({
        "file": name, "width": expected[0], "height": expected[1], "method": method,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "preview": preview_name,
    })
    column, row = index % 2, index // 2
    draw.text((column * 800 + 12, row * 550 + 10), f"{label}: {expected[0]} x {expected[1]}", fill="black")
    comparison.paste(preview.resize((800, 516), Image.Resampling.LANCZOS), (column * 800, row * 550 + 34))
assert manifest["images"][0]["sha256"] == "d037da152d7a4ae16d2d1e278726357683fabb2349f541e033ea9782d91a57b8"
comparison.save(root / "comparison-preview.jpg", quality=90, subsampling=0)
(root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
