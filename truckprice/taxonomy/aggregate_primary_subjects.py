"""Aggregate open_labels_batch_*.jsonl into primary_subject -> count dict."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parent
OUT_PY = TAXONOMY.parent / "primary_subject_counts.py"
OUT_JSON = TAXONOMY / "open_labels.jsonl"
OUT_COUNTS_JSON = TAXONOMY / "primary_subject_counts.json"


def main() -> None:
    records: list[dict] = []
    missing: list[str] = []
    for i in range(10):
        path = TAXONOMY / f"open_labels_batch_{i:02d}.jsonl"
        if not path.exists():
            missing.append(path.name)
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    if missing:
        raise SystemExit(f"Missing batch files: {missing}")

    if len(records) != 200:
        raise SystemExit(f"Expected 200 labels, got {len(records)}")

    counts = Counter(r["primary_subject"] for r in records)
    # stable sort: count desc, label asc
    primary_subject_counts = dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    OUT_JSON.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )
    OUT_COUNTS_JSON.write_text(
        json.dumps(primary_subject_counts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    py = [
        '"""Haiku open-ended primary_subject counts on the 200-image stratified sample."""',
        "",
        f"# total images labeled = {sum(primary_subject_counts.values())}",
        f"# unique primary_subject labels = {len(primary_subject_counts)}",
        "",
        "primary_subject_counts = {",
    ]
    for label, n in primary_subject_counts.items():
        py.append(f"    {label!r}: {n},")
    py.append("}")
    py.append("")
    OUT_PY.write_text("\n".join(py) + "\n", encoding="utf-8")

    print(f"wrote {OUT_PY}")
    print(f"unique labels: {len(primary_subject_counts)}")
    print(f"total: {sum(primary_subject_counts.values())}")
    for label, n in list(primary_subject_counts.items())[:25]:
        print(f"  {n:3d}  {label}")


if __name__ == "__main__":
    main()
