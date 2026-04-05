#!/usr/bin/env python3
"""Visualize world map using PIL."""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent  # World-Sim root
MAP_DIR = ROOT / "world" / "map"

# Load map
with open(MAP_DIR / "world-map.json") as f:
    graph = json.load(f)

cities = graph["cities"]
connections = graph["connections"]

# Canvas size
W, H = 800, 600
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

# Scale coordinates to canvas
def scale(x, y):
    return int(x * (W - 100) + 50), int(y * (H - 100) + 50)

# Colors
color_map = {
    "nation_1": "#4A90D9",  # Blue for Hodges
    "nation_2": "#D4A84B",  # Gold for Aksum
    "nation_3": "#8B4513",  # Brown for Urartu
    None: "#AAAAAA",        # Gray for unclaimed
}

# Draw connections
for c1, c2 in connections:
    x1, y1 = cities[c1]["x"], cities[c1]["y"]
    x2, y2 = cities[c2]["x"], cities[c2]["y"]
    p1 = scale(x1, y1)
    p2 = scale(x2, y2)
    draw.line([p1, p2], fill="#CCCCCC", width=2)

# Try to load a font, fall back to default
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw cities
for city_id, city in cities.items():
    x, y = scale(city["x"], city["y"])
    owner = city.get("owner")
    color = color_map.get(owner, "#AAAAAA")
    
    # Size based on city size
    radius = 15 + city["size"] * 3
    
    # Draw
    if city.get("is_capital"):
        # Star/circle with border
        draw.ellipse([x-radius-3, y-radius-3, x+radius+3, y+radius+3], fill="black")
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
        # Label
        draw.text((x + radius + 5, y - 10), city["name"], fill="black", font=font)
    else:
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline="black")
        # Label
        draw.text((x + radius + 3, y - 5), city["name"], fill="black", font=font_small)

# Legend
legend_y = 30
legend = [("Hodges", "#4A90D9"), ("Aksum", "#D4A84B"), ("Urartu", "#8B4513"), ("Unclaimed", "#AAAAAA")]
for i, (name, color) in enumerate(legend):
    x = 30 + i * 120
    draw.ellipse([x, legend_y, x+20, legend_y+20], fill=color, outline="black")
    draw.text((x + 25, legend_y + 3), name, fill="black", font=font_small)

# Title
draw.text((W//2 - 100, H - 30), f"World Map - {len(cities)} Cities, {len(connections)} Connections", fill="black", font=font)

# Save
img.save(MAP_DIR / "world-map.png")
print(f"Saved: {MAP_DIR / 'world-map.png'}")