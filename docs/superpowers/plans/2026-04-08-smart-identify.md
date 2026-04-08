# Smart Identify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "Identify" action that runs Lookup and Scan in parallel, picking the best result.

**Architecture:** Simple approach — `Tagger.identify()` calls both `autotag()` and `analyze()` on the selected objects. Both use existing `_lookup_finished()` callbacks. Picard already handles file re-assignment when a better match arrives (move_file_to_track). AcoustID typically takes longer, so metadata applies first and AcoustID overrides if it finds something. No custom coordination needed.

**Tech Stack:** PyQt6, pytest

**Spec:** `docs/superpowers/specs/2026-04-08-smart-identify-design.md`

**Simplification note:** The spec proposed IdentifyState coordination, but after code review, both Lookup and Scan use independent callbacks via `_lookup_finished()` which calls `tagger.move_file_to_track()`. Picard already handles moving files between tracks gracefully. Running both in parallel and letting results apply independently is simpler and equally correct — AcoustID result (arriving later) naturally overrides metadata result.

---

### Task 1: Tagger.identify() method — test + implementation

**Files:**
- Modify: `picard/tagger.py:1403-1406` (add identify after autotag)
- Create: `test/test_identify.py`

- [ ] **Step 1: Write failing tests**

Create `test/test_identify.py`:

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

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestTaggerIdentify:
    """Tests for Tagger.identify() method."""

    def _make_mock_tagger(self, use_acoustid=True):
        from picard.tagger import Tagger
        tagger = MagicMock(spec=Tagger)
        type(tagger).use_acoustid = PropertyMock(return_value=use_acoustid)
        tagger._acoustid = MagicMock()
        tagger.autotag = MagicMock()
        tagger.analyze = MagicMock()
        # Bind real identify method
        tagger.identify = Tagger.identify.__get__(tagger)
        return tagger

    def test_identify_calls_both_autotag_and_analyze(self):
        tagger = self._make_mock_tagger(use_acoustid=True)
        objs = [MagicMock()]
        tagger.identify(objs)
        tagger.autotag.assert_called_once_with(objs)
        tagger.analyze.assert_called_once_with(objs)

    def test_identify_without_acoustid_only_calls_autotag(self):
        tagger = self._make_mock_tagger(use_acoustid=False)
        objs = [MagicMock()]
        tagger.identify(objs)
        tagger.autotag.assert_called_once_with(objs)
        tagger.analyze.assert_not_called()

    def test_identify_passes_same_objects_to_both(self):
        tagger = self._make_mock_tagger(use_acoustid=True)
        objs = [MagicMock(), MagicMock()]
        tagger.identify(objs)
        assert tagger.autotag.call_args[0][0] is objs
        assert tagger.analyze.call_args[0][0] is objs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/picard && python3 -m pytest test/test_identify.py -v`
Expected: FAIL — `Tagger.identify` does not exist.

- [ ] **Step 3: Implement identify**

In `picard/tagger.py`, add after the `autotag` method (after line 1406):

```python
    def identify(self, objects):
        """Run Lookup and Scan in parallel for best identification.

        Both methods use existing _lookup_finished callbacks. Metadata
        lookup is typically faster; if AcoustID finds a better match
        later, it overrides via move_file_to_track.
        """
        self.autotag(objects)
        if self.use_acoustid:
            self.analyze(objects)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/picard && python3 -m pytest test/test_identify.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/tagger.py test/test_identify.py
git commit -m "ux(#05): add Tagger.identify() — parallel Lookup + Scan"
```

---

### Task 2: UI action and enum

**Files:**
- Modify: `picard/ui/enums.py:67` (add IDENTIFY after AUTOTAG)
- Modify: `picard/ui/mainwindow/actions.py:507` (add _create_identify_action)
- Modify: `picard/ui/mainwindow/__init__.py:1960` (add identify method)

- [ ] **Step 1: Add IDENTIFY to MainAction enum**

In `picard/ui/enums.py`, add after line 67 (`AUTOTAG = 'autotag_action'`):

```python
    IDENTIFY = 'identify_action'
```

- [ ] **Step 2: Add identify action**

In `picard/ui/mainwindow/actions.py`, add after the `_create_autotag_action` function (after line 507):

```python
@add_action(MainAction.IDENTIFY)
def _create_identify_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-auto-tag'), _("&Identify"), parent)
    action.setStatusTip(
        _("Identify files using both metadata lookup and audio fingerprinting")
    )
    action.setToolTip(
        _(
            "<b>Identify</b> &nbsp; <i>Ctrl+I</i><br><br>"
            "Runs both Lookup (metadata) and Scan (fingerprint) in "
            "parallel and picks the best result. Use this when you're "
            "not sure which method will work better."
        )
    )
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+I")))
    action.triggered.connect(parent.identify)
    return action
```

- [ ] **Step 3: Add identify UI method**

In `picard/ui/mainwindow/__init__.py`, add after the `autotag` method (after line 1960):

```python
    def identify(self):
        self.tagger.identify(self.selected_objects)
```

- [ ] **Step 4: Run tests**

Run: `cd ~/picard && python3 -m pytest test/test_identify.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/picard
git add picard/ui/enums.py picard/ui/mainwindow/actions.py picard/ui/mainwindow/__init__.py
git commit -m "ux(#05): add Identify action, enum, and UI method (Ctrl+I)"
```

---

### Task 3: Build, deploy Docker, verify

**Files:**
- No code changes — verification only

- [ ] **Step 1: Run full test suite**

Run: `cd ~/picard && python3 -m pytest test/test_identify.py test/test_drop_zones.py test/test_emptystate.py test/test_workflowstep.py -v`
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

- [ ] **Step 4: Visual verification**

Open http://192.168.4.101:5800 and verify:

1. **Identify button** visible in toolbar (uses same icon as Lookup for now)
2. **Ctrl+I** shortcut works
3. Select files, click Identify — files go to Pending, then match to albums
4. **Lookup** (Ctrl+L) and **Scan** (Ctrl+Y) still work independently

- [ ] **Step 5: Push to GitHub**

```bash
cd ~/picard && git push origin master
```
