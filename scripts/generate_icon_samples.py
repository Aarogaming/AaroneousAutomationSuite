"""
Generate icon samples for AAS Hub
Creates preview images of different icon designs
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "artifacts" / "icon_samples"
OUTPUT_DIR.mkdir(exist_ok=True)

def create_icon_option_1():
    """Indigo 'A' on solid background (current)"""
    img = Image.new('RGB', (256, 256), color=(99, 102, 241))  # Indigo-500
    draw = ImageDraw.Draw(img)
    
    # Try to use a larger, bolder font
    try:
        font = ImageFont.truetype("arial.ttf", 160)
    except:
        font = ImageFont.load_default()
    
    # Draw centered "A"
    draw.text((60, 40), "A", fill='white', font=font)
    
    img.save(OUTPUT_DIR / "option_1_simple_A.png")
    return "Option 1: Simple 'A' (Current)"

def create_icon_option_2():
    """Gradient background with bold 'AAS'"""
    img = Image.new('RGB', (256, 256), color=(99, 102, 241))
    draw = ImageDraw.Draw(img)
    
    # Create gradient
    for y in range(256):
        color_val = int(99 + (y / 256) * (50))
        color = (color_val, 102, 241)
        draw.line([(0, y), (256, y)], fill=color)
    
    try:
        font = ImageFont.truetype("arial.ttf", 90)
    except:
        font = ImageFont.load_default()
    
    draw.text((35, 85), "AAS", fill='white', font=font)
    
    img.save(OUTPUT_DIR / "option_2_gradient_AAS.png")
    return "Option 2: Gradient with 'AAS'"

def create_icon_option_3():
    """Hub/network node design"""
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    draw.ellipse([20, 20, 236, 236], fill=(99, 102, 241))
    
    # Central hub node
    center = 128
    draw.ellipse([center-25, center-25, center+25, center+25], fill='white')
    
    # Satellite nodes
    nodes = [
        (center, 60),      # top
        (196, 128),        # right
        (center, 196),     # bottom
        (60, 128),         # left
        (90, 90),          # top-left
        (166, 90),         # top-right
        (166, 166),        # bottom-right
        (90, 166)          # bottom-left
    ]
    
    for x, y in nodes:
        # Connection line
        draw.line([(center, center), (x, y)], fill='white', width=3)
        # Node circle
        draw.ellipse([x-12, y-12, x+12, y+12], fill='white')
    
    img.save(OUTPUT_DIR / "option_3_network_hub.png")
    return "Option 3: Network Hub Design"

def create_icon_option_4():
    """Hexagon with automation symbol"""
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Hexagon
    center = 128
    radius = 110
    import math
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        points.append((x, y))
    
    draw.polygon(points, fill=(99, 102, 241), outline='white', width=4)
    
    # Automation symbol (gear-like)
    gear_center = center
    gear_radius = 50
    for i in range(8):
        angle = math.radians(45 * i)
        x1 = gear_center + gear_radius * math.cos(angle)
        y1 = gear_center + gear_radius * math.sin(angle)
        x2 = gear_center + (gear_radius + 20) * math.cos(angle)
        y2 = gear_center + (gear_radius + 20) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill='white', width=6)
    
    draw.ellipse([gear_center-30, gear_center-30, gear_center+30, gear_center+30], 
                 fill=(99, 102, 241), outline='white', width=4)
    
    img.save(OUTPUT_DIR / "option_4_hexagon_gear.png")
    return "Option 4: Hexagon with Gear"

def create_icon_option_5():
    """Modern flat 'Hub' text"""
    img = Image.new('RGB', (256, 256), color=(99, 102, 241))
    draw = ImageDraw.Draw(img)
    
    # Rounded corners effect
    corner_radius = 40
    draw.rectangle([0, 0, 256, 256], fill=(99, 102, 241))
    
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 100)
        font_small = ImageFont.truetype("arial.ttf", 50)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large
    
    # Draw "AAS"
    draw.text((40, 60), "AAS", fill='white', font=font_large)
    draw.text((50, 160), "Hub", fill=(200, 220, 255), font=font_small)
    
    img.save(OUTPUT_DIR / "option_5_text_hub.png")
    return "Option 5: Text 'AAS Hub'"

def create_icon_option_6():
    """Circuit board pattern"""
    img = Image.new('RGB', (256, 256), color=(15, 23, 42))  # Dark slate
    draw = ImageDraw.Draw(img)
    
    # Draw circuit traces
    circuit_color = (99, 102, 241)
    
    # Horizontal lines
    for y in [40, 80, 120, 160, 200]:
        draw.line([(20, y), (236, y)], fill=circuit_color, width=3)
    
    # Vertical lines
    for x in [60, 100, 140, 180]:
        draw.line([(x, 20), (x, 236)], fill=circuit_color, width=3)
    
    # Connection nodes
    for x in [60, 100, 140, 180]:
        for y in [40, 80, 120, 160, 200]:
            draw.ellipse([x-6, y-6, x+6, y+6], fill='white')
    
    # Central "A" overlay
    try:
        font = ImageFont.truetype("arialbd.ttf", 120)
    except:
        font = ImageFont.load_default()
    
    draw.text((80, 65), "A", fill=(99, 255, 150), font=font)
    
    img.save(OUTPUT_DIR / "option_6_circuit_board.png")
    return "Option 6: Circuit Board Theme"

if __name__ == "__main__":
    print("Generating AAS Hub icon samples...")
    print(f"Output directory: {OUTPUT_DIR}\n")
    
    options = [
        create_icon_option_1(),
        create_icon_option_2(),
        create_icon_option_3(),
        create_icon_option_4(),
        create_icon_option_5(),
        create_icon_option_6()
    ]
    
    for opt in options:
        print(f"✓ {opt}")
    
    print(f"\n✓ All samples saved to: {OUTPUT_DIR}")
    print("\nTo use an icon, update create_icon() in aas_tray.py")
