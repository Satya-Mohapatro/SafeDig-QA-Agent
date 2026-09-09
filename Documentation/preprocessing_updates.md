# SafeDig QA Agent — Image Preprocessing Updates

## Overview

Preprocessing refers to everything the system does **before** a human reviewer sees a result — turning raw PDF map files into structured data: AOI boundaries, hazard candidates, and rendered overlay images. Six major areas were updated.

---

## 1. Map Frame Detection (What counts as "the map area")

Before any AOI or hazard can be detected, the system must know **which part of the page is the actual map cartography** versus the legend, title block, footer, or margin.

### 1a. Vector CAD Viewport Detection — Thames Water

**Problem:** Thames Water `Clean_Water.pdf` draws its map inside a CAD viewport made of 4 individual line segments (not a PDF rectangle primitive). The old detector only looked for `re`/`qu` rectangle items and missed this entirely, so the entire page (including legend) was treated as the map area.

**Fix in [`_find_vector_map_frame()`](file:///D:/SafeDig_AG/src/aoi/detector.py#L68-L135):**

```
Old approach:
  Only looked for rect primitives (re / qu) in drawing items

New approach:
  ALSO collects all long solid horizontal lines (width ≥ 50% of page)
  and long solid vertical lines (height ≥ 40% of page), then checks
  whether any 4 such lines form an enclosed orthogonal viewport box.
```

**Result:** Thames Water map frame now correctly detected as `[28.6, 28.6, 813.3, 453.5]` — the full cartographic area including the North arrow and all water mains, instead of being clipped at x=690.

---

### 1b. Pure-Raster Frame Detection — BT

**Problem:** BT PDFs (`BT.pdf`) contain a high-resolution raster image embedded in the PDF. There are no PDF vector drawings to scan — the map frame, legend, and header are all baked into the raster pixels.

**Fix — New [`_find_raster_map_frame()`](file:///D:/SafeDig_AG/src/aoi/detector.py#L137-L186):**

Uses **morphological pixel scanning** at 1:1 scale (no DPI upscaling needed):

```
Step 1 — Find the legend separator:
  Scans rows from 50%→85% of page height.
  A row with >65% dark pixels is the bold black line between
  cartographic area and the multi-column legend block below it.

Step 2 — Find the top border:
  Scans rows from 4%→20% of page height.
  A row with >80% dark pixels (in the middle 70% width) is the
  top black border of the map cartographic area.

Step 3 — Find left and right borders:
  Scans columns inward from the left and right edges.
  A column with >80% dark pixels between top and legend separator
  is the left / right border of the map.

Result: [left_x, top_y, right_x, sep_y] in PDF points.
```

**Result:** BT frame correctly detected as `[75.0, 100.0, 1175.0, 1200.0]` — the inner cartographic box, completely excluding the top header banner and the bottom multi-column symbol legend.

---

## 2. AOI (Area of Interest) Detection Fixes

The AOI is the pink/red dashed enquiry boundary drawn by the utility company showing the dig site area. The system detects this from vector drawings.

### 2a. True Circle Detection

**Problem:** Many utilities (NGED, WWU, UKPN) draw the enquiry boundary as a **circle made of 64 short line-segments** (approximated circle), not a rectangle. The old code only detected rectangular bounding boxes.

**Fix in [`_detect_circle_from_items()`](file:///D:/SafeDig_AG/src/aoi/detector.py):**

```
Algorithm:
  1. Collect all endpoints from the drawing's line/curve items
  2. Compute the geometric centroid of those endpoints
  3. Compute each endpoint's distance from the centroid (radius samples)
  4. If std_dev(distances) / mean(distance) < 0.08  →  it's a circle
     (i.e. all points are within 8% deviation of the mean radius)
  5. Returns (cx, cy, r) in unrotated PDF points
```

When a circle is confirmed, the AOI is stored with `geometry_type = CIRCLE`, `circle_center`, and `circle_radius` — enabling accurate circle overlay rendering.

---

### 2b. UKPN Rotated Page Coordinate Fix

**Problem:** `UKPN_42336414.pdf` has `page.rotation = 90`. PyMuPDF returns all drawing coordinates in **unrotated mediabox space** (portrait, origin bottom-left), but `get_pixmap()` renders the page in **visual orientation** (landscape, after applying the rotation). The circle centre was stored as `(225.5, 420.0)` in unrotated space, but the rendered image was landscape — causing the red overlay circle to be drawn at the **bottom-left** of the image instead of the map centre.

**Fix in [`detect_aoi_from_pdf()`](file:///D:/SafeDig_AG/src/aoi/detector.py#L691-L741):**

After the circle `(cx, cy, r)` is extracted in unrotated coordinates, it is immediately converted to **visual rendering coordinates** using the existing `_unrotated_to_visual()` helper:

```python
# For rotation=90, mh=842:
#   visual_x = mh - cy  =  842 - 420.0  =  422.0
#   visual_y = cx        =  225.5

vis_bbox = _unrotated_to_visual(
    pymupdf.Rect(cx-r, cy-r, cx+r, cy+r),
    rotation, mediabox
)
cx_vis = (vis_bbox.x0 + vis_bbox.x1) / 2.0
cy_vis = (vis_bbox.y0 + vis_bbox.y1) / 2.0

# Stored as visual coords → crops.py draws circle correctly
circle_center = [cx_vis, cy_vis]   # ← visual
# bbox and coordinates stay unrotated for spatial intersection ops
bbox = [cx-r, cy-r, cx+r, cy+r]   # ← unrotated
```

| | Before | After |
|---|---|---|
| `circle_center` stored | `[225.5, 420.0]` (unrotated) | `[422.0, 225.5]` (visual) |
| Circle drawn at | Bottom-left of image ❌ | Exactly on pink dashed boundary ✓ |

Works for all rotation values (0°, 90°, 180°, 270°) via `_unrotated_to_visual()`.

---

## 3. AOI Overlay Rendering (crops.py)

Once the AOI is detected, the system renders the full PDF page as a PNG and draws the AOI boundary on top as a coloured overlay.

**Fix in [`generate_aoi_map_render()`](file:///D:/SafeDig_AG/src/evidence/crops.py#L69-L199):**

Previously, all AOI types were rendered as rectangles. Now:

| AOI Geometry | How it's rendered |
|---|---|
| `CIRCLE` | `cv2.circle(img, (cx_px, cy_px), r_px, ...)` — true smooth circle |
| `POLYGON` | `cv2.polylines(img, [pts_arr], True, ...)` — exact polygon outline |
| `RECTANGLE` / fallback | `cv2.rectangle(img, (bx0, by0), (bx1, by1), ...)` |

Each shape is drawn as a **dual-stroke** (thick dark-red outer glow + sharp bright-red inner) for visibility on all map backgrounds. An "**AOI SITE BOUNDARY**" badge is positioned at the top of the boundary.

```python
# Circle example:
cv2.circle(img, (cx_px, cy_px), r_px + 2, (0, 0, 160), 6)   # dark glow
cv2.circle(img, (cx_px, cy_px), r_px,     (0, 0, 255), 4)   # bright red
```

---

## 4. Coordinate System (coordinates.py)

The `coordinate_transformer.pdf_to_pixel()` function scales from PDF points to pixels:

```python
scale = dpi / 72.0
pixel_x = int(round(x_pt * scale))
pixel_y = int(round(y_pt * scale))
```

PyMuPDF's `get_pixmap(matrix=Matrix(zoom, zoom))` renders in visual orientation where `(0,0)` is the top-left pixel. After the UKPN fix, all stored coordinates passed to `pdf_to_pixel()` are already in visual space — so the simple scale-only formula works correctly for all pages regardless of rotation.

---

## 5. Raster Page OCR — Missing Map Data Detection (inspector.py)

**Problem:** Some GTC portal enquiry responses (e.g. "No GTC plant has been found in the area selected — a confirmation email has been sent") produce PDF pages that are **pure raster images** with no extractable text. The system was treating these as normal maps.

**Fix in [`src/pdf/inspector.py`](file:///D:/SafeDig_AG/src/pdf/inspector.py):**

For raster pages (detected when `page.get_text()` returns < 20 characters), the system now:

1. Renders the page to a PIL image via `page.get_pixmap()`
2. Runs **Windows native OCR** (`winocr.recognize_cv2()`) — zero network, no GPU, uses the built-in Windows.Media.Ocr WinRT API
3. Searches the OCR output for portal enquiry keywords:
   ```
   "confirmation email", "no gtc plant", "no plant found",
   "enquiry reference", "area selected", "no apparatus"
   ```
4. If matched → sets `document.is_missing_map_data = True` and stores the extracted notice verbatim as `document.extracted_notice`

**Policy consequence:** Any document with `is_missing_map_data=True` is **immediately BLOCKED** by the policy engine — it never reaches AUTO_CLEAR regardless of any other gate results.

---

## 6. Map Image Route — Evidence Serving (evidence.py)

The API endpoint `GET /evidence/{document_id}/map-image` serves the rendered AOI overlay PNG to the UI.

**Fix in [`get_document_map_image()`](file:///D:/SafeDig_AG/src/api/routes/evidence.py):**

The previous implementation tried to re-render the PDF from scratch on every request, failing when the source path wasn't cached. New logic:

```
Priority order:
  1. Check for pre-rendered  aoi_overview_{document_id}.png  in qa_output/
  2. Read root_dir + filename from  job_report.json
  3. Read from  document_results.json
  4. Read from  manifest.json
  5. Fallback: resolve_folder_path() pattern-matching on Data/ directory
```

This means the first pipeline run writes the rendered image once, and subsequent requests serve it instantly from disk — no re-rendering on every UI refresh.

---

## Summary Table

| File | What Changed | Impact |
|---|---|---|
| [`src/aoi/detector.py`](file:///D:/SafeDig_AG/src/aoi/detector.py) | CAD 4-line viewport detection (`_find_vector_map_frame`) | Thames Water map frame correct |
| [`src/aoi/detector.py`](file:///D:/SafeDig_AG/src/aoi/detector.py) | Morphological raster frame scan (`_find_raster_map_frame`) | BT map frame excludes legend |
| [`src/aoi/detector.py`](file:///D:/SafeDig_AG/src/aoi/detector.py) | Circle AOI detection from 64-segment approximations | NGED/WWU/UKPN circular boundaries detected |
| [`src/aoi/detector.py`](file:///D:/SafeDig_AG/src/aoi/detector.py) | Visual-coord conversion for rotated pages (`_unrotated_to_visual`) | UKPN circle drawn at correct position |
| [`src/evidence/crops.py`](file:///D:/SafeDig_AG/src/evidence/crops.py) | True circle + polygon cv2 rendering, dual-stroke, badge | AOI overlay matches actual boundary shape |
| [`src/spatial/coordinates.py`](file:///D:/SafeDig_AG/src/spatial/coordinates.py) | No change — confirmed `pdf_to_pixel` works with visual coords | Consistent with renderer output |
| [`src/pdf/renderer.py`](file:///D:/SafeDig_AG/src/pdf/renderer.py) | Uses `page.get_pixmap(matrix=mat)` — renders in visual orientation | All overlays correctly aligned |
| [`src/pdf/inspector.py`](file:///D:/SafeDig_AG/src/pdf/inspector.py) | WinRT OCR for raster pages, missing-data detection | GTC portal enquiry = BLOCKED |
| [`src/api/routes/evidence.py`](file:///D:/SafeDig_AG/src/api/routes/evidence.py) | Cache-first map image serving, 5-source fallback | Map images load correctly in UI |
