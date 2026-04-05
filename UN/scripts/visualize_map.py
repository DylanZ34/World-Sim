#!/usr/bin/env python3
"""Visualize world map using PIL - with orthogonal routes (like roads)."""

import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MAP_DIR = ROOT / "world" / "map"

# Load map
with open(MAP_DIR / "world-map.json") as f:
    graph = json.load(f)

cities = graph["cities"]
connections = graph["connections"]

# Canvas
W, H = 900, 700
img = Image.new("RGB", (W, H), "#f5f5dc")
draw = ImageDraw.Draw(img)

def scale(x, y):
    margin = 70
    return int(x * (W - 2*margin) + margin), int(y * (H - 2*margin) + margin)

def midpoint(p1, p2):
    return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)

def ortho_route(p1, p2, offset=25):
    """Create orthogonal route: horizontal + vertical segments."""
    # Random choice for which way to go first
    random.seed(int(p1[0]*100 + p1[1]*200 + p2[0]*10 + p2[1]))
    if random.random() > 0.5:
        # Horizontal first: p1 -> midpoint -> p2
        mid = midpoint(p1, p2)
        return [p1, (mid[0], p1[1]), (mid[0], mid[1]), (mid[0], mid[1]), (mid[0], p2[1]), p2]
    else:
        # Vertical first
        mid = midpoint(p1, p2)
        return [p1, (p1[0], mid[1]), (p1[0], mid[1]), (mid[0], mid[1]), (mid[0], p2[1]), p2]

# Colors
color_map = {
    "nation_1": "#4A90D9",
    "nation_2": "#D4A84B", 
    "nation_3": "#8B4513",
    None: "#8B8B8B"
}

# Draw routes first
for c1, c2 in connections:
    x1, y1 = cities[c1]["x"], cities[c1]["y"]
    x2, y2 = cities[c2]["x"], cities[c2]["y"]
    p1 = scale(x1, y1)
    p2 = scale(x2, y2)
    
    # Get orthogonal points
    pts = ortho_route((x1,y1), (x2,y2), offset=30)
    scaled = [scale(p[0], p[1]) for p in pts]
    
    # Draw as thick route
    for i in range(len(scaled)-1):
        draw.line([scaled[i], scaled[i+1]], fill="#8B4513", width=3)

# Try font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
except:
    font = font_small = font_tiny = ImageFont.load_default()

# Draw cities
for city_id, city in cities.items():
    x, y = scale(city["x"], city["y"])
    owner = city.get("owner")
    color = color_map.get(owner, "#8B8B8B")
    radius = 20 + city["size"] * 4
    
    # White border  
    draw.ellipse([x-radius-3, y-radius-3, x+radius+3, y+radius+3], fill="white", outline="white")
    # City
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline="black", width=2)
    
    # Capital marker
    if city.get("is_capital"):
        draw.ellipse([x-radius+6, y-radius+6, x+radius-6, y+radius-6], fill="#ffe4b5")
        draw.text((x-10, y-10), "★", fill="black", font=font)
    
    # Label
    draw.text((x + radius + 5, y - 6), city["name"], fill="black", font=font_small)

# Legend
legend_y = 25
legend = [("Hodges", "#4A90D9"), ("Aksum", "#D4A84B"), ("Urartu", "#8B4513"), ("Neutral", "#8B8B8B")]
for i, (name, color) in enumerate(legend):
    x = 25 + i * 140
    draw.ellipse([x, legend_y, x+18, legend_y+18], fill=color, outline="black", width=1)
    draw.text((x + 22, legend_y + 2), name, fill="black", font=font_tiny)

# Stats
draw.text((W - 180, H - 30), f"{len(cities)} cities, {len(connections)} routes", fill="#555", font=font_tiny)

# Save
img.save(MAP_DIR / "world-map.png")
print(f"Saved: {MAP_DIR / 'world-map.png'}")