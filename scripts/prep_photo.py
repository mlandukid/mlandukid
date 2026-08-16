"""
prep_photo.py

Prepares a source photo for ASCII conversion:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so a flatly-lit face gets real
     highlights and shadows instead of converting to a dark blob.
  3. Composite onto pure white so the background maps to the blank
     end of the ASCII ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.jpg

Output:
    source-prepped.png  (grayscale, in the project root)
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str = "source-prepped.png") -> None:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Could not find source photo: {input_path}")

    print(f"[1/3] Removing background from {src.name}...")
    with open(src, "rb") as f:
        input_bytes = f.read()
    subject_bytes = remove(input_bytes)

    # rembg returns RGBA PNG bytes; load into PIL
    subject = Image.open(__import__("io").BytesIO(subject_bytes)).convert("RGBA")

    # Composite onto pure white background
    print("[2/3] Compositing onto white background...")
    white_bg = Image.new("RGBA", subject.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, subject).convert("RGB")

    # Convert to grayscale numpy array for CLAHE
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)

    print("[3/3] Boosting local contrast (CLAHE)...")
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    out = Image.fromarray(contrasted)
    out.save(output_path)
    print(f"Done. Wrote {output_path} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    prep_photo(sys.argv[1])
