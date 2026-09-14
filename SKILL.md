---
name: qualisys-cast-gap-repair
description: Diagnose, label, gap-fill, and validate Qualisys QTM files for the CAST lower-body marker set using a user-verified static trial, rigid-cluster geometry, trajectory continuity, and relational filling. Use for QTM marker identity errors, broken CAST lines, TH/SK plate swaps, missing dynamic markers, left/right color mismatches, or preparation for Visual3D. Do not use for unrelated marker sets without first adapting the marker and bone definitions.
---

# Qualisys CAST Gap Repair

Produce a traceable QTM result whose labels, marker colors, bone topology, rigid-cluster geometry, and gap fills agree with the verified static trial. Treat a visually plausible point position as insufficient: the identity and connected line topology must also be correct.

## Before Acting

1. Confirm the exact file and whether the user means a displayed QTM frame or a zero-based API sample index. QTM's UI commonly displays API sample `n` as frame `n + 1`; verify this in the installed version before modifying data.
2. Query `file/get_path` and `file/is_dirty`. Preserve a dirty in-memory measurement with `file/save_as` to a distinct backup before edits.
3. Never overwrite the raw capture or the user-completed static trial. Write a versioned output unless the user explicitly asks to replace a file.
4. Use the user's completed static measurement as ground truth. An AIM model or generic CAST diagram helps with topology, but it does not override the subject's verified point identities.
5. Separate diagnosis from mutation. Run read-only checks first and state the exact marker/range/reference set before filling or relabeling.

## Route The Task

- For marker definitions, expected counts, side colors, and bones, read [references/marker-set.md](references/marker-set.md).
- For labeling, fragment repair, gaps, corruption, and validation, read [references/workflow.md](references/workflow.md).
- For QTM REST calls, frame numbering, and safe write patterns, read [references/qtm-api.md](references/qtm-api.md).
- Use [scripts/qtm_cast_tool.py](scripts/qtm_cast_tool.py) for reproducible template capture, audit, and targeted relational repair.

## Core Decision Rules

### Identity before fill

- A gap is missing data. A marker that exists in the wrong location is an identity/corruption problem, not a gap.
- Do not fill through a wrong labeled sample. Remove, overwrite, or isolate the corrupt range first, then fill from reliable anchors.
- Do not swap all four labels because a single-frame distance permutation has a lower score. Confirm trajectory continuity, part boundaries, neighboring frames, and static geometry.
- On a nearly symmetric four-marker plate, multiple label permutations can have similar distance scores. Prefer the identity that is temporally continuous and agrees with verified frames on both sides.

### Relational fill

- Prefer three reliable references from the same rigid cluster: `origin`, `line`, and `plane`.
- If two targets overlap in their missing/corrupt ranges, repair one target with two reliable references only when good endpoints exist on both sides; then use the restored target as the third reference for the other target.
- Repair reference markers before dependent targets. Re-audit after every pass.
- Fill internal ranges by default. Do not extrapolate leading or trailing gaps merely to reach 100 percent fill; crop them from the analysis interval when appropriate.
- QTM relational fill overwrites all samples in the requested range. This is useful for corrupted samples but raises the write risk: use a backup and a new output path.

### Static and dynamic expectations

- Static CAST lower-body data may contain 36 markers because it includes anatomical/calibration markers.
- Dynamic data normally contains the 28 tracking markers listed in the marker-set reference.
- Visual3D needs consistent tracking-target names, not necessarily every anatomical static marker in dynamic trials.
- For a four-marker TH or SK plate, three non-collinear valid markers can define a six-degree-of-freedom pose; four markers provide redundancy. Do not infer that every frame must contain all four merely because 100 percent fill is aesthetically preferable.

## Required Validation

Before handing off a modified QTM file, verify all of the following:

1. Expected label set exists and no required label is empty.
2. Static/dynamic label and bone counts match the selected CAST configuration.
3. Left and right colors match the verified static convention.
4. No overlapping parts claim the same label; report any remaining unidentified/discarded parts.
5. Per-frame labeled point histogram is reported. Distinguish internal gaps from boundary gaps.
6. Every filled frame has all required references available.
7. Pairwise rigid-cluster distances are compared with the static template over the repaired range and its boundaries.
8. Position and velocity are continuous at both repair seams.
9. The target marker is visually inspected in QTM at the first bad frame, worst frame, and first good frame after the repair. Confirm the lines connect the intended physical plate.
10. Re-open the saved output and repeat the structural audit; do not rely only on in-memory state.

For rigid TH/SK plates, use RMS distance error as a screening signal, not an automatic identity oracle. As a local starting point, `<= 3 mm` is strong, `3-5 mm` merits visual review, and `> 5 mm` is suspicious. Adjust for marker movement and the static trial's own variability.

## Communication

Report the actual onset range and frame convention, wrong versus missing markers, relational dependency order, before/after errors, output and backup paths, and residual ambiguity. Do not describe a trial as fixed solely because it has 28 points in every frame. A complete but misidentified marker set is still invalid for biomechanical solving.
