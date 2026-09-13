import json
from pathlib import Path
from PIL import Image
import sys

# Load sample data
with open('c:\\Users\\senth\\54hackathon\\truckprice\\sample_200.json', 'r') as f:
    data = json.load(f)

# Extract samples 000-039
samples = sorted(
    [s for s in data if int(s['sample_id'].split('_')[1]) < 40],
    key=lambda x: int(x['sample_id'].split('_')[1])
)

print(f"Found {len(samples)} samples (000-039)")
print("\nFirst 5 samples:")
for s in samples[:5]:
    print(f"  {s['sample_id']}: {s['preview_path']}")
    # Check if file exists
    if Path(s['preview_path']).exists():
        print(f"    File exists")
    else:
        print(f"    File NOT found")
