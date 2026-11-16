# Validation evidence for docling-parse #466

Fix commit: [906e823](https://github.com/ainuo-AI/docling-parse/commit/906e8236cebdca361c107d06b86176b2ed3598ff).
Base: `88f1c3886edea018499f3385619909b96ad06837`.
Dataset revision: `12531342c926708dcb1387ea25213db4603a7255`.

The primary regression is a missing `=` on page 5 of the existing corpus file
`10749817875312063576_009.pdf`. The original #466 PDF is the [Georgia DDS
Driver's Manual](https://dds.georgia.gov/document/document/ga-drivers-manual-2023-2024/download),
SHA256 `e311de54ad0ee6f5913e18e694914a560dac3592987437290c271f53c0c7fa71`.
Both reproduce through `PageParseResult.get_image()` without altering the PDF.

## Comparisons

Each image panel is labelled PDFium, main, or fix. They are actual renderer
captures; only layout, labels, cropping and explicitly magnified nearest-neighbor
views have been added. The full-page comparisons are at scale 3.

- [Original heading](figures/original-page10-heading.png) and [full page 10](figures/original-page10-full.png).
- [Existing article equation](figures/corpus-page5-equation.png) and [full page 5](figures/corpus-page5-full.png).
- [All 954 selected corpus pages](corpus-before-after.csv).
- [All 52 original-manual pages](original-52-before-after.csv).
- [Empty affected-character-cell diff](cited-cell-diff.json): six `n` cells and one `=` cell retain identical data.

There are 457 hash-checked corpus PDFs. Page coverage is the repository's
default 954-page selection, not every page of every document. All selected
pages succeeded, and native/PDFium image sizes match. No resizing was needed.
The corpus and original-manual images and metrics consistently use pypdfium2
5.15.2. Metrics follow the repository's RGBA MAE and luminance threshold 12.

The corpus has 934 pixel-identical pages, 17 with lower MAE, and 3 with tiny
MAE increases. At scale 2 those increases are 0.000086678, 0.000000374 and
0.000003782. They are real, repeatable differences. See [risk-scales.csv](risk-scales.csv),
[risk-review.json](risk-review.json), and the `figures/risk-*.png` crops.

Each build was rendered three times independently at scale 2 on each of those
pages, with matching hashes; the results also match the initial corpus run.
Comparisons at scales 1, 2, 3 and 4 retain the same maximum MAE increase.
Their baseline positions, font identities, mappings and non-text instructions
are unchanged. A reconstruction from the exported text quads and metrics
gives effective-size differences of at most 1.84e-12 pixels at scale 2, which
is consistent with rounding sensitivity. It is not an instrumented Blend2D
trace or a proof of zero risk on other platforms.

One scale-1 comparison has a larger positive change: an instruction exported
as `J` with character code 45 on `926659986622553168-1.pdf` page 2 crosses the
old 0.5-pixel early-return threshold. The fix draws 8 additional/different
pixels and reduces MAE. The decoded text value is not a manual identification
of the symbol's shape. Thus the scale-2 maximum channel changes should not be
read as a bound on every scale.

## Groundtruth scope

[groundtruth-changes.csv](groundtruth-changes.csv) lists 145 normalized
instruction-output changes across 81 documents, using the existing project's
three-decimal normalization. Of these pages, 125 still have identical pixels.
Only text quads and normalized font ascent/descent change; instruction counts,
ordering and non-text data are unchanged. Hashed per-field outputs for all
954 pages and both builds are in `instructions/`.

This is a fresh main/fix comparison. Stored remote groundtruth blobs were not
downloaded, rewritten, or claimed to pass. `HF_DATASET_REVISION` is unchanged;
maintainers own the fixture review/update. The internal instruction export is
used only for this groundtruth audit; the bug reproduction and enforced image
tests use supported public APIs.

## Tests and limits

- pypdfium2 5.15.2: main has 9 expected failures, 3 passing controls and 5
  deselected pre-existing cases; the related fixed suite passes 97 tests with
  1 existing Arabic-fallback skip.
- Locked pypdfium2 5.14.0: main has the same 9 failures/3 passing controls;
  both fixed test modules pass all 17 cases. Full-corpus measurements use 5.15.2.
- The eight generated TrueType cases isolate the numeric AFM/CID collision
  on two rendering paths. The real formula is the ninth failing case. Three
  real whole-page controls pass on both versions and use embedded text fonts.
  Their MAE limits are 5.0 / 2.5 / 4.0, below the general report cutoff 9.0.
  Their changed-ratio limits are 0.15 / 0.07 / 0.14; the first and third are
  above the report cutoff 0.09 because main already measures 0.13577 / 0.12286
  on those pages. These are page-specific controls, not tighter bounds on
  both metrics, and no global tolerance was changed.
- Ruff format/check, offline `uv lock --check` and whitespace checks pass.
- MyPy has the same 19 baseline errors on main and fix in this Windows
  environment. The logs show missing optional benchmark packages and POSIX-only
  interfaces. This is not a claim of a green full pre-commit or CI run.
- Local build: Windows x64, Python 3.12.10, GCC 13.1.0, Release. macOS/Linux,
  the complete stored-groundtruth suite and OCR were not run locally. CI is
  separate from these local results.

Run [reproduce_public.py](reproduce_public.py) in main and patched environments
with the original PDF, or pass the existing corpus PDF with
`--page 5 --crop 100 124 114 139`. The small standalone script is portable;
the test matrix's workspace prefixes are shortened in the public logs and JSON.
Otherwise logged test outcomes are preserved. Original unshortened records
remain in the local review bundle.

The native extension hashes and reviewed source hashes are in `manifest.json`.
No original PDFs, extracted font programs, native binaries, credentials or
raw private instruction dumps are included in this snapshot.
