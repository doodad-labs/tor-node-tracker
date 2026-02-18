#!/usr/bin/env python3

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATS_DIR = PROJECT_ROOT / "stats"

TOP_LEFT_IMAGE = STATS_DIR / "network-chart.png"
TOP_RIGHT_IMAGE = STATS_DIR / "node-distribution-pie.png"
BOTTOM_IMAGE = STATS_DIR / "geolocation-map.png"
OUTPUT_FILE = STATS_DIR / "combined-analytics.png"

HORIZONTAL_GAP = 10  # pixels between left and right charts
VERTICAL_GAP = 20    # pixels between top row and bottom chart
BACKGROUND_COLOR = (255, 255, 255)  # white

def combine_charts():
    """Combine three chart images: two on top (side-by-side), one full-width on bottom."""
    
    # Check if all images exist
    if not TOP_LEFT_IMAGE.exists():
        print(f"Error: Top left image not found: {TOP_LEFT_IMAGE}")
        return False
    
    if not TOP_RIGHT_IMAGE.exists():
        print(f"Error: Top right image not found: {TOP_RIGHT_IMAGE}")
        return False
    
    if not BOTTOM_IMAGE.exists():
        print(f"Error: Bottom image not found: {BOTTOM_IMAGE}")
        return False
    
    print("Loading images...")
    top_left_img = Image.open(TOP_LEFT_IMAGE)
    top_right_img = Image.open(TOP_RIGHT_IMAGE)
    bottom_img = Image.open(BOTTOM_IMAGE)
    
    print(f"  Top left image (network chart): {top_left_img.size}")
    print(f"  Top right image (pie chart): {top_right_img.size}")
    print(f"  Bottom image (geolocation map): {bottom_img.size}")
    
    # Get dimensions
    left_width, left_height = top_left_img.size
    right_width, right_height = top_right_img.size
    bottom_width, bottom_height = bottom_img.size
    
    # Use max height of top charts as target for top row
    top_target_height = max(left_height, right_height)
    
    # Scale top images to target height while maintaining aspect ratio
    left_scale = top_target_height / left_height
    new_left_width = int(left_width * left_scale)
    top_left_resized = top_left_img.resize((new_left_width, top_target_height), Image.Resampling.LANCZOS)
    
    right_scale = top_target_height / right_height
    new_right_width = int(right_width * right_scale)
    top_right_resized = top_right_img.resize((new_right_width, top_target_height), Image.Resampling.LANCZOS)
    
    # Calculate top row width
    top_row_width = new_left_width + HORIZONTAL_GAP + new_right_width
    
    # Scale bottom image to match top row width while maintaining aspect ratio
    bottom_scale = top_row_width / bottom_width
    new_bottom_height = int(bottom_height * bottom_scale)
    bottom_resized = bottom_img.resize((top_row_width, new_bottom_height), Image.Resampling.LANCZOS)
    
    print(f"\nResized images:")
    print(f"  Top left: {top_left_resized.size}")
    print(f"  Top right: {top_right_resized.size}")
    print(f"  Bottom: {bottom_resized.size}")
    
    # Calculate final combined dimensions
    combined_width = top_row_width
    combined_height = top_target_height + VERTICAL_GAP + new_bottom_height
    
    print(f"\nCombined dimensions: {combined_width}x{combined_height}")
    
    # Create new image with white background
    combined_img = Image.new("RGB", (combined_width, combined_height), BACKGROUND_COLOR)
    
    # Paste top left image
    combined_img.paste(top_left_resized, (0, 0))
    
    # Paste top right image with horizontal gap
    combined_img.paste(top_right_resized, (new_left_width + HORIZONTAL_GAP, 0))
    
    # Paste bottom image with vertical gap
    combined_img.paste(bottom_resized, (0, top_target_height + VERTICAL_GAP))
    
    # Add timestamp in bottom left
    draw = ImageDraw.Draw(combined_img)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Try to use a system font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    # Add text with padding from bottom-left corner
    text_x = 10
    text_y = combined_height - 25
    draw.text((text_x, text_y), f"Generated: {timestamp}", fill="gray", font=font)
    
    # Save combined image
    combined_img.save(OUTPUT_FILE, "PNG")
    print(f"\n✓ Combined chart saved: {OUTPUT_FILE}")
    print(f"  Timestamp: {timestamp}")
    
    return True

if __name__ == "__main__":
    print("Generating combined analytics chart...\n")
    success = combine_charts()
    
    if not success:
        exit(1)
