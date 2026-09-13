import os
import json
import random
from pathlib import Path
import cv2
import numpy as np
import albumentations as A
from tqdm import tqdm

INPUT_DIR = "downloaded_truck_images"        # Directory containing clean source images
OUTPUT_IMAGE_DIR = "degraded_truck_images"   # Where degraded images will be saved
OUTPUT_JSON = "degraded_truck_dataset.json"  # Standalone degraded evaluation JSON file
SAMPLES_PER_CATEGORY = 100                   # Number of samples generated per defect type

os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

# 1. Blur Pipeline (Severe lens blur, defocus, motion blur)
heavy_blur_pipeline = A.Compose([
    A.OneOf([
        A.GaussianBlur(blur_limit=(35, 55), p=1.0),
        A.Defocus(radius=(12, 22), alias_blur=(0.3, 0.6), p=1.0),
        A.MotionBlur(blur_limit=(31, 51), p=1.0)
    ], p=1.0)
])

# 2. Underexposure (Dark night yard / unlit environment)
dark_pipeline = A.Compose([
    A.RandomBrightnessContrast(brightness_limit=(-0.85, -0.65), contrast_limit=(-0.4, -0.1), p=1.0),
    A.GaussNoise(var_limit=(50.0, 120.0), p=1.0)
])

# 3. Overexposure (Direct headlight/sunlight glare washout)
glare_pipeline = A.Compose([
    A.RandomBrightnessContrast(brightness_limit=(0.6, 0.85), contrast_limit=(0.3, 0.6), p=1.0),
    A.RandomSunFlare(flare_roi=(0, 0, 1, 0.6), angle_lower=0.5, src_radius=150, p=0.8)
])

# 4. Pixelation (Severe downsampling / thumbnail scaling)
pixelate_pipeline = A.Compose([
    A.Downscale(scale_range=(0.05, 0.12), interpolation_pair={"downscale": cv2.INTER_NEAREST, "upscale": cv2.INTER_NEAREST}, p=1.0)
])

# 5. Severe JPEG Compression (Messaging app re-encoding artifacts)
compression_pipeline = A.Compose([
    A.ImageCompression(quality_range=(3, 8), compression_type="jpeg", p=1.0)
])

def apply_image_sharding(img: np.ndarray) -> np.ndarray:
    """Simulates corrupt network packets, missing file blocks, and scanline errors."""
    corrupted = img.copy()
    h, w, c = corrupted.shape
    num_shards = random.randint(3, 7)

    for _ in range(num_shards):
        shard_type = random.choice(["blackout", "noise", "channel_shift", "slice_drop"])
        if random.random() > 0.4:
            y1 = random.randint(0, max(0, h - 30))
            y2 = min(h, y1 + random.randint(20, max(30, h // 4)))
            x1, x2 = 0, w
        else:
            x1 = random.randint(0, max(0, w - 30))
            x2 = min(w, x1 + random.randint(20, max(30, w // 4)))
            y1, y2 = 0, h

        if shard_type == "blackout":
            corrupted[y1:y2, x1:x2] = 0
        elif shard_type == "noise":
            corrupted[y1:y2, x1:x2] = np.random.randint(0, 256, (y2 - y1, x2 - x1, c), dtype=np.uint8)
        elif shard_type == "channel_shift":
            corrupted[y1:y2, x1:x2, random.randint(0, c - 1)] = 255
        elif shard_type == "slice_drop":
            shift = random.randint(20, 80)
            corrupted[y1:y2, :] = np.roll(corrupted[y1:y2, :], shift, axis=1)

    return corrupted

def apply_bad_framing(img: np.ndarray) -> np.ndarray:
    """Simulates poorly framed user uploads where the vehicle is largely out of view."""
    h, w = img.shape[:2]
    mode = random.choice(["edge_crop", "corner_slice", "extreme_offset"])

    if mode == "edge_crop":
        if random.random() > 0.5:
            y_start = 0 if random.random() > 0.5 else int(h * 0.75)
            y_end = int(h * 0.25) if y_start == 0 else h
            cropped = img[y_start:y_end, :]
        else:
            x_start = 0 if random.random() > 0.5 else int(w * 0.75)
            x_end = int(w * 0.25) if x_start == 0 else w
            cropped = img[:, x_start:x_end]

    elif mode == "corner_slice":
        crop_h, crop_w = int(h * random.uniform(0.18, 0.32)), int(w * random.uniform(0.18, 0.32))
        y_start = 0 if random.random() > 0.5 else (h - crop_h)
        x_start = 0 if random.random() > 0.5 else (w - crop_w)
        cropped = img[y_start:y_start + crop_h, x_start:x_start + crop_w]

    elif mode == "extreme_offset":
        shift_x = int(w * random.choice([-0.68, 0.68]))
        shift_y = int(h * random.choice([-0.68, 0.68]))
        matrix = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        return cv2.warpAffine(img, matrix, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

DEGRADATION_MODES = {
    "heavy_blur": lambda img: heavy_blur_pipeline(image=img)["image"],
    "sharded_corrupt": apply_image_sharding,
    "bad_framing": apply_bad_framing,
    "extreme_underexposed": lambda img: dark_pipeline(image=img)["image"],
    "extreme_overexposed": lambda img: glare_pipeline(image=img)["image"],
    "heavy_pixelation": lambda img: pixelate_pipeline(image=img)["image"],
    "heavy_compression": lambda img: compression_pipeline(image=img)["image"]
}

def generate_degraded_dataset():
    input_path = Path(INPUT_DIR)
    all_images = list(input_path.glob("*.jpg")) + list(input_path.glob("*.png")) + list(input_path.glob("*.jpeg"))
    
    if not all_images:
        print(f"No source images found in '{INPUT_DIR}'. Verify your directory.")
        return

    degraded_records = []
    sample_counter = 1

    for mode_name, transform_fn in DEGRADATION_MODES.items():
        sampled = random.sample(all_images, min(SAMPLES_PER_CATEGORY, len(all_images)))

        for idx, img_file in enumerate(tqdm(sampled, desc=f"Generating {mode_name}")):
            img = cv2.imread(str(img_file))
            if img is None:
                continue

            corrupted_img = transform_fn(img)
            out_filename = f"{img_file.stem}_{mode_name}_{idx}.jpg"
            dest_path = Path(OUTPUT_IMAGE_DIR) / out_filename
            cv2.imwrite(str(dest_path), corrupted_img)

            degraded_records.append({
                "id": f"degraded_sample_{sample_counter:04d}",
                "brand": "UNKNOWN",
                "price": None,
                "currency": "USD",
                "images": [dest_path.as_posix()]
            })
            sample_counter += 1

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(degraded_records, f, indent=2)

    print(f"\nGenerated {len(degraded_records)} degraded samples.")
    print(f"Images stored in: '{OUTPUT_IMAGE_DIR}/'")
    print(f"Evaluation metadata written to: '{OUTPUT_JSON}'")

if __name__ == "__main__":
    generate_degraded_dataset()