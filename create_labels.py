#!/usr/bin/env python3
"""
Create JSONL file with truck PHOTO PARTS labels for samples 000-039.

Labels based on visual inspection of each preview image.
"""

import json
from pathlib import Path

# Manual labels based on careful visual inspection of all 40 preview images
# Each label describes the dominant truck PART visible
labels = {
    'sample_000': 'side',      # Dump truck side view showing bed
    'sample_001': 'front',     # Dump truck front-facing cab
    'sample_002': 'front',     # Sleeper cab front angle
    'sample_003': 'side',      # Wrecker truck side view
    'sample_004': 'side',      # Dump truck with raised bed (side)
    'sample_005': 'side',      # Dump truck side view
    'sample_006': 'side',      # Flatbed truck side view
    'sample_007': 'side',      # Pickup truck side view (flatbed attachment)
    'sample_008': 'side',      # Flatbed truck side view with winch
    'sample_009': 'side',      # Box truck side view
    'sample_010': 'side',      # Box truck side view (parking lot)
    'sample_011': 'side',      # Sleeper cab side view
    'sample_012': 'front',     # Freightliner sleeper cab front
    'sample_013': 'side',      # Dump truck side view (wheels prominent)
    'sample_014': 'front',     # Freightliner cab front-facing
    'sample_015': 'front',     # Sleeper cab front view (dealer lot)
    'sample_016': 'side',      # Dump trucks lined up (side view)
    'sample_017': 'side',      # Box truck side view (International)
    'sample_018': 'side',      # Service truck side view (small)
    'sample_019': 'front',     # Dump truck front angle (bed up)
    'sample_020': 'side',      # Box truck side view (wet)
    'sample_021': 'back',      # Rear dump/service truck facing camera
    'sample_022': 'side',      # Dump truck side view (raised bed prominent)
    'sample_023': 'front',     # Sleeper cab front (Freightliner dealer)
    'sample_024': 'side',      # Sleeper cab International side view
    'sample_025': 'front',     # Sleeper cab front angle (vintage)
    'sample_026': 'side',      # Flatbed stake truck side view
    'sample_027': 'side',      # Dump truck side view (mountains background)
    'sample_028': 'front',     # Peterbilt sleeper cab front angle
    'sample_029': 'front',     # Freightliner cab front-facing (lot view)
    'sample_030': 'side',      # Box truck side view (rain)
    'sample_031': 'front',     # Kenworth cab front angle
    'sample_032': 'side',      # Flatbed truck side view (small cab)
    'sample_033': 'side',      # RAM pickup truck chassis/side view
    'sample_034': 'side',      # Garbage truck side view (orange compactor)
    'sample_035': 'side',      # Dump truck side view showing chassis/wheels
    'sample_036': 'side',      # Service truck side view (bucket lift)
    'sample_037': 'side',      # Bus/passenger van side view
    'sample_038': 'front',     # Sleeper cab front-facing (Freightliner)
    'sample_039': 'front',     # Flatbed truck front angle showing cab
}

# Validate all samples present
required_samples = {f'sample_{i:03d}' for i in range(40)}
labeled_samples = set(labels.keys())

if required_samples != labeled_samples:
    missing = required_samples - labeled_samples
    extra = labeled_samples - required_samples
    if missing:
        print(f"ERROR: Missing samples: {sorted(missing)}")
    if extra:
        print(f"ERROR: Extra samples: {sorted(extra)}")
    exit(1)

# Output JSONL
output_path = Path('c:\\Users\\senth\\54hackathon\\truckprice\\_partial_000_039.jsonl')

with open(output_path, 'w') as f:
    for i in range(40):
        sample_id = f'sample_{i:03d}'
        label = labels[sample_id]
        entry = {"sample_id": sample_id, "primary_subject": label}
        f.write(json.dumps(entry) + '\n')

print(f"Created {output_path}")
print(f"Total labels: {len(labels)}")

# Show label distribution
from collections import Counter
label_counts = Counter(labels.values())
print("\nLabel distribution:")
for label, count in sorted(label_counts.items()):
    print(f"  {label}: {count}")

print("\nFirst 5 entries:")
with open(output_path, 'r') as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        print(f"  {line.strip()}")

print("\nLast 5 entries:")
entries = []
with open(output_path, 'r') as f:
    entries = f.readlines()
for line in entries[-5:]:
    print(f"  {line.strip()}")
