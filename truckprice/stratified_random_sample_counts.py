"""Stratified sample of 200 TruckPaper images + aggregate part-focused labels."""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "image_scraper" / "truckpaper_listings.json"
IMG_ROOT = ROOT / "image_scraper" / "TruckPaper Scraped Images Dataset"
OUT_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = OUT_DIR / "sample_200.json"
LABELS_PATH = OUT_DIR / "primary_subject_labels.jsonl"
COUNTS_PATH = OUT_DIR / "primary_subject_counts.py"

N = 200
POS_TARGET = 130
NEG_TARGET = 70
SEED = 42


def load_pool() -> dict[str, dict[str, list[dict]]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_group: dict[str, dict[str, list[dict]]] = {
        "Positive (Class 7-8)": defaultdict(list),
        "Negative (Class 2-6)": defaultdict(list),
    }
    for cat, listings in data.items():
        group = cat.split("/")[0]
        if group not in by_group:
            continue
        for listing in listings:
            for i, rel in enumerate(listing.get("images") or []):
                abs_path = IMG_ROOT / Path(rel)
                if not abs_path.exists():
                    continue
                by_group[group][cat].append(
                    {
                        "sample_id": None,
                        "listing_id": listing["id"],
                        "brand": listing.get("brand"),
                        "category": cat,
                        "group": group,
                        "image_index": i,
                        "rel_path": rel.replace("\\", "/"),
                        "abs_path": str(abs_path),
                    }
                )
    return by_group


def sample_group(cat_map: dict[str, list[dict]], target: int, rng: random.Random) -> list[dict]:
    cats = [c for c, items in cat_map.items() if items]
    if not cats:
        return []
    per = {c: 0 for c in cats}
    remaining = target
    for c in sorted(cats, key=lambda x: -len(cat_map[x])):
        if remaining <= 0:
            break
        per[c] += 1
        remaining -= 1
    total = sum(len(cat_map[c]) for c in cats)
    while remaining > 0:
        best, best_score = None, -1e18
        for c in cats:
            capacity = len(cat_map[c]) - per[c]
            if capacity <= 0:
                continue
            ideal = target * (len(cat_map[c]) / total)
            score = (ideal - per[c]) + capacity * 0.001
            if score > best_score:
                best_score, best = score, c
        if best is None:
            break
        per[best] += 1
        remaining -= 1

    picked: list[dict] = []
    for c, n in per.items():
        by_listing: dict[str, list[dict]] = defaultdict(list)
        for it in cat_map[c]:
            by_listing[it["listing_id"]].append(it)
        listing_ids = list(by_listing.keys())
        rng.shuffle(listing_ids)
        chosen: list[dict] = []
        li = 0
        while len(chosen) < n and listing_ids:
            lid = listing_ids[li % len(listing_ids)]
            pool = by_listing[lid]
            if not pool:
                listing_ids = [x for x in listing_ids if x != lid]
                if not listing_ids:
                    break
                continue
            pool_sorted = sorted(pool, key=lambda x: x["image_index"])
            prefer = [0, len(pool_sorted) // 2, max(0, len(pool_sorted) - 1)]
            img = None
            for pref in prefer:
                cand = pool_sorted[min(pref, len(pool_sorted) - 1)]
                if cand in pool:
                    img = cand
                    break
            if img is None:
                img = rng.choice(pool)
            chosen.append(dict(img))
            by_listing[lid] = [x for x in pool if x is not img]
            li += 1
        picked.extend(chosen[:n])
    return picked


def build_sample() -> list[dict]:
    rng = random.Random(SEED)
    pool = load_pool()
    sample = sample_group(pool["Positive (Class 7-8)"], POS_TARGET, rng) + sample_group(
        pool["Negative (Class 2-6)"], NEG_TARGET, rng
    )
    rng.shuffle(sample)
    if len(sample) > N:
        sample = sample[:N]
    elif len(sample) < N:
        used = {s["abs_path"] for s in sample}
        extras = [
            it
            for items in pool["Positive (Class 7-8)"].values()
            for it in items
            if it["abs_path"] not in used
        ]
        rng.shuffle(extras)
        sample.extend(extras[: N - len(sample)])
    for i, s in enumerate(sample):
        s["sample_id"] = f"sample_{i:03d}"
    assert len(sample) == N
    SAMPLE_PATH.write_text(json.dumps(sample, indent=2), encoding="utf-8")
    return sample


def write_counts(labels: list[dict]) -> dict[str, int]:
    counts = Counter(r["primary_subject"] for r in labels)
    ordered = dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    lines = [
        '"""Part-focused primary_subject counts on a stratified 200-image sample."""',
        "",
        f"# total = {sum(ordered.values())}",
        f"# unique labels = {len(ordered)}",
        "",
        "primary_subject_counts = {",
    ]
    for label, n in ordered.items():
        lines.append(f"    {label!r}: {n},")
    lines.append("}")
    lines.append("")
    COUNTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ordered


def load_labels() -> list[dict]:
    if not LABELS_PATH.exists():
        return []
    rows = []
    for line in LABELS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


ALLOWED = {
    "front",
    "back",
    "side",
    "interior",
    "tire",
    "wheel",
    "chassis",
    "engine",
    "badge",
    "roof",
    "other",
}


def merge_partials() -> list[dict]:
    """Merge _partial_*.jsonl into primary_subject_labels.jsonl and counts dict."""
    partials = sorted(OUT_DIR.glob("_partial_*.jsonl"))
    if not partials:
        raise SystemExit("No _partial_*.jsonl files found yet")
    by_id: dict[str, str] = {}
    for path in partials:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            label = str(row["primary_subject"]).strip().lower()
            if label not in ALLOWED:
                raise SystemExit(f"Invalid label {label!r} in {path.name} ({row.get('sample_id')})")
            by_id[row["sample_id"]] = label
    if len(by_id) != N:
        raise SystemExit(f"Expected {N} labels, got {len(by_id)}")
    sample = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    labels = []
    for rec in sample:
        sid = rec["sample_id"]
        labels.append(
            {
                "sample_id": sid,
                "primary_subject": by_id[sid],
                "abs_path": rec["abs_path"],
                "preview_path": rec.get("preview_path"),
            }
        )
    LABELS_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in labels) + "\n",
        encoding="utf-8",
    )
    counts = write_counts(labels)
    # delete temporary partials
    for path in partials:
        path.unlink()
    return labels, counts


def print_validation_examples(labels: list[dict], k: int = 10) -> None:
    rng = random.Random(SEED)
    picks = rng.sample(labels, k=min(k, len(labels)))
    print("\n=== validation examples (check these images) ===")
    for r in picks:
        print(f"{r['sample_id']}: {r['primary_subject']}")
        print(f"  preview: {r.get('preview_path')}")
        print(f"  source:  {r['abs_path']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "merge":
        labels, counts = merge_partials()
        print(f"wrote {COUNTS_PATH}")
        print(f"wrote {LABELS_PATH}")
        print("primary_subject_counts =", counts)
        print_validation_examples(labels, 10)
    else:
        sample = build_sample()
        print(f"wrote {SAMPLE_PATH} n={len(sample)}")
        print(
            "pos",
            sum(1 for s in sample if "Positive" in s["group"]),
            "neg",
            sum(1 for s in sample if "Negative" in s["group"]),
        )
