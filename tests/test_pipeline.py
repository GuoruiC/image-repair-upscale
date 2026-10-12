# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=1.26", "opencv-contrib-python-headless>=4.10", "pillow>=10.0"]
# ///
"""Exercise real EDSR inference and the repair baseline on disposable images."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def run(script, *arguments, ok=True):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "scripts" / script), *map(str, arguments)],
        capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
    return result


with tempfile.TemporaryDirectory(prefix="修复超分验证-") as directory:
    folder = Path(directory)
    source = folder / "中文原图.png"
    repaired = folder / "修复后.png"
    final = folder / "超分结果.png"
    image = Image.new("RGBA", (48, 40), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 7, 39, 32), fill=(40, 110, 210, 180))
    draw.line((8, 32, 39, 7), fill=(255, 255, 255, 255), width=2)
    image.save(source)
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    run("enhance_raster.py", source, repaired, "--scale", "1", "--mode", "text")
    with Image.open(repaired) as check:
        assert check.size == image.size and check.mode == "RGBA"

    run("upscale_image.py", repaired, "--factor", "2", "--output", final,
        "--keep-raw", "--tile-size", "24", "--overlap", "12")
    with Image.open(final) as check, Image.open(repaired) as repaired_image:
        assert check.size == (96, 80) and check.mode == "RGBA"
        expected_alpha = repaired_image.getchannel("A").resize(check.size, Image.Resampling.LANCZOS)
        assert np.array_equal(np.array(check.getchannel("A")), np.array(expected_alpha))
        baseline = repaired_image.convert("RGB").resize(check.size, Image.Resampling.LANCZOS)
        assert not np.array_equal(np.array(check.convert("RGB")), np.array(baseline))

    raw = folder / "超分结果-edsr-x2-raw.png"
    with Image.open(raw) as check:
        assert check.size == (96, 80) and check.mode == "RGBA"
    output_hash = hashlib.sha256(final.read_bytes()).hexdigest()
    run("upscale_image.py", repaired, "--output", final, ok=False)
    assert hashlib.sha256(final.read_bytes()).hexdigest() == output_hash
    run("upscale_image.py", source, "--output", source, ok=False)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    run("upscale_image.py", repaired, "--size", "96x100", "--dry-run", ok=False)
    run("upscale_image.py", repaired, "--size", "400x400", "--dry-run", ok=False)
    for scale in (2, 3, 4):
        run("upscale_image.py", repaired, "--factor", scale,
            "--output", folder / f"plan-{scale}.png", "--dry-run")
    run("upscale_image.py", repaired, "--size", "96x80",
        "--output", folder / "精确尺寸.png", "--dry-run")
    run("upscale_image.py", repaired, "--output", folder / "透明丢失.jpg", ok=False)
    assert not (folder / "plan-4.png").exists()

    sys.path.insert(0, str(ROOT / "scripts"))
    from upscale_image import fit_image
    padded = fit_image(image, (96, 96), "contain", "#000000")
    assert padded.mode == "RGBA" and padded.getpixel((0, 0))[3] == 0

report = {
    "passed": True,
    "checks": ["Windows Unicode paths", "same-size conservative enhancement",
               "real tiled EDSR 2x inference", "exact output dimensions", "alpha preservation",
               "raw output alpha", "source and output overwrite refusal",
               "aspect ratio and maximum scale guards", "2x/3x/4x planning",
               "transparent PNG requirement", "transparent contain padding"],
    "not_tested": ["semantic or generative image repair", "EDSR 3x/4x inference", "large image performance"],
}
print(json.dumps(report, ensure_ascii=False, indent=2))
