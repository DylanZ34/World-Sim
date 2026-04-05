#!/usr/bin/env python3
"""Visualize world map using PIL - with routes between cities."""

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
W, H = 900, 700
img = Image.new("RGB", (W, H), "#f5f5dc")  # Parchment color
draw = ImageDraw.Draw(img)

# Scale coordinates to canvas
def scale(x, y):
    margin = 60
    return int(x * (W - 2*margin) + margin), int(y * (H - 2*margin) + margin)

# Colors
color_map = {
    "nation_1": "#4A90D9",  # Blue for Hodges
    "nation_2": "#D4A84B",  # Gold for Aksum
    "nation_3": "#8B4513",  # Brown for Urartu
    None: "#8B8B8B",        # Gray for unclaimed
}

route_color = "#8B4513"  # Brown roads
route_width = 2

# Draw routes first (behind cities)
for c1, c2 in connections:
    x1, y1 = cities[c1]["x"], cities[c1]["y"]
    x2, y2 = cities[c2]["x"], cities[c2]["y"]
    p1 = scale(x1, y1)
    p2 = scale(x2, y2)
    # Draw road as dashed line
    draw.line([p1, p2], fill=route_color, width=route_width)

# Try to load a font, fall back to default
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
except:
    font = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw cities
for city_id, city in cities.items():
    x, y = scale(city["x"], city["y"])
    owner = city.get("owner")
    color = color_map.get(owner, "#8B8B8B")
    
    # Size based on city size
    radius = 20 + city["size"] * 4
    
    # Draw city
    if city.get("is_capital"):
        # Star/circle with border
        draw.ellipse([x-radius-4, y-radius-4, x+radius+4, y+radius+4], fill="black")
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
        # Inner circle
        draw.ellipse([x-radius+5, y-radius+5, x+radius-5, y+radius-5], fill="#ffe4b5")
        # Label
        draw.text((x + radius + 8, y - 15), city["name"], fill="black", font=font)
    else:
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline="black")
        # Label
        draw.text((x + radius + 3, y - 5), city["name"], fill="black", font=font_small)

# Legend
legend_y = 30
legend = [("Hodges", "#4A90D9"), ("Aksum", "#D4A84B"), ("Urartu", "#8B4513"), ("Neutral", "#8B8B8B")]
for i, (name, color) in enumerate(legend):
    x = 30 + i * 150
    draw.ellipse([x, legend_y, x+20, legend_y+20], fill=color, outline="black")
    draw.text((x + 25, legend_y + 3), name, fill="black", font=font_small)

# Title
draw.text((W//2 - 120, H - 35), f"World Map - {len(cities)} Cities, {len(connections)} Routes", fill="black", font=font)

# Save
img.save(MAP_DIR / "world-map.png")
print(f"Saved: {MAP_DIR / 'world-map.png'}")