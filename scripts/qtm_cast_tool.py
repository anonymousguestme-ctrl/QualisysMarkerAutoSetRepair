#!/usr/bin/env python3
"""Capture a CAST template, audit an open trial, or plan/execute relational repair."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


API = "http://127.0.0.1:7979/api/scripting/qtm"
CLUSTERS = {
    "pelvis": ["L_IAS", "L_IPS", "R_IPS", "R_IAS"],
    "left_thigh": ["L_TH1", "L_TH2", "L_TH3", "L_TH4"],
    "left_shank": ["L_SK1", "L_SK2", "L_SK3", "L_SK4"],
    "left_foot": ["L_FCC", "L_FM1", "L_FM2", "L_FM5"],
    "right_thigh": ["R_TH1", "R_TH2", "R_TH3", "R_TH4"],
    "right_shank": ["R_SK1", "R_SK2", "R_SK3", "R_SK4"],
    "right_foot": ["R_FCC", "R_FM1", "R_FM2", "R_FM5"],
}
LEFT_COLOR = 16763904
RIGHT_COLOR = 3329330


def post(method: str, arguments=None):
    request = urllib.request.Request(
        f"{API}/{method}/",
        data=json.dumps(arguments or []).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
    except urllib.error.URLError as error:
        raise RuntimeError(f"QTM REST call failed: {method}: {error}") from error
    return json.loads(body) if body else None


def distance(first, second):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)] if ordered else None


def require_open_file():
    if not post("file/is_open"):
        raise RuntimeError("Open a QTM measurement before running this command.")


def all_labels():
    result = {}
    for trajectory_id in post("data/object/trajectory/get_trajectory_ids"):
        label = post("data/object/trajectory/get_label", [trajectory_id])
        if label is not None:
            result[label] = trajectory_id
    return result


def require_trajectories(labels):
    result = {label: post("data/object/trajectory/find_trajectory", [label]) for label in labels}
    missing = [label for label, trajectory_id in result.items() if trajectory_id is None]
    if missing:
        raise RuntimeError(f"Missing trajectories: {', '.join(missing)}")
    return result


def capture_template(output: Path):
    require_open_file()
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite existing template: {output}")
    measured = post("gui/timeline/get_measured_range")
    labels = all_labels()
    positions = {}
    for label, trajectory_id in labels.items():
        samples = post("data/series/_3d/get_samples", [trajectory_id, measured])
        valid = [sample["position"] for sample in samples if sample is not None]
        if valid:
            positions[label] = [statistics.median(axis) for axis in zip(*valid)]

    clusters = {}
    for name, members in CLUSTERS.items():
        if all(member in positions for member in members):
            clusters[name] = {
                f"{first}|{second}": distance(positions[first], positions[second])
                for first, second in itertools.combinations(members, 2)
            }
    payload = {
        "source": post("file/get_path"),
        "measured_range": measured,
        "positions_mm": positions,
        "clusters": clusters,
        "colors": {
            label: post("data/object/trajectory/get_color", [trajectory_id])
            for label, trajectory_id in labels.items()
        },
        "bone_count": len(post("data/object/bone/get_bone_ids") or []),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def identity_rms(members, points, expected):
    errors = [
        distance(points[first], points[second]) - expected[f"{first}|{second}"]
        for first, second in itertools.combinations(members, 2)
    ]
    return math.sqrt(sum(error * error for error in errors) / len(errors))


def best_permutations(members, points, expected):
    scored = []
    for permutation in itertools.permutations(members):
        permuted = dict(zip(members, (points[label] for label in permutation)))
        scored.append((identity_rms(members, permuted, expected), permutation))
    return sorted(scored, key=lambda item: item[0])[:2]


def audit(template_path: Path | None, include_permutations: bool):
    require_open_file()
    measured = post("gui/timeline/get_measured_range")
    all_ids = post("data/object/trajectory/get_trajectory_ids")
    labels_by_id = {
        trajectory_id: post("data/object/trajectory/get_label", [trajectory_id])
        for trajectory_id in all_ids
    }
    labels = {label: trajectory_id for trajectory_id, label in labels_by_id.items() if label is not None}
    samples = {
        trajectory_id: post("data/series/_3d/get_samples", [trajectory_id, measured])
        for trajectory_id in all_ids
    }
    frame_count = measured["end"] - measured["start"] + 1
    labelled_histogram = Counter()
    total_histogram = Counter()
    for offset in range(frame_count):
        present = [trajectory_id for trajectory_id in all_ids if samples[trajectory_id][offset] is not None]
        total_histogram[len(present)] += 1
        labelled_histogram[sum(labels_by_id[item] is not None for item in present)] += 1

    gaps = {}
    for label, trajectory_id in labels.items():
        ranges = post("data/series/_3d/get_gap_ranges", [trajectory_id]) or []
        if ranges:
            gaps[label] = ranges
    result = {
        "path": post("file/get_path"),
        "dirty": post("file/is_dirty"),
        "measured_range_api": measured,
        "display_range_if_one_based": {"start": measured["start"] + 1, "end": measured["end"] + 1},
        "label_count": len(labels),
        "empty_labels": [
            label for label, trajectory_id in labels.items()
            if not (post("data/object/trajectory/get_parts", [trajectory_id]) or [])
        ],
        "bad_project_colors": [
            label for label, trajectory_id in labels.items()
            if label.startswith(("L_", "R_"))
            and post("data/object/trajectory/get_color", [trajectory_id])
            != (LEFT_COLOR if label.startswith("L_") else RIGHT_COLOR)
        ],
        "bone_count": len(post("data/object/bone/get_bone_ids") or []),
        "labelled_points_per_frame": dict(sorted(labelled_histogram.items())),
        "total_points_per_frame": dict(sorted(total_histogram.items())),
        "gaps": gaps,
    }

    if template_path:
        template = json.loads(template_path.read_text(encoding="utf-8"))
        rigid = {}
        for name, members in CLUSTERS.items():
            if name not in template.get("clusters", {}) or not all(member in labels for member in members):
                continue
            values = []
            alternatives = []
            for offset in range(frame_count):
                frame_samples = {member: samples[labels[member]][offset] for member in members}
                if any(sample is None for sample in frame_samples.values()):
                    continue
                points = {member: sample["position"] for member, sample in frame_samples.items()}
                current = identity_rms(members, points, template["clusters"][name])
                values.append(current)
                if include_permutations:
                    best_two = best_permutations(members, points, template["clusters"][name])
                    if best_two[0][1] != tuple(members):
                        alternatives.append({
                            "api_sample": measured["start"] + offset,
                            "display_frame_if_one_based": measured["start"] + offset + 1,
                            "current_rms_mm": round(current, 3),
                            "best_rms_mm": round(best_two[0][0], 3),
                            "best_mapping": dict(zip(members, best_two[0][1])),
                            "second_best_rms_mm": round(best_two[1][0], 3),
                        })
            rigid[name] = {
                "frames": len(values),
                "median_rms_mm": round(statistics.median(values), 3) if values else None,
                "p95_rms_mm": round(percentile(values, 0.95), 3) if values else None,
                "max_rms_mm": round(max(values), 3) if values else None,
                "nonidentity_best_frames": alternatives,
            }
        result["rigid_clusters"] = rigid
    return result


def ensure_new_path(path: Path, description: str):
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite existing {description}: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def repair(args):
    require_open_file()
    start = args.start - args.frame_base
    end = args.end - args.frame_base
    if start > end:
        raise RuntimeError("Repair start must not exceed repair end.")
    measured = post("gui/timeline/get_measured_range")
    if start <= measured["start"] or end >= measured["end"]:
        raise RuntimeError("Relational repair requires a trusted target sample on both sides.")

    matching_clusters = [
        members for members in CLUSTERS.values()
        if args.target in members and all(reference in members for reference in args.references)
    ]
    if not matching_clusters:
        raise RuntimeError("Target and references must belong to the same CAST cluster.")
    ids = require_trajectories([args.target, *args.references])
    repair_range = {"start": start, "end": end}
    reference_missing = {}
    for label in args.references:
        series = post("data/series/_3d/get_samples", [ids[label], repair_range])
        missing = [start + index for index, sample in enumerate(series) if sample is None]
        if missing:
            reference_missing[label] = missing
    boundaries = {
        "before": post("data/series/_3d/get_sample", [ids[args.target], start - 1]) is not None,
        "after": post("data/series/_3d/get_sample", [ids[args.target], end + 1]) is not None,
    }
    plan = {
        "current_path": post("file/get_path"),
        "current_dirty": post("file/is_dirty"),
        "target": args.target,
        "requested_frames": {"start": args.start, "end": args.end, "frame_base": args.frame_base},
        "api_range": repair_range,
        "references": args.references,
        "reference_missing_samples": reference_missing,
        "target_boundaries_present": boundaries,
        "execute": args.execute,
    }
    if reference_missing or not all(boundaries.values()):
        raise RuntimeError(json.dumps(plan, indent=2))
    if not args.execute:
        return plan
    if args.backup is None or args.output is None:
        raise RuntimeError("--execute requires both --backup and --output.")
    ensure_new_path(args.backup, "backup")
    ensure_new_path(args.output, "output")

    post("file/save_as", [str(args.backup.resolve())])
    settings = {"origin": ids[args.references[0]], "line": ids[args.references[1]]}
    if len(args.references) == 3:
        settings["plane"] = ids[args.references[2]]
    post("data/object/trajectory/fill_trajectory", [ids[args.target], "relational", repair_range, settings])
    post("file/save_as", [str(args.output.resolve())])
    plan.update({"backup": str(args.backup.resolve()), "output": str(args.output.resolve())})
    return plan


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture-template")
    capture.add_argument("--output", required=True, type=Path)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--template", type=Path)
    audit_parser.add_argument("--include-permutations", action="store_true")

    repair_parser = subparsers.add_parser("repair")
    repair_parser.add_argument("--target", required=True, choices=sum(CLUSTERS.values(), []))
    repair_parser.add_argument("--start", required=True, type=int)
    repair_parser.add_argument("--end", required=True, type=int)
    repair_parser.add_argument("--frame-base", choices=(0, 1), default=1, type=int)
    repair_parser.add_argument("--references", required=True, nargs="+", choices=sum(CLUSTERS.values(), []))
    repair_parser.add_argument("--backup", type=Path)
    repair_parser.add_argument("--output", type=Path)
    repair_parser.add_argument("--execute", action="store_true")
    return parser


def main():
    args = build_parser().parse_args()
    if args.command == "capture-template":
        result = capture_template(args.output)
    elif args.command == "audit":
        result = audit(args.template, args.include_permutations)
    else:
        if not 2 <= len(args.references) <= 3:
            raise RuntimeError("Relational repair requires two or three references.")
        if args.target in args.references:
            raise RuntimeError("Target cannot also be a reference.")
        result = repair(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
