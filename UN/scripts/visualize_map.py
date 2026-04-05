#!/usr/bin/env python3
"""Visualize world map using PIL - smaller cities, larger fonts."""

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
W, H = 950, 750
img = Image.new("RGB", (W, H), "#f5f5dc")  # Slightly larger canvas
draw = ImageDraw.Draw(img)

def scale(x, y):
    margin = 80  # More margin
    return int(x * (W - 2*margin) + margin), int(y * (H - 2*margin) + margin)

def midpoint(p1, p2):
    return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)

def ortho_route(p1, p2, offset=20):
    """Orthogonal route with less overlap."""
    random.seed(int(p1[0]*1000 + p1[1]*2000 + p2[0]*100 + p2[1]))
    
    # Alternate routes more to reduce overlap
    if random.random() > 0.3:
        mid = midpoint(p1, p2)
        if random.random() > 0.5:
            return [p1, (mid[0], p1[1]), (mid[0], mid[1]), (mid[0], p2[1]), p2]
        else:
            return [p1, (p1[0], mid[1]), (mid[0], mid[1]), (p2[0], mid[1]), p2]
    else:
        # Direct route for some (reduces clutter)
        return [p1, p2]

# Colors
color_map = {
    "nation_1": "#4A90D9",
    "nation_2": "#D4A84B", 
    "nation_3": "#8B4513",
    None: "#8B8B8B"
}

# Draw routes first (thinner)
for c1, c2 in connections:
    x1, y1 = cities[c1]["x"], cities[c1]["y"]
    x2, y2 = cities[c2]["x"], cities[c2]["y"]
    p1 = scale(x1, y1)
    p2 = scale(x2, y2)
    
    pts = ortho_route((x1,y1), (x2,y2), offset=20)
    scaled = [scale(p[0], p[1]) for p in pts]
    
    for i in range(len(scaled)-1):
        draw.line([scaled[i], scaled[i+1]], fill="#8B4513", width=2)  # Thinner routes

# Larger fonts
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font = font_large = font_small = font_tiny = ImageFont.load_default()

# Smaller cities!
for city_id, city in cities.items():
    x, y = scale(city["x"], city["y"])
    owner = city.get("owner")
    color = color_map.get(owner, "#8B8B8B")
    radius = 12 + city["size"] * 2  # Smaller: 12 + size*2 instead of 20 + size*4
    
    # White border
    draw.ellipse([x-radius-2, y-radius-2, x+radius+2, y+radius+2], fill="white", outline="white")
    # City
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline="black", width=2)
    
    # Capital marker
    if city.get("is_capital"):
        draw.ellipse([x-radius+4, y-radius+4, x+radius-4, y+radius-4], fill="#ffe4b5")
        draw.text((x-8, y-8), "★", fill="black", font=font)
    
    # Label below city instead
    draw.text((x - len(city["name"])*5, y + radius + 5), city["name"], fill="black", font=font_large)

# Legend
legend_y = 30
legend = [("Hodges", "#4A90D9"), ("Aksum", "#D4A84B"), ("Urartu", "#8B4513"), ("Neutral", "#8B8B8B")]
for i, (name, color) in enumerate(legend):
    x = 30 + i * 150
    draw.ellipse([x, legend_y, x+20, legend_y+20], fill=color, outline="black", width=1)
    draw.text((x + 25, legend_y + 3), name, fill="black", font=font_small)

# Stats
draw.text((W - 180, H - 35), f"{len(cities)} cities, {len(connections)} routes", fill="#555", font=font_tiny)

# Save
img.save(MAP_DIR / "world-map.png")
print(f"Saved: {MAP_DIR / 'world-map.png'}")