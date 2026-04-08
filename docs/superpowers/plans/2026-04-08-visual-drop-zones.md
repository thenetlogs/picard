# Visual Drop Zones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add layered visual feedback during drag-and-drop: panel-level border glow + row-level accent bar.

**Architecture:** All changes in `BaseTreeView` (the base class for both `FileTreeView` and `AlbumTreeView`). Panel glow uses Qt stylesheet property binding (same pattern as `EmptyStateWidget._set_drag_hover`). Row highlight uses `QTreeWidgetItem.setBackground()` with saved/restored original backgrounds.

**Tech Stack:** PyQt6, Qt stylesheets, pytest

**Spec:** `docs/superpowers/specs/2026-04-08-visual-drop-zones-design.md`

**Known Qt CSS limitations (spec deviations):**
- `box-shadow` is not supported in Qt stylesheets — panel glow uses border-only styling
- CSS `transition` is not supported — property changes apply instantly (no 200ms fade)
- Per-item left border accent bar is not possible via `QTreeWidgetItem` — row highlight uses background tint only. A custom `QStyledItemDelegate` would be needed for the left bar, deferred as optional enhancement.

---

### Task 1: Panel-level drop zone — test + implementation

**Files:**
- Modify: `picard/ui/itemviews/basetreeview.py:177-209` (BaseTreeView.__init__, add _set_drop_active)
- Modify: `picard/ui/itemviews/basetreeview.py:549-560` (dragEnterEvent, dragMoveEvent)
- Test: `test/test_drop_zones.py` (new file)

- [ ] **Step 1: Write failing tests for _set_drop_active**

Create `test/test_drop_zones.py`:

```python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 metaisfacil
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)


@pytest.fixture(scope="module")
def qt_app():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv[:1])
    yield app


def _make_test_view():
    """Create a minimal BaseTreeView for testing (shared helper)."""
    from picard.ui.itemviews.basetreeview import BaseTreeView

    class TestTreeView(BaseTreeView):
        NAME = "test"
        DESCRIPTION = "test view"

        def __init__(self):
            columns = []
            window = type('W', (), {
                'selected_objects': [],
                'update_selection': lambda *a: None,
            })()
            super().__init__(columns, window)

    return TestTreeView()


def _make_test_view_with_items(col_count=2, item_count=3):
    """Create a BaseTreeView with test items (shared helper)."""
    view = _make_test_view()
    view.setColumnCount(col_count)
    for i in range(item_count):
        item = QtWidgets.QTreeWidgetItem([f"Item {i}"] + [f"Col{c} {i}" for c in range(1, col_count)])
        view.addTopLevelItem(item)
    return view


class TestPanelDropZone:
    """Tests for BaseTreeView panel-level drop zone visual feedback."""

    def test_drop_active_property_default_false(self, qt_app):
        view = _make_test_view()
        assert view.property("drop_active") == "false"

    def test_set_drop_active_true(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        assert view.property("drop_active") == "true"

    def test_set_drop_active_false(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        view._set_drop_active(False)
        assert view.property("drop_active") == "false"

    def test_set_drop_active_idempotent(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        view._set_drop_active(True)
        assert view.property("drop_active") == "true"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py -v`
Expected: FAIL — `_set_drop_active` does not exist yet.

- [ ] **Step 3: Implement _set_drop_active and stylesheet**

In `picard/ui/itemviews/basetreeview.py`, add to `BaseTreeView.__init__` (after line 196, after `self.setDropIndicatorShown(True)`):

```python
        # Drop zone visual feedback
        self._drop_active = False
        self.setProperty("drop_active", "false")
        self.setStyleSheet(
            "*[drop_active=\"true\"] {"
            "  border: 2px solid palette(highlight);"
            "  border-radius: 3px;"
            "}"
        )
```

Note: Qt stylesheet type selectors match C++ class names, not Python subclass names. `BaseTreeView` would not match — use universal selector `*` instead (same approach works for `FileTreeView` and `AlbumTreeView` since the property is set on each instance).

Add the `_set_drop_active` method to `BaseTreeView` (after `_handle_external_drag`):

```python
    def _set_drop_active(self, active):
        """Toggle panel-level drop zone visual feedback."""
        if self._drop_active == active:
            return
        self._drop_active = active
        self.setProperty("drop_active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py::TestPanelDropZone -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add test/test_drop_zones.py picard/ui/itemviews/basetreeview.py
git commit -m "ux(#04): add panel-level drop zone property + stylesheet + tests"
```

---

### Task 2: Wire panel drop zone into drag events

**Files:**
- Modify: `picard/ui/itemviews/basetreeview.py:549-637` (dragEnterEvent, dragMoveEvent, dropEvent, add dragLeaveEvent)

- [ ] **Step 1: Write failing tests for drag event integration**

Add to `test/test_drop_zones.py`:

```python
class TestPanelDropZoneDragEvents:
    """Tests that drag events toggle drop_active."""

    def _make_drag_event(self, event_class, mime_data, pos=None, action=None):
        """Create a drag/drop event with MIME data."""
        if pos is None:
            pos = QtCore.QPointF(10, 10)
        if action is None:
            action = QtCore.Qt.DropAction.CopyAction
        return event_class(
            pos,
            action,
            mime_data,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )

    def test_drag_enter_activates_drop_zone(self, qt_app):
        view = _make_test_view()
        mime = QtCore.QMimeData()
        mime.setUrls([QtCore.QUrl.fromLocalFile("/tmp/test.flac")])
        event = self._make_drag_event(QtGui.QDragEnterEvent, mime)
        view.dragEnterEvent(event)
        assert view.property("drop_active") == "true"

    def test_drag_leave_deactivates_drop_zone(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        event = QtGui.QDragLeaveEvent()
        view.dragLeaveEvent(event)
        assert view.property("drop_active") == "false"

    def test_drop_deactivates_drop_zone(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        mime = QtCore.QMimeData()
        # Use IgnoreAction to hit the early return path and avoid
        # QTreeView.dropEvent internals crashing in headless env
        event = self._make_drag_event(
            QtGui.QDropEvent, mime,
            action=QtCore.Qt.DropAction.IgnoreAction,
        )
        view.dropEvent(event)
        assert view.property("drop_active") == "false"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py::TestPanelDropZoneDragEvents -v`
Expected: FAIL — `dragLeaveEvent` not overridden, `dragEnterEvent` doesn't call `_set_drop_active`.

- [ ] **Step 3: Modify drag events in BaseTreeView**

In `picard/ui/itemviews/basetreeview.py`, update `dragEnterEvent`:

```python
    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        self._handle_external_drag(event)
        self._set_drop_active(True)
```

Add new `dragLeaveEvent` (after `_handle_external_drag`):

```python
    def dragLeaveEvent(self, event):
        self._set_drop_active(False)
        self._clear_drop_highlight()
        super().dragLeaveEvent(event)
```

Update `dropEvent` — add cleanup at the start:

```python
    def dropEvent(self, event):
        self._set_drop_active(False)
        self._clear_drop_highlight()
        if event.proposedAction() == QtCore.Qt.DropAction.IgnoreAction:
            event.acceptProposedAction()
            return
        # Dropping with Alt key pressed forces all dropped files being
        # assigned to the same track.
        if event.modifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            self._move_to_multi_tracks = False
        QtWidgets.QTreeView.dropEvent(self, event)
        # The parent dropEvent implementation automatically accepts the proposed
        # action. Override this, for external drops we never support move (which
        # can result in file deletion, e.g. on Windows).
        if event.isAccepted() and (not event.source() or event.mimeData().hasUrls()):
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()
```

Add stub `_clear_drop_highlight` (implemented in Task 3):

```python
    def _clear_drop_highlight(self):
        """Clear row-level drop highlight. Implemented in Task 3."""
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py -v`
Expected: All tests PASS (both TestPanelDropZone and TestPanelDropZoneDragEvents).

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/ui/itemviews/basetreeview.py test/test_drop_zones.py
git commit -m "ux(#04): wire panel drop zone into dragEnter/dragLeave/drop events"
```

---

### Task 3: Row-level drop highlight — test + implementation

**Files:**
- Modify: `picard/ui/itemviews/basetreeview.py` (_clear_drop_highlight, _set_drop_highlight, dragMoveEvent)
- Modify: `test/test_drop_zones.py`

- [ ] **Step 1: Write failing tests for row highlight**

Add to `test/test_drop_zones.py`:

```python
class TestRowDropHighlight:
    """Tests for row-level drop highlight."""

    def test_set_drop_highlight_applies_background(self, qt_app):
        view = _make_test_view_with_items()
        item = view.topLevelItem(0)
        view._set_drop_highlight(item)
        bg = item.background(0)
        assert bg.style() != QtCore.Qt.BrushStyle.NoBrush

    def test_set_drop_highlight_tracks_item(self, qt_app):
        view = _make_test_view_with_items()
        item = view.topLevelItem(1)
        view._set_drop_highlight(item)
        assert view._drop_highlight_item is item

    def test_clear_drop_highlight_restores_background(self, qt_app):
        view = _make_test_view_with_items()
        item = view.topLevelItem(0)
        orig_bg = item.background(0)
        view._set_drop_highlight(item)
        view._clear_drop_highlight()
        restored_bg = item.background(0)
        assert restored_bg.style() == orig_bg.style()
        assert view._drop_highlight_item is None

    def test_set_highlight_on_new_item_clears_previous(self, qt_app):
        view = _make_test_view_with_items()
        item0 = view.topLevelItem(0)
        item1 = view.topLevelItem(1)
        view._set_drop_highlight(item0)
        view._set_drop_highlight(item1)
        assert item0.background(0).style() == QtCore.Qt.BrushStyle.NoBrush
        assert item1.background(0).style() != QtCore.Qt.BrushStyle.NoBrush
        assert view._drop_highlight_item is item1

    def test_set_highlight_same_item_noop(self, qt_app):
        view = _make_test_view_with_items()
        item = view.topLevelItem(0)
        view._set_drop_highlight(item)
        view._set_drop_highlight(item)
        assert view._drop_highlight_item is item

    def test_clear_highlight_when_none_is_noop(self, qt_app):
        view = _make_test_view_with_items()
        view._clear_drop_highlight()
        assert view._drop_highlight_item is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py::TestRowDropHighlight -v`
Expected: FAIL — `_set_drop_highlight` does not exist.

- [ ] **Step 3: Implement row highlight methods**

In `picard/ui/itemviews/basetreeview.py`, add to `__init__` (after the drop zone lines):

```python
        # Row-level drop highlight
        self._drop_highlight_item = None
        self._drop_highlight_orig_bg = {}
```

Replace the stub `_clear_drop_highlight` with the real implementation, and add `_set_drop_highlight`:

```python
    def _set_drop_highlight(self, item):
        """Apply highlight to the given tree item as a drop target."""
        if item is self._drop_highlight_item:
            return
        self._clear_drop_highlight()
        self._drop_highlight_item = item
        col_count = self.columnCount()
        self._drop_highlight_orig_bg = {
            col: item.background(col) for col in range(col_count)
        }
        highlight_color = self.palette().highlight().color()
        highlight_color.setAlphaF(0.18)
        brush = QtGui.QBrush(highlight_color)
        for col in range(col_count):
            item.setBackground(col, brush)

    def _clear_drop_highlight(self):
        """Clear row-level drop highlight, restoring original backgrounds."""
        if self._drop_highlight_item is None:
            return
        for col, bg in self._drop_highlight_orig_bg.items():
            self._drop_highlight_item.setBackground(col, bg)
        self._drop_highlight_item = None
        self._drop_highlight_orig_bg = {}
```

Update `dragMoveEvent` to call `_set_drop_highlight`:

```python
    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        self._handle_external_drag(event)
        item = self.itemAt(event.position().toPoint())
        if item is not None:
            self._set_drop_highlight(item)
        else:
            self._clear_drop_highlight()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/ui/itemviews/basetreeview.py test/test_drop_zones.py
git commit -m "ux(#04): add row-level drop highlight with background save/restore"
```

---

### Task 4: Source item dimming (optional)

**Files:**
- Modify: `picard/ui/itemviews/basetreeview.py:562-574` (startDrag)
- Modify: `test/test_drop_zones.py`

- [ ] **Step 1: Write failing tests for source dimming**

Add to `test/test_drop_zones.py`:

```python
class TestSourceItemDimming:
    """Tests for source item dimming during drag."""

    def test_dim_source_items_reduces_opacity(self, qt_app):
        view = _make_test_view_with_items()
        items = [view.topLevelItem(0), view.topLevelItem(1)]
        view._dim_source_items(items)
        for item in items:
            fg = item.foreground(0).color()
            assert fg.alphaF() < 1.0

    def test_restore_source_items_resets_opacity(self, qt_app):
        view = _make_test_view_with_items()
        items = [view.topLevelItem(0)]
        view._dim_source_items(items)
        view._restore_source_items()
        assert items[0].foreground(0).style() == QtCore.Qt.BrushStyle.NoBrush

    def test_restore_when_nothing_dimmed_is_noop(self, qt_app):
        view = _make_test_view_with_items()
        view._restore_source_items()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py::TestSourceItemDimming -v`
Expected: FAIL — `_dim_source_items` does not exist.

- [ ] **Step 3: Implement source dimming**

In `picard/ui/itemviews/basetreeview.py`, add to `__init__`:

```python
        # Source item dimming during drag
        self._dimmed_items = []
        self._dimmed_orig_fg = {}
```

Add methods:

```python
    def _dim_source_items(self, items):
        """Dim the foreground of items being dragged."""
        self._dimmed_items = list(items)
        self._dimmed_orig_fg = {}
        col_count = self.columnCount()
        for item in items:
            self._dimmed_orig_fg[id(item)] = {
                col: item.foreground(col) for col in range(col_count)
            }
            fg_color = self.palette().text().color()
            fg_color.setAlphaF(0.4)
            dim_brush = QtGui.QBrush(fg_color)
            for col in range(col_count):
                item.setForeground(col, dim_brush)

    def _restore_source_items(self):
        """Restore dimmed items to their original foreground."""
        if not self._dimmed_items:
            return
        for item in self._dimmed_items:
            orig = self._dimmed_orig_fg.get(id(item), {})
            for col, brush in orig.items():
                item.setForeground(col, brush)
        self._dimmed_items = []
        self._dimmed_orig_fg = {}
```

Update `startDrag` to dim selected items and restore after drag completes:

```python
    def startDrag(self, supportedActions):
        """Start drag, *without* using pixmap."""
        items = self.selectedItems()
        if items:
            self._dim_source_items(items)
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.mimeData(items))
            item = self.currentItem()
            rectangle = self.visualItemRect(item)
            pixmap = QtGui.QPixmap(rectangle.width(), rectangle.height())
            self.viewport().render(pixmap, QtCore.QPoint(), QtGui.QRegion(rectangle))
            drag.setPixmap(pixmap)
            drag.exec(QtCore.Qt.DropAction.MoveAction)
            self._restore_source_items()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/ui/itemviews/basetreeview.py test/test_drop_zones.py
git commit -m "ux(#04): add source item dimming during drag"
```

---

### Task 5: Build, deploy Docker, and verify visually

**Files:**
- No code changes — verification only

- [ ] **Step 1: Run full test suite**

Run: `cd ~/picard && python -m pytest test/test_drop_zones.py test/test_emptystate.py test/test_workflowstep.py -v`
Expected: All tests PASS. Existing tests not broken.

- [ ] **Step 2: Build Docker image**

```bash
cd ~/picard
docker build -f /opt/docker/picard/build/Dockerfile.v3 -t picard-ux:latest .
```

- [ ] **Step 3: Restart container**

```bash
docker stop picard && docker rm picard
docker run -d \
  --name picard \
  -p 192.168.4.101:5800:5800 \
  -v /opt/docker/picard/config:/config \
  -v /srv/nextcloud/backup-external/music:/music \
  picard-ux:latest
```

- [ ] **Step 4: Visual verification in browser**

Open http://192.168.4.101:5800 and verify:

1. **Panel glow:** Drag a file from left panel to right — right panel shows blue border glow
2. **Row highlight:** While dragging, hover over specific album/track — row gets blue accent bar + tinted background
3. **Source dimming:** The item being dragged appears dimmer in the source panel
4. **External drag:** Drag a file from file browser widget — same visual feedback
5. **Cleanup:** After dropping, all visual indicators reset to normal
6. **EmptyState:** If a panel is empty, the existing dashed border hover still works

- [ ] **Step 5: Push to GitHub**

```bash
cd ~/picard && git push origin master
```
