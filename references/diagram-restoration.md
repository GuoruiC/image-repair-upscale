# Dense Diagram Restoration

Use this reference for architecture diagrams, flowcharts, timelines, dashboards, screenshots, and other images where relationships and exact labels matter.

## Evidence Ladder

Do not treat every large PNG as a successful restoration. Rank evidence in this order:

1. Correct source text or a verified transcription.
2. Editable text and geometry with calibrated positions.
3. Visual inspection of same-scale crops.
4. OCR agreement as a supporting check.
5. Pixel dimensions and file size.

The last item proves only that the file is large.

## Strategy Ladder

Use the first route that can satisfy the task:

1. Preserve the source and apply gentle deterministic enhancement when text is already correct and readable.
2. Replace isolated text boxes when only a few labels are wrong.
3. Rebuild the text layer when many labels are wrong but geometry is usable.
4. Rebuild the whole diagram when the source layout is crowded, rasterized, or structurally damaged.
5. Use a model-generated text-free base only when old text cannot be removed cleanly by masks or vector reconstruction.

Whole-image model redraw is a visual draft for a text-heavy diagram. It is not a final text source.

## Common Failed Approaches

- **Upscaling the same layout**: adds pixels but does not enlarge the boxes relative to their text. Reflow the layout when information density is the problem.
- **Writing new text over old text**: produces double strokes and shadows because font metrics differ. Remove the full old glyph bounds first.
- **Coarse white rectangles**: can leave old antialiasing outside the patch or erase nearby icons and rules. Inspect tight crops and reconstruct affected structure.
- **One-shot manual coordinates**: commonly cause overlaps and missed labels. Use a repeated render-crop-adjust loop.
- **Calling OCR output exact**: OCR can misread small Chinese characters and technical identifiers. Maintain a correction ledger.
- **Assuming Image2 text removal preserves geometry**: it can shift boxes, arrows, and icons. Compare the blank base with the source before adding text.
- **Treating Real-ESRGAN as text correction**: it sharpens or invents edges; it does not know which character is correct.
- **Rendering multiline HTML inside SVG without testing**: `<br>` and CSS line layout may not survive conversion. Emit explicit SVG text lines.
- **Using display size as pixel size on macOS**: AppKit point dimensions and embedded DPI can make new text unexpectedly small. Render against the actual pixel canvas.
- **Silent font fallback**: a fallback expression can change both family and size, making the same script render much smaller text on another machine. Log the selected font, preserve the intended size, and remeasure wrapping.
- **Trusting a batch `Done` line**: a loop can skip inputs, leave stale outputs, or finish after only part of the batch. Verify expected filenames, fresh modification times, successful decoding, and dimensions for every item.
- **Fixed line counts in fixed-height cards**: a nominal reflow can still push the last baseline outside the box. Measure glyph or line bounds after font resolution and fail the render on overflow.
- **Missing super-resolution tile seams**: tiled inference can produce inconsistent blocks. Inspect long straight rules, flat-color backgrounds, gradients, and text edges across tile boundaries.

## Artifact Contract

Keep the work reviewable:

- original source, unchanged;
- text ledger with location, exact text, confidence, and action;
- editable vector/layout source when rebuilding;
- blank base labeled as an intermediate when used;
- target-size candidate PNG;
- expected-input and verified-output manifests for batches;
- crop checks for text, icons, arrows, and dense regions;
- short report of what was verified and what remains uncertain.

## Acceptance Gate

A dense diagram is ready only when all applicable checks pass:

- every important label matches the source of truth character-for-character;
- no pseudo-Chinese, residual old text, doubled glyphs, or clipped lines remain;
- arrows, boxes, icons, logos, numbering, and relationships match the reference;
- text fits its boxes at the intended display size;
- automated or visual overflow checks confirm that glyph and line bounds stay inside their intended containers;
- target pixel dimensions and aspect ratio are correct;
- every expected batch item has a fresh, decodable output; output count and names match the manifest;
- 100% and 200% crop inspection shows no visible repair seams or sharpening halos;
- tiled super-resolution shows no block boundaries or discontinuities in rules, flat fills, gradients, or glyph strokes;
- editable sources and the final raster correspond to the same version.

If any hard check fails, report the output as a draft or partial result and name the failing regions.

## Real-ESRGAN on macOS

The ncnn Vulkan build uses MoltenVK and therefore Metal. A sandboxed agent process may report that Metal is unavailable even when the Mac has a capable Apple GPU. In that case, prepare deterministic inputs and a runnable script, then run it in an environment that exposes Metal. Verify actual outputs before claiming the batch completed.

For a target of 7680x4320, consider preparing 3840x2160 inputs and using 2x output. This keeps the target size bounded and avoids accidental 15360x8640 or 30720x17280 artifacts. Preserve the non-super-resolved candidate for comparison because small text can become less faithful after neural enhancement.
