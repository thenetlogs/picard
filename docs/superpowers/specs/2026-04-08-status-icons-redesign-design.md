# UX #6: Status Icons Redesign

## Summary

Replace PNG status icons with Unicode symbols rendered as QPixmaps. Clearer, scalable, zero external assets.

## Current State

- Status icons are small PNG files (match-50..100.png, file.png, file-pending.png, track-saved.png, etc.)
- Icons are tiny and details hard to see, especially on high-DPI displays
- Match quality shown via 6 graduated PNG icons (match-50 through match-100)
- Album icons use system theme icons (media-optical variants)

## Design

### File Status Icons

| State | Symbol | Color | Replaces |
|-------|--------|-------|----------|
| Unmatched file | ◇ | default text color | file.png |
| Pending (lookup in progress) | ⟳ | yellow (#f0c040) | file-pending.png |
| Matched (changed, unsaved) | ◆ | gradient by match quality | match-50..100.png |
| Saved (tags written) | ✔ | green (#50c878) | track-saved.png |
| Error | ⚠ | red (#e05050) | dialog-error |
| File not found | ⊘ | red (#e05050) | error-not-found |

### Match Quality Gradient (on ◆ symbol)

Same `_match_icon_index` logic, but instead of selecting different PNGs, the color of ◆ changes:

| Similarity | Color |
|-----------|-------|
| 50% | red (#e05050) |
| 60% | orange (#e08040) |
| 70% | yellow (#c0a040) |
| 80% | yellow-green (#80b050) |
| 90% | green (#50c060) |
| 100% | bright green (#50c878) |

Pending match uses the same gradient colors but with ⟳ symbol instead of ◆.

### Album Status Icons

| State | Symbol | Color |
|-------|--------|-------|
| Incomplete (not all tracks matched) | ◎ | default text color |
| Complete, unsaved (modified) | ◉ | blue (#4da6ff) |
| Complete, saved | ◉ | green (#50c878) |
| Error | ◉ | red (#e05050) |

### Implementation

**Icon rendering:** Create a helper function `render_unicode_icon(symbol, color, size)` that:
1. Creates a `QPixmap(size, size)` with transparent background
2. Uses `QPainter` + `drawText()` to render the Unicode symbol centered
3. Sets font size to fill the pixmap
4. Returns `QIcon(pixmap)`

**Icon caching:** Pre-render all icons in `MainPanel.create_icons()` (same as current PNG loading), stored as class attributes on `FileItem`, `AlbumItem`, etc. No per-frame rendering.

**Match quality icons:** Pre-render 6 ◆ icons (one per quality level) with the gradient colors above. Same for 6 pending ⟳ icons.

**Fallback:** If the font doesn't support a symbol (rare on modern systems), fall back to the existing PNG icons. Check via `QFontMetrics.inFont()`.

### Font Selection

Use the application's default font. Unicode symbols ◇ ◆ ◎ ◉ ✔ ⚠ ⊘ ⟳ are widely supported in system fonts (DejaVu Sans, Segoe UI, SF Pro, Noto Sans).

## Files Changed

| File | Changes |
|------|---------|
| `picard/ui/itemviews/__init__.py` | `create_icons()` — render Unicode instead of loading PNGs; `decide_file_icon_info()` and `AlbumItem.update()` — use new icon references |
| `picard/ui/iconrender.py` | New file: `render_unicode_icon()` helper |
| `test/test_status_icons.py` | Tests for icon rendering and state mapping |

## Out of Scope

- Changing match quality color gradient on row backgrounds (keep existing `get_match_color()`)
- Track type icons (audio/video/data) — keep as PNG
- Fingerprint column icons — keep existing
- Cluster icons — keep existing
