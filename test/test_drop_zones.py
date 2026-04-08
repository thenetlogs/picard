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
