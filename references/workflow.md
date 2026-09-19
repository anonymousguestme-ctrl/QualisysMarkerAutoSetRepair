# CAST QTM Repair Workflow

## Protect the acquisition first

Before QTM is opened for editing, build a read-only manifest of the acquisition files containing exact paths, filenames, sizes, modification times, and SHA-256 hashes. Ask the user to confirm non-consecutive trial numbering when it is ambiguous. For the `2026-09-18/CAST - Lower body_esp32-ao-flexsensor4.5` session, the confirmed dynamic raw sequence is `1, 3, 4, 5, 6, 7`.

Never edit or re-save a raw capture in place. Make a working copy and save every labeled, corrected, or filled result under a distinct suffix. Do not use an unsuffixed raw filename for a processed result.

Cleanup is separate from marker repair. Reconcile the files that will remain against the raw manifest, protect exact raw/static/final paths, and remove only an explicit allowlist of generated artifacts. Do not delete a whole `Labeled_Output` tree without checking it for the only recoverable raw copy. Treat `.qpr`, PAF configuration/dependency files, calibration/project metadata, and their directory relationships as protected acquisition infrastructure; removing them can break the project even when `.qtm` files remain. Keep deletion recoverable and never empty the Recycle Bin as part of cleanup.

When recovering a missing trial, select candidates by acquisition session and timestamp before filename. Reject same-number trials from other dates. Copy only when the destination is absent, then compare source and destination hashes. A file such as `identity_normalized` may preserve measured trajectories but is not proof of a byte-identical raw capture; report that distinction explicitly.

## Establish ground truth

Open the user-completed static trial and capture exact labels, colors, median positions across stable frames, six pairwise distances for each cluster, and bone endpoints. Reject missing or visibly erroneous static frames. The completed static trial takes precedence over a generic AIM model.

## Inventory the dynamic trial

Collect each trajectory's ID, label, color, part ranges and types, sample/gap ranges, provenance, and discarded or unidentified state. Report labeled and total point counts per frame. A file can contain 28 label objects while fewer than 28 samples are valid.

When multiple candidates cover the same marker and frame, evaluate identity first and prefer correctly identified `Measured` data over validated fills and other synthetic data. Separate measured-and-mapped, measured-but-ambiguous, and expected-but-unmeasured outcomes. Never turn the last category into a generated trajectory.

## Diagnose identity

Use evidence in this order:

1. Continuity from a trusted previous frame.
2. Continuity into a trusted following frame.
3. Source trajectory boundaries and tracking jumps.
4. Six-distance match against the static cluster.
5. Stable assignment votes across a trajectory part.
6. Visual QTM inspection of marker and bone placement.

A large one-frame displacement in one marker while three plate partners remain continuous usually identifies the corrupted marker. If all four move smoothly but lines are wrong, suspect label permutation or bone topology.

Inspect per-marker displacement/acceleration, centroid motion, rigid RMS, best-versus-second-best permutation, permutation runs, and part boundaries. Do not accept a permutation when its score advantage is small.

## Repair fragments

When one source trajectory contains multiple physical identities, split at verified transition frames and move only the relevant part. Re-fetch part indices after every split or move. Reject overlaps. Preserve ambiguous evidence in an unidentified or discarded trajectory rather than deleting it when feasible. Rebuild or verify bones after replacing label objects.

## Repair gaps and corrupt samples

Enter gap repair only after explicit authorization. For one bad target with three reliable plate markers, use those markers as `origin`, `line`, and `plane`. Prefer references measured throughout the range, and require reliable target samples immediately before and after it.

For two overlapping bad targets, first rebuild one with the two reliable plate markers across trusted endpoints. Then use the restored target as the third reference for the other. Re-audit after both passes.

QTM relational fill can overwrite an explicit non-gap range. Inspect provenance first. Do not overwrite correctly identified measured data. Use it for corrupted measured samples only after preserving the original, proving the identity error, and recording the exact replaced range and reason.

Extend repairs to the true onset, not just where the artifact becomes obvious. In the demonstrated case, a problem reported at UI frame 497 began several samples earlier.

Do not extrapolate boundary gaps by default. Leave them missing or shorten the analysis range unless the user requests extrapolation and the downstream calculation needs those frames. Do not fill a marker with no trustworthy measured observations anchoring its identity.

## Validate and hand off

Check the repair plus at least 10 samples on both sides for position/velocity seams, rigid RMS, identity continuity, correct QTM bone connections, and measured-versus-filled provenance. Confirm that correctly identified measured samples, point counts, analog/force channels, frequencies, and measurement range are unchanged except for explicitly justified marker edits.

Save to a new file, re-open it, repeat the audit, and leave QTM at the user's reported frame.

For Visual3D, prioritize a complete static calibration, consistent dynamic tracking labels, at least three non-collinear valid tracking markers per rigid segment inside the analysis window, and no internal identity errors. Do not create artificial boundary data merely to claim 100 percent fill.
