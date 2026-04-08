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

### Implementation

- New method `Tagger.identify(objects)` in `picard/tagger.py`:
  - For each file in objects: launch both lookup and scan
  - Track completion state per file (which lookups finished)
  - On each callback: check if both done, then pick winner (AcoustID priority)
- New action `_create_identify_action()` in `picard/ui/mainwindow/actions.py`
- New UI method `MainWindow.identify()` in `picard/ui/mainwindow/__init__.py`

### Edge Cases

- File already matched: re-identify should work (same as current re-lookup/re-scan behavior)
- AcoustID not configured (no API key / no fpcalc): fall back to metadata-only (same as just Lookup)
- Both return same album/track: no conflict, just use AcoustID result

## Files Changed

| File | Changes |
|------|---------|
| `picard/tagger.py` | New `identify()` method with parallel coordination |
| `picard/ui/mainwindow/actions.py` | New `_create_identify_action()` |
| `picard/ui/mainwindow/__init__.py` | New `identify()` UI method |
| `picard/ui/enums.py` | New `MainAction.IDENTIFY` |
| `test/test_identify.py` | Tests for identify coordination logic |

## Out of Scope

- Changing how Lookup or Scan work internally
- Auto-identify on file add (separate feature)
- Progress indicator for identify (use existing pending state)
