# CAST Lower-Body Marker Set

## Dynamic tracking set: 28 markers

| Region | Markers | Structure |
|---|---|---|
| Pelvis | `L_IAS`, `L_IPS`, `R_IPS`, `R_IAS` | Four-point pelvis tracking cluster |
| Left thigh | `L_TH1` ... `L_TH4` | Four-marker rigid plate |
| Right thigh | `R_TH1` ... `R_TH4` | Four-marker rigid plate |
| Left shank | `L_SK1` ... `L_SK4` | Four-marker rigid plate |
| Right shank | `R_SK1` ... `R_SK4` | Four-marker rigid plate |
| Left foot | `L_FCC`, `L_FM1`, `L_FM2`, `L_FM5` | Four tracking points |
| Right foot | `R_FCC`, `R_FM1`, `R_FM2`, `R_FM5` | Four tracking points |

Static files commonly have 36 markers: these 28 tracking markers plus anatomical/calibration markers. Learn the exact set from the user's completed static file and the project's marker-list XML; do not invent missing names.

## Local side-color convention

The demonstrated project uses QTM integer colors in `0xbbggrr` representation:

- Left: cyan, `16763904`
- Right: green, `3329330`

Treat these values as a project convention. In another project, read colors from the verified static trial before changing them.

## Bone topology

Use the project's label-list XML or verified static trial as the authoritative edge list. In the demonstrated configuration, static has 25 bones and dynamic has 21 bones.

Bones are semantic identity checks, not decoration. Correct positions with wrong names produce wrong lines and an invalid model even when all points are present. Within each plate, preserve the exact edges defined by the marker list. Do not assume a complete graph or infer edge order only from proximity.

## Rigid-cluster invariants

Store the six pairwise distances from the verified static trial. For each dynamic frame with four valid points, calculate:

```text
error_ij = dynamic_distance_ij - static_distance_ij
RMS = sqrt(sum(error_ij^2) / 6)
```

Use all six distances when testing label permutations. Also track individual edges because a low aggregate RMS can conceal one distorted edge. A four-marker plate may be close to symmetric, so require temporal continuity and agreement with trusted frames in addition to distance matching.
