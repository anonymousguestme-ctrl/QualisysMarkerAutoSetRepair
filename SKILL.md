---
name: qualisys-cast-gap-repair
description: Diagnose, label, gap-fill, and validate Qualisys QTM files for the CAST lower-body marker set by mapping captured measured markers to verified anatomical/tracking labels before any explicitly requested gap repair. Use for marker identity errors, broken CAST lines, TH/SK plate swaps, missing dynamic markers, left/right color mismatches, or preparation for Visual3D. Do not invent absent markers, and do not use for unrelated marker sets without first adapting the definitions.
---

# Qualisys CAST Gap Repair

Produce a traceable QTM result whose labels, marker colors, bone topology, rigid-cluster geometry, and gap fills agree with the verified static trial. Treat a visually plausible point position as insufficient: the identity and connected line topology must also be correct.

## Before Acting

1. Confirm the exact file and whether the user means a displayed QTM frame or a zero-based API sample index. QTM's UI commonly displays API sample `n` as frame `n + 1`; verify this in the installed version before modifying data.
2. Before opening or editing QTM, inventory every candidate raw trial with its exact path, filename, size, modification time, and SHA-256 hash. Record the user-confirmed trial sequence; do not infer it from consecutive numbering.
3. Query `file/get_path` and `file/is_dirty`. Preserve a dirty in-memory measurement with `file/save_as` to a distinct backup before edits.
4. Never overwrite, rename, move, delete, or re-save the raw capture or the user-completed static trial. Work from a copy and write every result to a distinct, versioned output path. A request to clean generated files does not authorize deleting raw data.
5. Use the user's completed static measurement as ground truth. An AIM model or generic CAST diagram helps with topology, but it does not override the subject's verified point identities.
6. Separate diagnosis from mutation. Run read-only checks first and state the exact marker/range/reference set before filling or relabeling.

## Raw Capture Preservation

- Treat an unsuffixed capture file and any file matching the acquisition session's date/time as protected until its provenance is verified. Never classify files as disposable solely from their names or trial numbers.
- "Original" means the byte-for-byte raw capture or a hash-verified copy of it. Files named `identity_normalized`, `before_fragments`, `before_relational`, `corrected`, or similar are processing-stage copies, not raw originals. Describe them accurately.
- Use copy-on-write: copy the raw capture to a clearly named working file, perform all QTM writes there, and keep corrected or gap-filled results under explicit suffixes such as `_corrected_measured` or `_relational`.
- Before cleanup, compare the protected raw manifest against the files that will remain. Use an exact allowlist for deletion; never delete by a broad wildcard, a whole output tree, or assumed consecutive numbering. Do not empty the Recycle Bin as part of cleanup.
- Treat QTM project files and PAF configuration/dependency files, including `.qpr` and adjacent project metadata, as protected acquisition infrastructure. Do not rename, move, delete, regenerate, or replace them during marker cleanup. If the user explicitly requests their removal, first preserve a byte-identical backup and explain that deleting them can break the PAF/QTM project.
- If a raw trial is missing, stop further cleanup and search read-only backups, the Recycle Bin, and session folders. Restore only to a missing destination, abort if the target exists, and verify source/target SHA-256 hashes after copying.
- If the exact raw file cannot be found, preserve the earliest pre-edit copy but do not call it byte-identical original. Report its filename, timestamp, processing stage, and the resulting limitation.
- For the `2026-09-18/CAST - Lower body_esp32-ao-flexsensor4.5` session, the user-confirmed raw dynamic trial numbers are `1, 3, 4, 5, 6, 7`. This is session-specific and must not be generalized to other acquisitions.

## Route The Task

- For marker definitions, expected counts, side colors, and bones, read [references/marker-set.md](references/marker-set.md).
- For labeling, fragment repair, gaps, corruption, and validation, read [references/workflow.md](references/workflow.md).
- For QTM REST calls, frame numbering, and safe write patterns, read [references/qtm-api.md](references/qtm-api.md).
- Use [scripts/qtm_cast_tool.py](scripts/qtm_cast_tool.py) for reproducible template capture, audit, and targeted relational repair.

## Core Decision Rules

### Measured data has priority

- Start from the markers physically present in the capture and associate those trajectories with the verified static trial's anatomical/tracking labels. Label assignment does not authorize generating missing points.
- Treat valid `Measured` samples and trajectory parts as the primary evidence. Prefer them over relational, interpolated, pattern-filled, or otherwise synthetic samples whenever both are available for the same marker and frame.
- Never overwrite a correctly identified `Measured` sample merely to make a trajectory smoother, complete a 28-point frame, or reach 100 percent fill.
- A `Measured` sample can still carry the wrong marker identity. Replace or relabel it only after identity error is supported by trajectory continuity on both sides, verified static-cluster geometry, source-part boundaries, and QTM bone/line inspection. Preserve the original and report the exact replaced range.
- Prefer `Measured` references for relational filling. If a filled reference must be used in a dependent repair, validate it first, record its provenance, and re-audit after the dependent fill.

### Do not create markers by default

- Never create a marker object or coordinate merely because the CAST model expects that anatomical landmark. An expected but unmeasured landmark remains missing.
- Do not copy, mirror, offset, interpolate, extrapolate, or otherwise synthesize a point to make the marker count reach 36 static or 28 dynamic markers.
- A bone line connects two correctly identified existing marker labels; it is not evidence that a missing endpoint should be generated.
- Relational fill is an explicit gap-repair operation, not ordinary marker correspondence. Use it only when the user explicitly requests filling, the target is a previously observed physical marker with defensible anchors/references, and the result is reported as filled rather than measured.
- Never use relational fill to manufacture a physical marker that was never captured or where the complete reference cluster is absent.

### Identity before fill

- A gap is missing data. A marker that exists in the wrong location is an identity/corruption problem, not a gap.
- Do not fill through a wrong labeled sample. Remove, overwrite, or isolate the corrupt range first, then fill from reliable anchors.
- Do not swap all four labels because a single-frame distance permutation has a lower score. Confirm trajectory continuity, part boundaries, neighboring frames, and static geometry.
- On a nearly symmetric four-marker plate, multiple label permutations can have similar distance scores. Prefer the identity that is temporally continuous and agrees with verified frames on both sides.

### Relational fill

- Apply this section only after explicit authorization to fill gaps. For labeling/correspondence requests, stop after mapping existing measured trajectories and report missing landmarks.
- Prefer three reliable references from the same rigid cluster: `origin`, `line`, and `plane`.
- If two targets overlap in their missing/corrupt ranges, repair one target with two reliable references only when good endpoints exist on both sides; then use the restored target as the third reference for the other target.
- Repair reference markers before dependent targets. Re-audit after every pass.
- Fill internal ranges by default. Do not extrapolate leading or trailing gaps merely to reach 100 percent fill; crop them from the analysis interval when appropriate.
- QTM relational fill overwrites all samples in the requested range. This is useful for corrupted samples but raises the write risk: use a backup and a new output path.
- Before every relational write, enumerate existing `Measured` samples in the target range. Abort by default if correctly identified measured samples would be overwritten.

### Static and dynamic expectations

- Static CAST lower-body data may contain 36 markers because it includes anatomical/calibration markers.
- Dynamic data normally contains the 28 tracking markers listed in the marker-set reference.
- Visual3D needs consistent tracking-target names, not necessarily every anatomical static marker in dynamic trials.
- For a four-marker TH or SK plate, three non-collinear valid markers can define a six-degree-of-freedom pose; four markers provide redundancy. Do not infer that every frame must contain all four merely because 100 percent fill is aesthetically preferable.

## Required Validation

Before handing off a modified QTM file, verify all of the following:

1. Compare the observed label set with the expected CAST set. Report every missing or empty required label; never create a trajectory merely to make this check pass.
2. Static/dynamic label and bone counts match the selected CAST configuration.
3. Left and right colors match the verified static convention.
4. No overlapping parts claim the same label; report any remaining unidentified/discarded parts.
5. Per-frame labeled point histogram is reported. Distinguish internal gaps from boundary gaps.
6. Every filled frame has all required references available.
7. The result records sample provenance and confirms that no correctly identified `Measured` samples were replaced. Any intentionally replaced measured range has an identity-error justification.
8. Pairwise rigid-cluster distances are compared with the static template over the repaired range and its boundaries.
9. Position and velocity are continuous at both repair seams.
10. The target marker is visually inspected in QTM at the first bad frame, worst frame, and first good frame after the repair. Confirm the lines connect the intended physical plate.
11. Re-open the saved output and repeat the structural audit; do not rely only on in-memory state.

Marker completeness is an observed-data result, not a target to fabricate.

For rigid TH/SK plates, use RMS distance error as a screening signal, not an automatic identity oracle. As a local starting point, `<= 3 mm` is strong, `3-5 mm` merits visual review, and `> 5 mm` is suspicious. Adjust for marker movement and the static trial's own variability.

## Communication

Report the actual onset range and frame convention, wrong versus missing markers, measured-versus-filled provenance, relational dependency order, any intentionally replaced measured range, before/after errors, output and backup paths, and residual ambiguity. Do not describe a trial as fixed solely because it has 28 points in every frame. A complete but misidentified marker set is still invalid for biomechanical solving.
