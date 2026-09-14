# QTM Scripting Notes

The local REST endpoint is normally:

```text
http://127.0.0.1:7979/api/scripting/qtm
```

POST a JSON array of positional arguments with `Content-Type: application/json`.

## Read-only methods

- `file/get_path`, `file/is_dirty`, `file/is_open`
- `gui/timeline/get_measured_range`, `gui/timeline/get_current_frame`
- `data/object/trajectory/get_trajectory_ids`, `find_trajectory`
- `data/object/trajectory/get_label`, `get_color`, `get_parts`
- `data/series/_3d/get_sample`, `get_samples`, `get_gap_ranges`
- `data/object/bone/get_bone_ids`

## Mutation methods

- `file/save_as`, `file/save`
- `data/object/trajectory/split_part`
- `data/object/trajectory/move_parts`, `swap_parts`, `delete_parts`
- `data/object/trajectory/fill_trajectory`
- `data/series/_3d/delete_samples`, `set_sample`, `set_samples`
- `data/object/bone/clear_bones`, `add_bone`

## Relational fill

Example arguments:

```json
[
  1234,
  "relational",
  {"start": 492, "end": 522},
  {"origin": 1235, "line": 1236, "plane": 1237}
]
```

Two-reference fallback omits `plane`. The range is inclusive and all samples inside it are overwritten, including existing measured samples.

## Part and frame semantics

`split_part(id, sample_index)` makes `sample_index` the last sample before the split. To isolate API samples 492-499, split after 491. Part indices change after edits; re-fetch them before each mutation.

The API uses zero-based sample indices while the visible QTM frame can be one-based. Verify this locally and report both conventions.

## Safe writes

Query path and dirty state first. Save a dirty state to a distinct backup, modify only confirmed ranges, save to a new versioned result, re-open it, and repeat read-only validation. Avoid deleting evidence when it can be moved to a preserved unidentified trajectory.

## Tool examples

Run commands from the skill directory or use the script's absolute path.

Capture a template while the completed static trial is open:

```powershell
py scripts/qtm_cast_tool.py capture-template --output C:\work\cast-static-template.json
```

Audit the open dynamic trial without changing it:

```powershell
py scripts/qtm_cast_tool.py audit --template C:\work\cast-static-template.json --include-permutations
```

Preview a repair plan for visible QTM frames 493-523. The default `--frame-base 1` converts them to API samples 492-522:

```powershell
py scripts/qtm_cast_tool.py repair --target R_TH1 --start 493 --end 523 --references R_TH2 R_TH3 R_TH4
```

Execute only after reviewing the plan. Both paths must not already exist:

```powershell
py scripts/qtm_cast_tool.py repair --target R_TH1 --start 493 --end 523 --references R_TH2 R_TH3 R_TH4 --backup C:\work\trial-before-rth1.qtm --output C:\work\trial-rth1-fixed.qtm --execute
```

For two overlapping corrupt targets, use separate versioned passes. First repair one marker from the two reliable references, reopen/audit that output, then repair the dependent marker with three references. Do not attempt both writes simultaneously because the second repair must be validated against the first.
