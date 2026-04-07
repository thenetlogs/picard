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
    QtGui,
    QtWidgets,
)

from picard.util import icontheme


class EmptyStateWidget(QtWidgets.QWidget):
    """Reusable empty state widget with optional CTA button and drag-and-drop support.

    Signals:
        cta_clicked: emitted when the CTA button is clicked.
        files_dropped: emitted with a list of local file paths when files are
            dropped onto the widget (only when accept_drops=True).
    """

    cta_clicked = QtCore.pyqtSignal()
    files_dropped = QtCore.pyqtSignal(list)

    _COMPACT_WIDTH = 300  # px below which description is hidden

    def __init__(
        self,
        title,
        *,
        icon_name=None,
        description=None,
        cta_text=None,
        accept_drops=False,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setObjectName("EmptyStateWidget")
        self._accept_drops = accept_drops
        self._drag_hover = False

        self._build_ui(title, icon_name=icon_name, description=description, cta_text=cta_text)
        self._setup_animation()
        self._update_accessible_name(title, description, cta_text)

        if accept_drops:
            self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, title, *, icon_name, description, cta_text):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.addStretch(1)

        # Icon
        self._icon_label = QtWidgets.QLabel()
        self._icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        if icon_name:
            icon = icontheme.lookup(icon_name, icontheme.ICON_SIZE_TOOLBAR)
            if not icon.isNull():
                self._icon_label.setPixmap(icon.pixmap(48, 48))
        outer.addWidget(self._icon_label)

        # Title
        title_label = QtWidgets.QLabel(title)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        font = title_label.font()
        font.setPointSize(font.pointSize() + 1)
        title_label.setFont(font)
        title_label.setWordWrap(True)
        outer.addWidget(title_label)

        # Description (hidden in compact mode)
        self._description_label = None
        if description:
            self._description_label = QtWidgets.QLabel(description)
            self._description_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            self._description_label.setWordWrap(True)
            palette = self._description_label.palette()
            color = palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
            self._description_label.setStyleSheet(
                f"color: {color.name()};"
            )
            outer.addWidget(self._description_label)

        # CTA button
        self._cta_button = None
        if cta_text:
            self._cta_button = QtWidgets.QPushButton(cta_text)
            self._cta_button.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.addStretch(1)
            btn_layout.addWidget(self._cta_button)
            btn_layout.addStretch(1)
            outer.addLayout(btn_layout)
            self._cta_button.clicked.connect(self.cta_clicked)

        outer.addStretch(1)

        # Dashed drop-zone border via stylesheet
        self.setStyleSheet(
            "#EmptyStateWidget {"
            "  border: 2px dashed palette(mid);"
            "  border-radius: 6px;"
            "}"
            "#EmptyStateWidget[drag_hover=\"true\"] {"
            "  border-color: palette(highlight);"
            "  background-color: palette(highlight);"
            "}"
        )

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _setup_animation(self):
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QtCore.QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._should_hide_on_finish = False
        # Connect once — no repeated connections on repeated fade_out calls
        self._fade_anim.finished.connect(self._on_fade_finished)

    def fade_in(self):
        """Animate opacity from 0 → 1 and ensure the widget is visible."""
        self._fade_anim.stop()
        self._should_hide_on_finish = False
        self.show()
        self._opacity_effect.setOpacity(0.0)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def fade_out(self, *, hide_on_finish=True):
        """Animate opacity from 1 → 0, optionally hiding the widget after."""
        self._fade_anim.stop()
        self._should_hide_on_finish = hide_on_finish
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def _on_fade_finished(self):
        if self._should_hide_on_finish and self._opacity_effect.opacity() < 0.1:
            self.hide()

    # ------------------------------------------------------------------
    # Responsive layout
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._description_label is not None:
            compact = self.width() < self._COMPACT_WIDTH
            self._description_label.setVisible(not compact)

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if self._accept_drops and event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_hover(True)
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self._set_drag_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drag_hover(False)
        if self._accept_drops and event.mimeData().hasUrls():
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _set_drag_hover(self, state):
        self._drag_hover = state
        self.setProperty("drag_hover", "true" if state else "false")
        # Force Qt to re-evaluate the stylesheet with the new property value
        self.style().unpolish(self)
        self.style().polish(self)

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------

    def _update_accessible_name(self, title, description, cta_text):
        parts = [title]
        if description:
            parts.append(description)
        if cta_text:
            parts.append(cta_text)
        self.setAccessibleName(". ".join(parts))
