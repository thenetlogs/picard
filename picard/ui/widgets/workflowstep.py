# picard/ui/widgets/workflowstep.py
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

from enum import Enum


class StepState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETE = "complete"


def compute_workflow_states(
    file_count: int,
    album_count: int,
    pending_count: int,
    changed_count: int,
) -> list[StepState]:
    """Derive 4-step workflow states from current tagger statistics.

    Pure function — takes plain integers so it is unit-testable without Qt.
    Returns a list of four StepState values:
      [Add Files, Identify, Review, Save]
    """
    # Step 1: Add Files
    step1 = StepState.COMPLETE if file_count > 0 else StepState.ACTIVE

    # Step 2: Identify
    if file_count == 0:
        step2 = StepState.INACTIVE
    elif pending_count > 0:
        step2 = StepState.ACTIVE   # lookup/fingerprint in progress
    elif album_count > 0:
        step2 = StepState.COMPLETE
    else:
        step2 = StepState.ACTIVE   # files present but none identified yet

    # Step 3: Review
    if album_count == 0 or pending_count > 0:
        step3 = StepState.INACTIVE
    elif changed_count > 0:
        step3 = StepState.ACTIVE
    else:
        step3 = StepState.COMPLETE

    # Step 4: Save
    if changed_count > 0:
        step4 = StepState.ACTIVE
    elif album_count > 0 and pending_count == 0:
        step4 = StepState.COMPLETE
    else:
        step4 = StepState.INACTIVE

    return [step1, step2, step3, step4]


# ============================================================================
# Qt widget section: imported only when widget is instantiated
# ============================================================================

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import (
    N_,
    gettext as _,
)


# Step definitions: (number_string, translatable_label)
_STEP_DEFS = [
    ("1", N_("Add Files")),
    ("2", N_("Identify")),
    ("3", N_("Review")),
    ("4", N_("Save")),
]

_STYLESHEET = """\
WorkflowStepIndicator {
    background-color: palette(window);
    border-bottom: 1px solid palette(mid);
}
QLabel[state="active"] {
    background-color: palette(highlight);
    color: palette(highlighted-text);
    border-radius: 10px;
}
QLabel[state="complete"] {
    background-color: #4a9f57;
    color: white;
    border-radius: 10px;
}
QLabel[state="inactive"] {
    background-color: palette(button);
    color: palette(button-text);
    border-radius: 10px;
}
"""


class WorkflowStepIndicator(QtWidgets.QWidget):
    """Horizontal 4-step workflow indicator: Add Files → Identify → Review → Save."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bubbles: list[QtWidgets.QLabel] = []
        self._labels: list[QtWidgets.QLabel] = []
        self._setup_ui()
        initial = [StepState.ACTIVE] + [StepState.INACTIVE] * 3
        self.set_states(initial)

    def _setup_ui(self) -> None:
        self.setStyleSheet(_STYLESHEET)
        self.setFixedHeight(36)

        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(12, 0, 12, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        for i, (number, title) in enumerate(_STEP_DEFS):
            bubble = QtWidgets.QLabel(number)
            bubble.setFixedSize(20, 20)
            bubble.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            label = QtWidgets.QLabel(_(title))

            step_box = QtWidgets.QHBoxLayout()
            step_box.setSpacing(5)
            step_box.setContentsMargins(0, 0, 0, 0)
            step_box.addWidget(bubble)
            step_box.addWidget(label)

            outer.addLayout(step_box)
            self._bubbles.append(bubble)
            self._labels.append(label)

            if i < len(_STEP_DEFS) - 1:
                sep = QtWidgets.QLabel("  ▸  ")
                outer.addWidget(sep)

        outer.addStretch(1)

    def set_states(self, states: list[StepState]) -> None:
        """Apply a list of 4 StepState values to the indicator bubbles and labels."""
        for i, (bubble, label, state) in enumerate(
            zip(self._bubbles, self._labels, states)
        ):
            bubble.setProperty("state", state.value)
            bubble.style().unpolish(bubble)
            bubble.style().polish(bubble)

            bubble.setText("✓" if state == StepState.COMPLETE else str(i + 1))

            font = label.font()
            font.setBold(state == StepState.ACTIVE)
            label.setFont(font)
            label.setEnabled(state != StepState.INACTIVE)
