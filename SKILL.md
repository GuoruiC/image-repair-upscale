---
name: image-repair-upscale
description: Repair existing AI-generated images or text-heavy diagrams, then upscale locally with EDSR. Use for GPT Image output enhancement, incorrect or blurry labels, and 2x to 4x enlargement while preserving composition and transparency.
---

# Image Repair → Super-resolution

Combine content-aware repair with local neural super-resolution. Finish repair before EDSR: enlarging a wrong label or malformed object does not correct it. This skill operates on existing images; generating an unrelated new composition is outside its scope.

## 1. Inspect and repair

- Inspect the original and representative full-resolution crops. Record source dimensions, target dimensions, transparency, and the actual defects. Keep the original unchanged.
- For incorrect or unreadable text, establish the exact intended wording from the user or a verifiable source. OCR is a draft, not authority. Read [diagram-restoration.md](references/diagram-restoration.md) for dense diagrams or text replacement. Rebuild important labels with real fonts and preserve editable text when practical.
- For malformed non-text detail, use the available native image editing tool on the smallest useful region. Preserve subject identity, layout, object count, arrows, colors, and unaffected text. Include the original as a reference and preserve its transparency. Do not silently send private images to a new external provider.
- If content is already correct and only mildly soft, optional restrained sharpening is available with `scripts/enhance_raster.py --scale 1`. It is conventional processing, not semantic repair or neural super-resolution. Do not sharpen by default when it creates halos or does not improve the source.
- Save and inspect a named `repaired.png` before moving on. If no repair is needed, use the inspected original and say repair was unnecessary. Do not invent unreadable labels.

## 2. Upscale the repaired image

Use the bundled EDSR helper, resolved relative to this skill directory. Python 3.11+ and `uv` are supported; the dependency runner uses OpenCV, NumPy and Pillow. Models are downloaded once into the user's local cache. Do not use another unrelated virtual environment.

```powershell
uv run --python 3.12 --script "<skill-dir>/scripts/upscale_image.py" "<repaired.png>" --factor 2 --output "<final-upscaled.png>" --keep-raw
```

For an exact target, replace `--factor 2` with `--size 3840x2160`. Match the original aspect ratio. A mismatched `stretch` target is rejected; use `--fit contain` only for requested padding or `--fit cover` for requested cropping. `--factor` supports 2, 3 and 4. Targets beyond the 4x neural canvas are rejected rather than being labelled neural detail restoration.

The helper preserves an existing alpha channel through deterministic alpha resizing. RGB detail uses EDSR; the alpha mask is not neural reconstruction. PNG output is required for transparent inputs. Outputs are new files; existing output files are refused. Windows Unicode paths use Pillow file loading and saving.

Keep the raw neural result when comparison matters. Use `--dry-run` to inspect size and output choices without downloading a model or rendering. See `--help` for tile controls.

## 3. Verify and deliver

- Decode the final file and check exact dimensions and alpha presence. Compare original, repaired, and final at the same display size, then inspect 100% and 200% crops for text, arrows, fine edges, transparent boundaries and tile seams.
- Recheck all important labels, numbers, symbols and relationships after EDSR. If text changed, restore the verified editable text at final resolution or keep the repaired candidate; do not silently accept invented strokes.
- Do not enlarge an already high-resolution vector rebuild unnecessarily. A faithful vector render can already satisfy the target.
- Return the final image/path, input and output dimensions, what was repaired, the actual method, and any unresolved defects. EDSR predicts detail; it does not establish that the new detail is true. File dimensions alone do not establish visual quality.

## Source provenance

Adapted from `pmatos/skills/upscale` (37e0a9889c5534a620039ed4dd38bb80c1f93d06) and `bosprimigenious/image-text-restore-skill` (8e18928dacc6ef400b3bc1779c197fd4ab52691a). The first supplies EDSR inference; the second supplies repair guidance and the conservative raster helper. Windows path handling, alpha preservation and output guards are local adaptations. Both sources are MIT licensed; notices are retained in `LICENSE`.
