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

# Use offscreen platform so tests run without a display
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)


@pytest.fixture(scope="module")
def qt_app():
    """QApplication instance for widget tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv[:1])
    yield app


# ---------------------------------------------------------------------------
# EmptyStateWidget tests
# ---------------------------------------------------------------------------

class TestEmptyStateWidget:
    def test_init_with_all_params(self, qt_app):
        """Widget creates with icon, title, description, cta_text."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget(
            "Hello",
            icon_name='folder',
            description="Some description",
            cta_text="Click me",
            accept_drops=True,
        )
        assert w is not None
        assert w._description_label is not None
        assert w._cta_button is not None

    def test_init_minimal(self, qt_app):
        """Widget creates with just title (no icon, description, CTA)."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Minimal")
        assert w is not None
        assert w._description_label is None
        assert w._cta_button is None

    def test_cta_clicked_signal(self, qt_app):
        """Clicking CTA button emits cta_clicked signal."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test", cta_text="Do it")
        received = []
        w.cta_clicked.connect(lambda: received.append(True))
        w._cta_button.click()
        assert received == [True]

    def test_fade_out_no_signal_accumulation(self, qt_app):
        """Repeated fade_out() calls do NOT accumulate finished connections.

        This is the P1 fix from the review: only one _on_fade_finished
        connection is made in __init__, not per-call.
        """
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test")
        # Call fade_out multiple times
        for _ in range(10):
            w.fade_out(hide_on_finish=True)
            w._fade_anim.stop()

        # Count connections on the finished signal by checking receiver count
        # Qt's meta-system: if connections accumulated, hiding would be called
        # multiple times.  We verify the animation object has exactly one
        # connection to _on_fade_finished.
        count = w._fade_anim.receivers(w._fade_anim.finished)
        assert count == 1, (
            f"Expected 1 connection to _on_fade_finished, got {count}. "
            "Memory leak: fade_out() is accumulating signal connections."
        )

    def test_fade_in_shows_widget(self, qt_app):
        """fade_in() makes widget visible."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test")
        w.hide()
        assert not w.isVisible()
        w.fade_in()
        assert w.isVisible()

    def test_drag_drop_emits_files_dropped(self, qt_app):
        """Dropping files emits files_dropped with the local paths."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test", accept_drops=True)
        received_paths = []
        w.files_dropped.connect(received_paths.extend)

        # Simulate a drop event with two file URLs
        mime = QtCore.QMimeData()
        mime.setUrls([
            QtCore.QUrl.fromLocalFile("/tmp/a.mp3"),
            QtCore.QUrl.fromLocalFile("/tmp/b.flac"),
        ])
        event = QtGui.QDropEvent(
            QtCore.QPointF(0, 0),
            QtCore.Qt.DropAction.CopyAction,
            mime,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )
        w.dropEvent(event)

        assert "/tmp/a.mp3" in received_paths
        assert "/tmp/b.flac" in received_paths

    def test_responsive_hides_description(self, qt_app):
        """At width < COMPACT_WIDTH, description label is hidden."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test", description="Desc")
        w.show()
        # Force a narrow resize
        w.resize(100, 300)
        # Manually trigger the resize logic
        w.resizeEvent(None)
        assert not w._description_label.isVisible()

    def test_responsive_shows_description_wide(self, qt_app):
        """At width >= COMPACT_WIDTH, description label is visible."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget("Test", description="Desc")
        w.show()
        w.resize(500, 300)
        w.resizeEvent(None)
        assert w._description_label.isVisible()

    def test_accessible_name_set(self, qt_app):
        """accessibleName() contains title, description, and cta_text."""
        from picard.ui.widgets.emptystate import EmptyStateWidget

        w = EmptyStateWidget(
            "My Title",
            description="My Description",
            cta_text="My CTA",
        )
        name = w.accessibleName()
        assert "My Title" in name
        assert "My Description" in name
        assert "My CTA" in name


# ---------------------------------------------------------------------------
# TreeContainer tests
# ---------------------------------------------------------------------------

class TestTreeContainer:
    def _make_tree_widget(self, qt_app):
        """Return a plain QTreeWidget for testing."""
        return QtWidgets.QTreeWidget()

    def test_shows_empty_state_initially_no_content(self, qt_app):
        """With has_content_fn returning False, starts on index 0 (empty state)."""
        from picard.ui.widgets.emptystate import EmptyStateWidget
        from picard.ui.widgets.treecontainer import TreeContainer

        tree = self._make_tree_widget(qt_app)
        empty = EmptyStateWidget("Empty")
        container = TreeContainer(tree, empty, has_content_fn=lambda: False)

        # Trigger the deferred check
        container._do_check_state()
        assert container.currentIndex() == 0

    def test_switches_to_tree_on_content(self, qt_app):
        """When has_content_fn returns True, switches to tree view (index 1)."""
        from picard.ui.widgets.emptystate import EmptyStateWidget
        from picard.ui.widgets.treecontainer import TreeContainer

        tree = self._make_tree_widget(qt_app)
        empty = EmptyStateWidget("Empty")

        has_content = [False]
        container = TreeContainer(tree, empty, has_content_fn=lambda: has_content[0])

        # Start empty
        container._do_check_state()
        assert container.currentIndex() == 0

        # Add content
        has_content[0] = True
        container._do_check_state()
        assert container.currentIndex() == 1

    def test_returns_to_empty_on_clear(self, qt_app):
        """Removing all content switches back to empty state (index 0)."""
        from picard.ui.widgets.emptystate import EmptyStateWidget
        from picard.ui.widgets.treecontainer import TreeContainer

        tree = self._make_tree_widget(qt_app)
        empty = EmptyStateWidget("Empty")

        has_content = [True]
        container = TreeContainer(tree, empty, has_content_fn=lambda: has_content[0])

        # Should be at tree (index 1) initially due to constructor default
        assert container.currentIndex() == 1

        # Remove content → empty state
        has_content[0] = False
        container._do_check_state()
        assert container.currentIndex() == 0


