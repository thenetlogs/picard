# UX #5: Smart Identify

## Summary

Add a new "Identify" action that runs Lookup (metadata search) and Scan (AcoustID fingerprint) in parallel, taking the best result. AcoustID has priority; metadata result is used as fallback.

## Current State

- **Lookup** (Ctrl+L): searches MusicBrainz by existing metadata tags. Fast but requires decent tags.
- **Scan** (Ctrl+Y): calculates audio fingerprint via fpcalc, queries AcoustID API. Slower but works with no tags.
- Users must manually decide which to use and run them separately.

## Design

### Behavior

1. User selects files/clusters, clicks "Identify" (or Ctrl+I)
2. Both `lookup_metadata()` and `acoustid.analyze()` start in parallel
3. When both complete:
   - If AcoustID returned a result: use it (fingerprint is more reliable)
   - If AcoustID failed/no result but metadata found something: use metadata result
   - If neither found anything: file stays unmatched
4. If only one completes and the other errors out: use the successful one

### Toolbar/Menu

- New toolbar button "Identify" with icon `picard-identify`
- Keyboard shortcut: `Ctrl+I`
- Existing Lookup (Ctrl+L) and Scan (Ctrl+Y) remain unchanged for advanced users
- New `MainAction.IDENTIFY` enum value

### Parallel Coordination

Both `lookup_metadata()` and `acoustid.analyze()` are async and callback-driven. Running them in parallel requires coordination to avoid race conditions:

**Pending state management:**
- Both operations call `file.set_pending()` / `file.clear_pending()` independently
- Problem: first callback clears pending while second still running
- Solution: new `IdentifyState` tracker per file (not modifying File class):
  - `Tagger._identify_states: dict[str, IdentifyState]` keyed by file path
  - `IdentifyState` tracks: metadata_done, acoustid_done, metadata_result, acoustid_result
  - Custom callbacks wrap `_lookup_finished` — store result but don't apply it yet
  - When both done: pick winner (AcoustID priority), apply once, then clear pending

**Result conflict resolution:**
- Neither callback applies results directly — they store results in IdentifyState
- After both complete, `_identify_resolve(file)` picks AcoustID result if available, else metadata
- The winning result is applied via the standard `_lookup_finished` path (single application, no double-move)
- If both fail: clear pending, file stays unmatched

**Fallback when AcoustID not configured:**
- If `self.use_acoustid` is False: skip IdentifyState machinery, just call `lookup_metadata()` directly (same as Lookup action)

### Toolbar/Button Enablement

- Identify action enabled when: `can_autotag OR can_analyze` (most permissive — at least one operation can run)
- This matches the "smart" philosophy: it does whatever it can

### Implementation

- New `IdentifyState` dataclass in `picard/tagger.py` (metadata_done, acoustid_done, results)
- New method `Tagger.identify(objects)`:
  - For each file: create IdentifyState, launch both with custom callbacks
  - If AcoustID not configured: fall back to plain lookup_metadata()
- New `Tagger._identify_metadata_done(file, state, ...)` and `_identify_acoustid_done(file, state, ...)` callbacks
- New `Tagger._identify_resolve(file, state)` — picks winner, applies result
- New action `_create_identify_action()` in `picard/ui/mainwindow/actions.py`
- New UI method `MainWindow.identify()` in `picard/ui/mainwindow/__init__.py`

### Edge Cases

- File already matched: re-identify should work (same as current re-lookup/re-scan behavior)
- AcoustID not configured (no API key / no fpcalc): fall back to metadata-only (same as just Lookup)
- Both return same album/track: no conflict, just use AcoustID result
- Metadata completes first: result stored, not applied until AcoustID also completes
- AcoustID errors out: metadata result used as fallback
- Both error out: file stays unmatched, pending state cleared

## Files Changed

| File | Changes |
|------|---------|
| `picard/tagger.py` | New `IdentifyState`, `identify()`, `_identify_metadata_done()`, `_identify_acoustid_done()`, `_identify_resolve()` |
| `picard/ui/mainwindow/actions.py` | New `_create_identify_action()` |
| `picard/ui/mainwindow/__init__.py` | New `identify()` UI method |
| `picard/ui/enums.py` | New `MainAction.IDENTIFY` |
| `test/test_identify.py` | Tests for identify coordination logic |

## Out of Scope

- Changing how Lookup or Scan work internally
- Auto-identify on file add (separate feature)
- Progress indicator for identify (use existing pending state)
