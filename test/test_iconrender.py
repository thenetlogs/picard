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


class TestRenderUnicodeIcon:
    """Tests for render_unicode_icon helper."""

    def test_returns_qicon(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("\u2714", QtGui.QColor(80, 200, 120), 16)
        assert isinstance(icon, QtGui.QIcon)
        assert not icon.isNull()

    def test_pixmap_size_matches(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("\u25c6", QtGui.QColor(255, 0, 0), 16)
        pixmap = icon.pixmap(16, 16)
        assert pixmap.width() == 16
        assert pixmap.height() == 16

    def test_different_colors_produce_different_icons(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon_red = render_unicode_icon("\u25c6", QtGui.QColor(224, 80, 80), 16)
        icon_green = render_unicode_icon("\u25c6", QtGui.QColor(80, 200, 120), 16)
        px_red = icon_red.pixmap(16, 16).toImage()
        px_green = icon_green.pixmap(16, 16).toImage()
        assert px_red != px_green

    def test_different_symbols_produce_different_icons(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon_a = render_unicode_icon("\u25c7", QtGui.QColor(200, 200, 200), 16)
        icon_b = render_unicode_icon("\u2714", QtGui.QColor(200, 200, 200), 16)
        px_a = icon_a.pixmap(16, 16).toImage()
        px_b = icon_b.pixmap(16, 16).toImage()
        assert px_a != px_b

    def test_high_dpi_pixmap(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("\u2714", QtGui.QColor(80, 200, 120), 16, device_pixel_ratio=2.0)
        sizes = icon.availableSizes()
        assert len(sizes) > 0
        assert sizes[0].width() == 32
        assert sizes[0].height() == 32

    def test_all_spec_symbols_render(self, qt_app):
        """All symbols from the spec should produce non-null icons."""
        from picard.ui.iconrender import render_unicode_icon
        symbols = ["\u25c7", "\u27f3", "\u25c6", "\u2714", "\u26a0", "\u2298", "\u25ce", "\u25c9"]
        color = QtGui.QColor(200, 200, 200)
        for sym in symbols:
            icon = render_unicode_icon(sym, color, 16)
            assert not icon.isNull(), f"Symbol {sym} produced null icon"
