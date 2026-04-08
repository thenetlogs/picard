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
    # BaseTreeView.restore_state checks tagger._no_restore
    if not hasattr(app, '_no_restore'):
        app._no_restore = True
    yield app


class _FakeColumns(list):
    """Minimal columns stub satisfying ConfigurableColumnsHeader requirements."""
    default_width = 100

    def always_visible_columns(self):
        return []


def _make_test_view():
    """Create a minimal BaseTreeView for testing (shared helper)."""
    from picard.ui.itemviews.basetreeview import BaseTreeView

    class TestTreeView(BaseTreeView):
        NAME = "test"
        DESCRIPTION = "test view"

        def __init__(self):
            columns = _FakeColumns()
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

    def test_drop_active_default_false(self, qt_app):
        view = _make_test_view()
        assert view._drop_active is False
        assert view.styleSheet() == ""

    def test_set_drop_active_true(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        assert view._drop_active is True
        assert "border" in view.styleSheet()

    def test_set_drop_active_false(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        view._set_drop_active(False)
        assert view._drop_active is False
        assert view.styleSheet() == ""

    def test_set_drop_active_idempotent(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        view._set_drop_active(True)
        assert view._drop_active is True


class TestPanelDropZoneDragEvents:
    """Tests that drag events toggle drop_active."""

    def _make_drag_event(self, event_class, mime_data, pos=None, action=None):
        """Create a drag/drop event with MIME data."""
        if action is None:
            action = QtCore.Qt.DropAction.CopyAction
        # QDragEnterEvent/QDragMoveEvent take QPoint; QDropEvent takes QPointF
        if event_class in (QtGui.QDragEnterEvent, QtGui.QDragMoveEvent):
            if pos is None:
                pos = QtCore.QPoint(10, 10)
        else:
            if pos is None:
                pos = QtCore.QPointF(10, 10)
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
        assert view._drop_active is True

    def test_drag_leave_deactivates_drop_zone(self, qt_app):
        view = _make_test_view()
        view._set_drop_active(True)
        event = QtGui.QDragLeaveEvent()
        view.dragLeaveEvent(event)
        assert view._drop_active is False

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
        assert view._drop_active is False


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
