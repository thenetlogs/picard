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

from unittest.mock import MagicMock, PropertyMock

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
