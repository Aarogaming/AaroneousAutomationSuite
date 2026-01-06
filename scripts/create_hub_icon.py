"""
Create a proper .ico file for AAS Hub with anti-aliasing
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math

OUTPUT_FILE = Path(__file__).parent.parent / "artifacts" / "aas_hub.ico"

def create_network_hub_icon(size):
    """Create simple letter A on colored background."""
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Solid indigo background circle
    draw.ellipse([0, 0, size - 1, size - 1], fill=(67, 56, 202))
    
    # Draw a bold letter "A" that fills most of the icon
    # Use simple geometric shapes since we can't rely on fonts
    
    # Calculate dimensions
    margin = int(size * 0.15)
    letter_width = size - (2 * margin)
    letter_height = int(size * 0.7)
    top = int(size * 0.15)
    left = margin
    
    # Letter A as a triangle outline
    peak_x = size // 2
    peak_y = top
    left_bottom = (left, top + letter_height)
    right_bottom = (left + letter_width, top + letter_height)
    
    # Outer triangle
    outer_thickness = max(4, int(size * 0.08))
    draw.polygon([
        (peak_x, peak_y),
        left_bottom,
        right_bottom
    ], fill='white')
    
    # Inner triangle (cut out to make it hollow)
    inner_offset = max(3, int(size * 0.12))
    draw.polygon([
        (peak_x, peak_y + inner_offset * 1.5),
        (left_bottom[0] + inner_offset, left_bottom[1] - inner_offset),
        (right_bottom[0] - inner_offset, right_bottom[1] - inner_offset)
    ], fill=(67, 56, 202))
    
    # Cross bar for A
    bar_y = top + int(letter_height * 0.6)
    bar_thickness = max(3, int(size * 0.08))
    bar_left = left + int(letter_width * 0.25)
    bar_right = left + int(letter_width * 0.75)
    draw.rectangle([
        bar_left, bar_y,
        bar_right, bar_y + bar_thickness
    ], fill='white')
    
    return img

# Create multiple sizes for Windows .ico format
# Create all sizes
sizes = [256, 128, 64, 48, 32, 24, 16]
images = []

for size in sizes:
    img = create_network_hub_icon(size)
    images.append(img)

# Save the largest image with all smaller sizes appended
images[0].save(
    OUTPUT_FILE, 
    format='ICO',
    append_images=images[1:],
    bitmap_format='png'  # Use PNG compression for better quality
)

print(f"✓ Icon created: {OUTPUT_FILE}")
print(f"  File size: {OUTPUT_FILE.stat().st_size} bytes")
print(f"  Contains {len(images)} sizes: {sizes}")

