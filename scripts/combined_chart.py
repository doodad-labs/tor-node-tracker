#!/usr/bin/env python3

from pathlib import Path
from PIL import Image

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATS_DIR = PROJECT_ROOT / "stats"

LEFT_IMAGE = STATS_DIR / "network-chart.png"
RIGHT_IMAGE = STATS_DIR / "node-distribution-pie.png"
OUTPUT_FILE = STATS_DIR / "combined-analytics.png"

GAP = 10  # pixels
BACKGROUND_COLOR = (255, 255, 255)  # white

def combine_charts():
    """Combine two chart images side-by-side with white background."""
    
    # Check if both images exist
    if not LEFT_IMAGE.exists():
        print(f"Error: Left image not found: {LEFT_IMAGE}")
        return False
    
    if not RIGHT_IMAGE.exists():
        print(f"Error: Right image not found: {RIGHT_IMAGE}")
        return False
    
    print("Loading images...")
    left_img = Image.open(LEFT_IMAGE)
    right_img = Image.open(RIGHT_IMAGE)
    
    print(f"  Left image (network chart): {left_img.size}")
    print(f"  Right image (pie chart): {right_img.size}")
    
    # Get dimensions
    left_width, left_height = left_img.size
    right_width, right_height = right_img.size
    
    # Use max height as target (so both images fit without cropping)
    target_height = max(left_height, right_height)
    
    # Scale images to target height while maintaining aspect ratio
    left_scale = target_height / left_height
    new_left_width = int(left_width * left_scale)
    left_resized = left_img.resize((new_left_width, target_height), Image.Resampling.LANCZOS)
    
    right_scale = target_height / right_height
    new_right_width = int(right_width * right_scale)
    right_resized = right_img.resize((new_right_width, target_height), Image.Resampling.LANCZOS)
    
    print(f"\nResized images:")
    print(f"  Left: {left_resized.size}")
    print(f"  Right: {right_resized.size}")
    
    # Calculate combined dimensions
    combined_width = new_left_width + GAP + new_right_width
    combined_height = target_height
    
    print(f"\nCombined dimensions: {combined_width}x{combined_height}")
    
    # Create new image with white background
    combined_img = Image.new("RGB", (combined_width, combined_height), BACKGROUND_COLOR)
    
    # Paste left image
    combined_img.paste(left_resized, (0, 0))
    
    # Paste right image with gap
    combined_img.paste(right_resized, (new_left_width + GAP, 0))
    
    # Save combined image
    combined_img.save(OUTPUT_FILE, "PNG")
    print(f"\n✓ Combined chart saved: {OUTPUT_FILE}")
    
    return True

if __name__ == "__main__":
    print("Generating combined analytics chart...\n")
    success = combine_charts()
    
    if not success:
        exit(1)
