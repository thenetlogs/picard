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

import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from picard.ui.widgets.workflowstep import StepState, compute_workflow_states
import pytest
from PyQt6 import QtWidgets


@pytest.fixture(scope="module")
def qt_app():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv[:1])
    yield app


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

    def test_pending_no_albums(self):
        """Files present, pending requests but no albums yet (fingerprinting started)."""
        s = cws(3, 0, 2, 0)
        assert s[0] == StepState.COMPLETE
        assert s[1] == StepState.ACTIVE    # pending in progress
        assert s[2] == StepState.INACTIVE
        assert s[3] == StepState.INACTIVE


class TestWorkflowStepIndicator:
    def test_creates_four_bubbles(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator
        w = WorkflowStepIndicator()
        assert len(w._bubbles) == 4

    def test_creates_four_labels(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator
        w = WorkflowStepIndicator()
        assert len(w._labels) == 4

    def test_set_states_updates_bubble_property(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        w.set_states([StepState.COMPLETE, StepState.ACTIVE,
                      StepState.INACTIVE, StepState.INACTIVE])
        assert w._bubbles[0].property("state") == "complete"
        assert w._bubbles[1].property("state") == "active"
        assert w._bubbles[2].property("state") == "inactive"

    def test_complete_bubble_shows_checkmark(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        w.set_states([StepState.COMPLETE] + [StepState.INACTIVE] * 3)
        assert w._bubbles[0].text() == "✓"

    def test_active_bubble_shows_number(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        w.set_states([StepState.ACTIVE] + [StepState.INACTIVE] * 3)
        assert w._bubbles[0].text() == "1"

    def test_initial_state_is_first_step_active(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        assert w._bubbles[0].property("state") == "active"
        for i in range(1, 4):
            assert w._bubbles[i].property("state") == "inactive"

    def test_active_label_is_bold(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        w.set_states([StepState.INACTIVE, StepState.ACTIVE,
                      StepState.INACTIVE, StepState.INACTIVE])
        assert w._labels[1].font().bold()
        assert not w._labels[0].font().bold()

    def test_inactive_label_is_disabled(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        w.set_states([StepState.ACTIVE, StepState.INACTIVE,
                      StepState.INACTIVE, StepState.INACTIVE])
        assert not w._labels[1].isEnabled()
        assert w._labels[0].isEnabled()

    def test_set_states_wrong_length_raises(self, qt_app):
        from picard.ui.widgets.workflowstep import WorkflowStepIndicator, StepState
        w = WorkflowStepIndicator()
        with pytest.raises(ValueError, match="expected 4 states"):
            w.set_states([StepState.ACTIVE, StepState.INACTIVE])
