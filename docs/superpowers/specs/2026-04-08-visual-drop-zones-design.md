# UX #4: Visual Drop Zones

## Summary

Add visual feedback during drag-and-drop operations in Picard's dual-pane interface. Uses a layered approach: subtle panel-level glow indicates a valid drop zone, while a row-level accent bar shows the exact drop target.

## Current State

- Qt's default thin drop indicator line (barely visible)
- `EmptyStateWidget` has its own drag hover feedback (dashed border → highlight) — only shown when panels are empty
- No visual feedback when dragging over a populated panel or specific album/track row
- No visual difference between the source panel and the target panel during drag

## Design Decisions

- **Style: Layered** — panel glow for general "you can drop here" + row accent for precise "drop exactly here"
- **External drag: Single panel** — only the panel under the cursor highlights (not both)
- **Colors: palette(highlight)** — uses Qt system palette for automatic dark/light theme support
- **Source dimming: Optional** — dim the dragged item to ~40% opacity if feasible, skip if Qt item rendering makes it complex

## 1. Panel-Level Drop Zone

When a drag enters a `BaseTreeView`, the panel shows a border glow:

**Normal state:**
- `border: 1px solid palette(mid)` (existing)

**Drag hover state:**
- `border: 2px solid palette(highlight)` at 40% opacity
- `box-shadow: 0 0 6px palette(highlight)` at 15% opacity, inset
- Transition: 200ms via Qt stylesheet property binding

**Implementation:**
- Add `_set_drop_active(active: bool)` to `BaseTreeView`, modeled after `EmptyStateWidget._set_drag_hover()`
- Uses Qt dynamic property `drop_active` ("true"/"false") + stylesheet selector `[drop_active="true"]`
- Call `style().unpolish(self)` / `style().polish(self)` to force re-evaluation
- Set `True` in `dragEnterEvent`, `False` in `dragLeaveEvent` and `dropEvent`

**File:** `picard/ui/itemviews/basetreeview.py`

## 2. Row-Level Highlight

When dragging over a specific tree item, that row gets an accent bar:

**Highlight style:**
- Background: `rgba(highlight, 18%)`
- Left border: `3px solid palette(highlight)`
- No animation (instant) — row changes on every mouse move during drag

**Implementation:**
- Override `dragMoveEvent` in `BaseTreeView`:
  1. Call `super().dragMoveEvent(event)` (preserves existing external drag handling)
  2. Get item under cursor via `self.itemAt(event.position().toPoint())`
  3. If different from `self._drop_highlight_item`, clear previous highlight, apply new
- Track highlighted item in `self._drop_highlight_item: QTreeWidgetItem | None`
- Apply highlight via `item.setBackground(column, highlight_brush)` for all columns
- Clear on `dragLeaveEvent` and `dropEvent` (call `_clear_drop_highlight()`)
- Store original background in `self._drop_highlight_orig_bg: dict[int, QBrush]` (column → brush) before applying highlight, restore on clear. This preserves match-quality gradient colors that Picard applies to track rows.

**File:** `picard/ui/itemviews/basetreeview.py`

## 3. External Drag (from File Manager)

Behavior is identical to internal drag — same panel glow + row highlight. Qt already dispatches `dragEnterEvent` for external drags. The existing `_handle_external_drag()` method already accepts external drops — the new `_set_drop_active()` call just needs to be added alongside it.

`EmptyStateWidget` already has its own drag hover feedback — no changes needed there.

## 4. Source Item Dimming (Optional)

When a drag starts, the source items become semi-transparent (~40% opacity) to show "these are being moved."

**Implementation (if feasible):**
- In `startDrag()`: iterate selected items, reduce foreground color alpha
- After drag completes: restore original colors
- Skip if Qt `QTreeWidgetItem` color manipulation proves unreliable

**File:** `picard/ui/itemviews/basetreeview.py`

## Files Changed

| File | Changes |
|------|---------|
| `picard/ui/itemviews/basetreeview.py` | `_set_drop_active()`, `_clear_drop_highlight()`, modified `dragEnterEvent`, `dragMoveEvent`, `dragLeaveEvent`, `dropEvent`, optionally `startDrag` |
| `picard/ui/itemviews/__init__.py` | Panel container stylesheet for `drop_active` property (if needed at container level) |
| `test/test_ui_drop_zones.py` | Tests for drop zone visual state management |

## Out of Scope

- Keyboard alternative to drag-and-drop (UX #2 — deferred)
- Custom drag pixmap styling (current rendered pixmap is sufficient)
- Cross-panel "move" indicator text in the header (decided against — too noisy)
