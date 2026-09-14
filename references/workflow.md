# CAST QTM Repair Workflow

## Establish ground truth

Open the user-completed static trial and capture exact labels, colors, median positions across stable frames, six pairwise distances for each cluster, and bone endpoints. Reject missing or visibly erroneous static frames. The completed static trial takes precedence over a generic AIM model.

## Inventory the dynamic trial

Collect each trajectory's ID, label, color, part ranges and types, sample/gap ranges, and discarded or unidentified state. Report labeled and total point counts per frame. A file can contain 28 label objects while fewer than 28 samples are valid.

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

For one bad target with three reliable plate markers, use those markers as `origin`, `line`, and `plane`. Require reliable target samples immediately before and after the repair range and references throughout it.

For two overlapping bad targets, first rebuild one with the two reliable plate markers across trusted endpoints. Then use the restored target as the third reference for the other. Re-audit after both passes.

QTM relational fill can overwrite an explicit non-gap range. Use this for corrupted samples only after preserving the original and recording that the measured samples were replaced.

Extend repairs to the true onset, not just where the artifact becomes obvious. In the demonstrated case, a problem reported at UI frame 497 began several samples earlier.

Do not extrapolate boundary gaps by default. Leave them missing or shorten the analysis range unless the user requests extrapolation and the downstream calculation needs those frames.

## Validate and hand off

Check the repair plus at least 10 samples on both sides for position/velocity seams, rigid RMS, identity continuity, and correct QTM bone connections. Confirm that point counts, analog/force channels, frequencies, and measurement range are unchanged except for intended marker samples.

Save to a new file, re-open it, repeat the audit, and leave QTM at the user's reported frame.

For Visual3D, prioritize a complete static calibration, consistent dynamic tracking labels, at least three non-collinear valid tracking markers per rigid segment inside the analysis window, and no internal identity errors. Do not create artificial boundary data merely to claim 100 percent fill.
