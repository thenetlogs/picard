# test/test_workflowstep.py
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

from picard.ui.widgets.workflowstep import StepState, compute_workflow_states
import pytest


def cws(files, albums, pending, changed):
    """Shorthand wrapper for compute_workflow_states."""
    return compute_workflow_states(files, albums, pending, changed)


class TestComputeWorkflowStates:
    def test_empty_session(self):
        s = cws(0, 0, 0, 0)
        assert s[0] == StepState.ACTIVE    # Add Files — always prompt
        assert s[1] == StepState.INACTIVE  # Identify
        assert s[2] == StepState.INACTIVE  # Review
        assert s[3] == StepState.INACTIVE  # Save

    def test_files_added_no_albums(self):
        s = cws(3, 0, 0, 0)
        assert s[0] == StepState.COMPLETE  # files exist
        assert s[1] == StepState.ACTIVE    # no albums yet — prompt to identify
        assert s[2] == StepState.INACTIVE
        assert s[3] == StepState.INACTIVE

    def test_identify_in_progress(self):
        s = cws(3, 1, 5, 0)
        assert s[0] == StepState.COMPLETE
        assert s[1] == StepState.ACTIVE    # pending > 0
        assert s[2] == StepState.INACTIVE
        assert s[3] == StepState.INACTIVE

    def test_albums_loaded_with_changed_files(self):
        s = cws(5, 2, 0, 3)
        assert s[0] == StepState.COMPLETE
        assert s[1] == StepState.COMPLETE  # albums loaded, nothing pending
        assert s[2] == StepState.ACTIVE    # changed files present → review
        assert s[3] == StepState.ACTIVE    # changed files → prompt to save

    def test_all_saved(self):
        # albums exist, nothing pending, nothing changed
        s = cws(5, 2, 0, 0)
        assert s[0] == StepState.COMPLETE
        assert s[1] == StepState.COMPLETE
        assert s[2] == StepState.COMPLETE
        assert s[3] == StepState.COMPLETE

    def test_no_files_only_step1_active(self):
        s = cws(0, 0, 0, 0)
        assert s[0] == StepState.ACTIVE
        for i in range(1, 4):
            assert s[i] == StepState.INACTIVE
