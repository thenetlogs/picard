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
