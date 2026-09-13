#!/usr/bin/env python3
"""
Manually label each of the 40 truck images by inspecting them one by one.
"""

import json
from pathlib import Path

# Load sample data
with open('c:\\Users\\senth\\54hackathon\\truckprice\\sample_200.json', 'r') as f:
    data = json.load(f)

# Extract samples 000-039
samples = sorted(
    [s for s in data if int(s['sample_id'].split('_')[1]) < 40],
    key=lambda x: int(x['sample_id'].split('_')[1])
)

# I'll build labels based on systematic visual inspection
# This maps sample_id to primary_subject label

manual_labels = {
    # Will be filled by examining each image
}

print(f"Total samples to label: {len(samples)}")
print("\nRunning visual analysis on each preview image...")

for i, sample in enumerate(samples):
    sample_id = sample['sample_id']
    preview_path = Path(sample['preview_path'])
    print(f"\n[{i+1}/{len(samples)}] {sample_id}: {preview_path.name}")
    
    if preview_path.exists():
        print(f"  File exists: {preview_path}")
    else:
        print(f"  WARNING: File not found!")

print(f"\nReady to label all {len(samples)} samples")
