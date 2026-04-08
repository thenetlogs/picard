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
)


def render_unicode_icon(symbol, color, size, device_pixel_ratio=1.0):
    """Render a Unicode symbol as a QIcon.

    Args:
        symbol: Single Unicode character to render.
        color: QColor for the symbol.
        size: Logical icon size in pixels.
        device_pixel_ratio: DPI scale factor (e.g. 2.0 for Retina).

    Returns:
        QIcon with the rendered symbol.
    """
    physical = int(size * device_pixel_ratio)
    pixmap = QtGui.QPixmap(physical, physical)
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)

    font = painter.font()
    font.setPixelSize(int(size * 0.75))
    painter.setFont(font)

    painter.setPen(color)
    painter.drawText(
        QtCore.QRectF(0, 0, size, size),
        QtCore.Qt.AlignmentFlag.AlignCenter,
        symbol,
    )
    painter.end()

    return QtGui.QIcon(pixmap)


def _init_icons():
    """Pre-render all Unicode status icons. Call after QApplication exists."""
    global FILE_ICONS, MATCH_ICONS, MATCH_PENDING_ICONS, ALBUM_ICONS

    FILE_ICONS = {
        "unmatched": render_unicode_icon("\u25C7", QtGui.QColor(200, 200, 200), 16),
        "pending": render_unicode_icon("\u27F3", QtGui.QColor(240, 192, 64), 16),
        "saved": render_unicode_icon("\u2714", QtGui.QColor(80, 200, 120), 16),
        "error": render_unicode_icon("\u26A0", QtGui.QColor(224, 80, 80), 16),
        "not_found": render_unicode_icon("\u2298", QtGui.QColor(224, 80, 80), 16),
    }

    _match_colors = [
        QtGui.QColor(224, 80, 80),
        QtGui.QColor(224, 128, 64),
        QtGui.QColor(192, 160, 64),
        QtGui.QColor(128, 176, 80),
        QtGui.QColor(80, 192, 96),
        QtGui.QColor(80, 200, 120),
    ]

    MATCH_ICONS = [
        render_unicode_icon("\u25C6", c, 16) for c in _match_colors
    ]
    MATCH_PENDING_ICONS = [
        render_unicode_icon("\u27F3", c, 16) for c in _match_colors
    ]

    ALBUM_ICONS = {
        "incomplete": render_unicode_icon("\u25CE", QtGui.QColor(200, 200, 200), 16),
        "complete_unsaved": render_unicode_icon("\u25C9", QtGui.QColor(77, 166, 255), 16),
        "complete_saved": render_unicode_icon("\u25C9", QtGui.QColor(80, 200, 120), 16),
        "error": render_unicode_icon("\u25C9", QtGui.QColor(224, 80, 80), 16),
    }


# Module-level placeholders (populated by _init_icons)
FILE_ICONS = {}
MATCH_ICONS = []
MATCH_PENDING_ICONS = []
ALBUM_ICONS = {}
