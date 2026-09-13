import json
from pathlib import Path
from PIL import Image
import sys

# Load the sample data
with open('sample_200.json', 'r') as f:
    samples = json.load(f)

# Get records 160-199
records = samples[160:200]

# Manual labeling based on visual inspection of each image
# ALLOWED: front, back, side, interior, tire, wheel, chassis, engine, badge, roof, other
labels = {}

for i, record in enumerate(records):
    sample_id = record['sample_id']
    preview_path = record['preview_path']
    
    try:
        # Try to open the image to verify it exists
        img = Image.open(preview_path)
        labels[sample_id] = None  # Will be filled manually
        print(f"{i}: {sample_id} loaded - {preview_path}")
    except Exception as e:
        print(f"{i}: {sample_id} - Error: {e}")

print(f"\nTotal records to process: {len(labels)}")
print("Need to manually inspect and label each image...")
