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


from PyQt6 import (
    QtCore,
    QtWidgets,
)


class TreeContainer(QtWidgets.QStackedWidget):
    """Wraps a QTreeWidget and an EmptyStateWidget in a QStackedWidget.

    Index 0 — EmptyStateWidget (shown when no content).
    Index 1 — the tree view (shown when content exists).

    Parameters
    ----------
    tree_view:
        The QTreeWidget to wrap.
    empty_state:
        An EmptyStateWidget to show when the tree is empty.
    has_content_fn:
        Callable[[], bool] — returns True when the tree has meaningful
        content.  Needed because FileTreeView always has 2 permanent
        top-level items (unmatched_files + clusters), so
        ``topLevelItemCount() > 0`` is always True.
    """

    def __init__(self, tree_view, empty_state, has_content_fn, parent=None):
        super().__init__(parent=parent)
        self._tree_view = tree_view
        self._empty_state = empty_state
        self._has_content_fn = has_content_fn

        self.addWidget(empty_state)  # index 0
        self.addWidget(tree_view)    # index 1

        # Show tree initially; the first signal will correct state
        self.setCurrentIndex(1)

    def check_state(self):
        """Schedule a state check deferred to the next event-loop tick.

        Using QTimer.singleShot(0) ensures the tree model is fully updated
        before we read topLevelItemCount() / childCount().
        """
        QtCore.QTimer.singleShot(0, self._do_check_state)

    def _do_check_state(self):
        has_items = self._has_content_fn()
        current = self.currentIndex()
        if has_items and current == 0:
            # Content appeared — fade out empty state, switch to tree
            self._empty_state.fade_out(hide_on_finish=False)
            self.setCurrentIndex(1)
        elif not has_items and current == 1:
            # Content gone — switch to empty state and fade in
            self.setCurrentIndex(0)
            self._empty_state.fade_in()
