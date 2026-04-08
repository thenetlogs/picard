# Status Icons Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PNG status icons with Unicode symbols rendered via QPainter for clarity and scalability.

**Architecture:** New `render_unicode_icon()` helper in `picard/ui/iconrender.py` creates QIcon from Unicode symbol + color. All icons pre-rendered in `MainPanel.create_icons()` (no per-frame rendering). File and album icon references updated to use new icons.

**Tech Stack:** PyQt6 (QPainter, QPixmap, QFont, QIcon), pytest

**Spec:** `docs/superpowers/specs/2026-04-08-status-icons-redesign-design.md`

---

### Task 1: Icon rendering helper — test + implementation

**Files:**
- Create: `picard/ui/iconrender.py`
- Create: `test/test_iconrender.py`

- [ ] **Step 1: Write failing tests**

Create `test/test_iconrender.py`:

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


class TestRenderUnicodeIcon:
    """Tests for render_unicode_icon helper."""

    def test_returns_qicon(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("✔", QtGui.QColor(80, 200, 120), 16)
        assert isinstance(icon, QtGui.QIcon)
        assert not icon.isNull()

    def test_pixmap_size_matches(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("◆", QtGui.QColor(255, 0, 0), 16)
        pixmap = icon.pixmap(16, 16)
        assert pixmap.width() == 16
        assert pixmap.height() == 16

    def test_different_colors_produce_different_icons(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon_red = render_unicode_icon("◆", QtGui.QColor(224, 80, 80), 16)
        icon_green = render_unicode_icon("◆", QtGui.QColor(80, 200, 120), 16)
        px_red = icon_red.pixmap(16, 16).toImage()
        px_green = icon_green.pixmap(16, 16).toImage()
        assert px_red != px_green

    def test_different_symbols_produce_different_icons(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon_a = render_unicode_icon("◇", QtGui.QColor(200, 200, 200), 16)
        icon_b = render_unicode_icon("✔", QtGui.QColor(200, 200, 200), 16)
        px_a = icon_a.pixmap(16, 16).toImage()
        px_b = icon_b.pixmap(16, 16).toImage()
        assert px_a != px_b

    def test_high_dpi_pixmap(self, qt_app):
        from picard.ui.iconrender import render_unicode_icon
        icon = render_unicode_icon("✔", QtGui.QColor(80, 200, 120), 16, device_pixel_ratio=2.0)
        # availableSizes returns physical sizes
        sizes = icon.availableSizes()
        assert len(sizes) > 0
        # Physical size should be 32x32 for 2x DPI
        assert sizes[0].width() == 32
        assert sizes[0].height() == 32

    def test_all_spec_symbols_render(self, qt_app):
        """All symbols from the spec should produce non-null icons."""
        from picard.ui.iconrender import render_unicode_icon
        symbols = ["◇", "⟳", "◆", "✔", "⚠", "⊘", "◎", "◉"]
        color = QtGui.QColor(200, 200, 200)
        for sym in symbols:
            icon = render_unicode_icon(sym, color, 16)
            assert not icon.isNull(), f"Symbol {sym} produced null icon"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python3 -m pytest test/test_iconrender.py -v`
Expected: FAIL — `picard.ui.iconrender` does not exist.

- [ ] **Step 3: Implement render_unicode_icon**

Create `picard/ui/iconrender.py`:

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python3 -m pytest test/test_iconrender.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/ui/iconrender.py test/test_iconrender.py
git commit -m "ux(#06): add render_unicode_icon helper + tests"
```

---

### Task 2: Replace file status icons

**Files:**
- Modify: `picard/ui/itemviews/__init__.py:269-300` (create_icons — FileItem icons)
- Modify: `picard/ui/itemviews/__init__.py:758-791` (decide_file_icon_info)
- Modify: `test/test_iconrender.py`

- [ ] **Step 1: Write failing tests for file icon mapping**

Add to `test/test_iconrender.py`:

```python
class TestFileStatusIcons:
    """Tests that file status icons use correct Unicode symbols and colors."""

    def test_file_icon_unmatched(self, qt_app):
        from picard.ui.iconrender import FILE_ICONS
        icon = FILE_ICONS["unmatched"]
        assert not icon.isNull()

    def test_file_icon_pending(self, qt_app):
        from picard.ui.iconrender import FILE_ICONS
        icon = FILE_ICONS["pending"]
        assert not icon.isNull()

    def test_file_icon_saved(self, qt_app):
        from picard.ui.iconrender import FILE_ICONS
        icon = FILE_ICONS["saved"]
        assert not icon.isNull()

    def test_file_icon_error(self, qt_app):
        from picard.ui.iconrender import FILE_ICONS
        icon = FILE_ICONS["error"]
        assert not icon.isNull()

    def test_file_icon_not_found(self, qt_app):
        from picard.ui.iconrender import FILE_ICONS
        icon = FILE_ICONS["not_found"]
        assert not icon.isNull()

    def test_match_icons_have_6_levels(self, qt_app):
        from picard.ui.iconrender import MATCH_ICONS
        assert len(MATCH_ICONS) == 6

    def test_match_pending_icons_have_6_levels(self, qt_app):
        from picard.ui.iconrender import MATCH_PENDING_ICONS
        assert len(MATCH_PENDING_ICONS) == 6

    def test_match_icons_colors_differ(self, qt_app):
        from picard.ui.iconrender import MATCH_ICONS
        px_first = MATCH_ICONS[0].pixmap(16, 16).toImage()
        px_last = MATCH_ICONS[5].pixmap(16, 16).toImage()
        assert px_first != px_last
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python3 -m pytest test/test_iconrender.py::TestFileStatusIcons -v`
Expected: FAIL — `FILE_ICONS` does not exist.

- [ ] **Step 3: Add icon constants to iconrender.py**

Add to `picard/ui/iconrender.py` (after `render_unicode_icon` function):

```python
from PyQt6 import QtWidgets


def _init_icons():
    """Pre-render all Unicode status icons. Call after QApplication exists."""
    global FILE_ICONS, MATCH_ICONS, MATCH_PENDING_ICONS, ALBUM_ICONS

    # File status icons
    FILE_ICONS = {
        "unmatched": render_unicode_icon("◇", QtGui.QColor(200, 200, 200), 16),
        "pending": render_unicode_icon("⟳", QtGui.QColor(240, 192, 64), 16),
        "saved": render_unicode_icon("✔", QtGui.QColor(80, 200, 120), 16),
        "error": render_unicode_icon("⚠", QtGui.QColor(224, 80, 80), 16),
        "not_found": render_unicode_icon("⊘", QtGui.QColor(224, 80, 80), 16),
    }

    # Match quality gradient colors (50% → 100%)
    _match_colors = [
        QtGui.QColor(224, 80, 80),    # 50% - red
        QtGui.QColor(224, 128, 64),   # 60% - orange
        QtGui.QColor(192, 160, 64),   # 70% - yellow
        QtGui.QColor(128, 176, 80),   # 80% - yellow-green
        QtGui.QColor(80, 192, 96),    # 90% - green
        QtGui.QColor(80, 200, 120),   # 100% - bright green
    ]

    MATCH_ICONS = [
        render_unicode_icon("◆", c, 16) for c in _match_colors
    ]
    MATCH_PENDING_ICONS = [
        render_unicode_icon("⟳", c, 16) for c in _match_colors
    ]

    # Album status icons
    ALBUM_ICONS = {
        "incomplete": render_unicode_icon("◎", QtGui.QColor(200, 200, 200), 16),
        "complete_unsaved": render_unicode_icon("◉", QtGui.QColor(77, 166, 255), 16),
        "complete_saved": render_unicode_icon("◉", QtGui.QColor(80, 200, 120), 16),
        "error": render_unicode_icon("◉", QtGui.QColor(224, 80, 80), 16),
    }


# Module-level placeholders (populated by _init_icons)
FILE_ICONS = {}
MATCH_ICONS = []
MATCH_PENDING_ICONS = []
ALBUM_ICONS = {}
```

- [ ] **Step 4: Update create_icons to use new icons**

In `picard/ui/itemviews/__init__.py`, add import at top:

```python
from picard.ui.iconrender import (
    _init_icons,
    FILE_ICONS,
    MATCH_ICONS,
    MATCH_PENDING_ICONS,
    ALBUM_ICONS,
)
```

Replace lines 260-300 in `create_icons()`:

```python
        # Initialize Unicode status icons
        _init_icons()

        AlbumItem.icon_cd = ALBUM_ICONS["incomplete"]
        AlbumItem.icon_cd_modified = ALBUM_ICONS["complete_unsaved"]
        AlbumItem.icon_cd_saved = ALBUM_ICONS["complete_saved"]
        AlbumItem.icon_cd_saved_modified = ALBUM_ICONS["complete_saved"]
        AlbumItem.icon_error = ALBUM_ICONS["error"]
        TrackItem.icon_audio = QtGui.QIcon(":/images/track-audio.png")
        TrackItem.icon_video = QtGui.QIcon(":/images/track-video.png")
        TrackItem.icon_data = QtGui.QIcon(":/images/track-data.png")
        TrackItem.icon_error = FILE_ICONS["error"]
        FileItem.icon_file = FILE_ICONS["unmatched"]
        FileItem.icon_file_pending = FILE_ICONS["pending"]
        FileItem.icon_error = FILE_ICONS["error"]
        FileItem.icon_error_not_found = FILE_ICONS["not_found"]
        FileItem.icon_error_no_access = FILE_ICONS["not_found"]
        FileItem.icon_saved = FILE_ICONS["saved"]
        FileItem.icon_fingerprint = icontheme.lookup('fingerprint', icontheme.ICON_SIZE_MENU)
        FileItem.icon_fingerprint_gray = icontheme.lookup('fingerprint-gray', icontheme.ICON_SIZE_MENU)
        FileItem.match_icons = MATCH_ICONS
        FileItem.match_icons_info = [
            N_("Bad match"),
            N_("Poor match"),
            N_("Ok match"),
            N_("Good match"),
            N_("Great match"),
            N_("Excellent match"),
        ]
        FileItem.match_pending_icons = MATCH_PENDING_ICONS
```

Note: `decide_file_icon_info()` and `AlbumItem.update()` do NOT need changes — they reference the same class attributes (`FileItem.icon_file`, `AlbumItem.icon_cd`, etc.) which now point to Unicode icons.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/picard && python3 -m pytest test/test_iconrender.py -v`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/picard
git add picard/ui/iconrender.py picard/ui/itemviews/__init__.py test/test_iconrender.py
git commit -m "ux(#06): replace file and album PNG icons with Unicode symbols"
```

---

### Task 3: Build, deploy Docker, verify visually

**Files:**
- No code changes — verification only

- [ ] **Step 1: Run full test suite**

Run: `cd ~/picard && python3 -m pytest test/test_iconrender.py test/test_drop_zones.py test/test_emptystate.py test/test_workflowstep.py -v`
Expected: All tests PASS.

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

1. **Unmatched files:** ◇ symbol (gray) in status column
2. **Pending files:** ⟳ symbol (yellow) when lookup/scan running
3. **Matched files:** ◆ symbol with color gradient (red→green based on match quality)
4. **Saved files:** ✔ symbol (green) after saving
5. **Error files:** ⚠ symbol (red) on errors
6. **Albums incomplete:** ◎ symbol (gray)
7. **Albums complete unsaved:** ◉ symbol (blue)
8. **Albums complete saved:** ◉ symbol (green)
9. **Track type icons:** Still PNG (audio/video/data) — unchanged
10. **Fingerprint icons:** Still PNG — unchanged

- [ ] **Step 5: Push to GitHub**

```bash
cd ~/picard && git push origin master
```
