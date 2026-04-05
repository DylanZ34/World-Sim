#!/usr/bin/env python3
"""World Map Generator.

Generates a world map as a fully connected graph of cities.
Each city has 2-5 connections.

Usage:
    python3 generate_map.py [num_cities] [seed_cities...]
    
Examples:
    python3 generate_map.py                       # 10 cities, default 3 seeds
    python3 generate_map.py 15                     # 15 cities, default seeds
    python3 generate_map.py 12 Hodges,Aksum,Urartu  # 12 cities, named seeds
"""

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1].parent
MAP_OUTPUT_DIR = ROOT / "world" / "map"


def parse_args():
    """Parse command line arguments."""
    num_cities = 10
    seed_names = ["Hodges", "Aksum", "Urartu"]
    
    if len(sys.argv) > 1:
        try:
            num_cities = int(sys.argv[1])
        except ValueError:
            print(f"Invalid num_cities: {sys.argv[1]}, using default 10")
    
    if len(sys.argv) > 2:
        seed_names = sys.argv[2].split(",")
    
    return num_cities, seed_names


def generate_city_name(index: int, is_seed: bool, seed_name: str = None) -> str:
    """Generate a city name."""
    if is_seed and seed_name:
        return f"{seed_name} Capital"
    
    prefixes = ["Port", "Fort", "Lake", "River", "Mountain", "Valley", "Coast", "Bay", "Plain", "Canyon"]
    suffixes = ["ville", "burg", "ton", "ford", "haven", "port", "crest", "vale", "hold", "watch"]
    
    return f"{random.choice(prefixes)}{random.choice(suffixes)}"


def distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Calculate Euclidean distance."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def generate_map(num_cities: int, seed_names: list[str]) -> dict[str, Any]:
    """Generate a world map as a graph."""
    print(f"=== Generating world map: {num_cities} cities, seeds: {seed_names} ===")
    
    # Initialize
    cities = {}
    num_seeds = len(seed_names)
    
    # Place seed cities far apart (corners of a polygon)
    for i, seed_name in enumerate(seed_names):
        angle = 2 * math.pi * i / num_seeds - math.pi / 2
        x = 0.5 + 0.4 * math.cos(angle)  # Keep away from edges
        y = 0.5 + 0.4 * math.sin(angle)
        
        city_id = f"city_{i}"
        cities[city_id] = {
            "id": city_id,
            "name": f"{seed_name} Capital",
            "x": x,
            "y": y,
            "is_capital": True,
            "owner": f"nation_{i + 1}",
            "size": random.randint(5, 7),
            "fortification": random.randint(3, 6)
        }
    
    # Place other cities randomly but not too close to seeds
    for i in range(num_seeds, num_cities):
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.uniform(0.1, 0.9)
            y = random.uniform(0.1, 0.9)
            
            # Check distance from all existing cities
            too_close = False
            for other in cities.values():
                if distance((x, y), (other["x"], other["y"])) < 0.15:
                    too_close = True
                    break
            
            if not too_close:
                city_id = f"city_{i}"
                cities[city_id] = {
                    "id": city_id,
                    "name": generate_city_name(i, False),
                    "x": x,
                    "y": y,
                    "is_capital": False,
                    "owner": None,
                    "size": random.randint(3, 6),
                    "fortification": random.randint(1, 4)
                }
                break
        else:
            # Fallback: place at random
            city_id = f"city_{i}"
            cities[city_id] = {
                "id": city_id,
                "name": generate_city_name(i, False),
                "x": random.uniform(0.1, 0.9),
                "y": random.uniform(0.1, 0.9),
                "is_capital": False,
                "owner": None,
                "size": random.randint(3, 6),
                "fortification": random.randint(1, 4)
            }
    
    # Generate connections (each city 2-5 connections, fully connected graph structure)
    connections = []
    city_ids = list(cities.keys())
    
    # First, ensure connectivity (connect to nearest neighbors)
    for city_id in city_ids:
        city = cities[city_id]
        distances = [(other_id, distance((city["x"], city["y"]), (cities[other_id]["x"], cities[other_id]["y"]))) 
                     for other_id in city_ids if other_id != city_id]
        distances.sort(key=lambda x: x[1])
        
        # Connect to 2 nearest
        for other_id, _ in distances[:2]:
            edge = tuple(sorted([city_id, other_id]))
            if edge not in connections:
                connections.append(edge)
    
    # Then add random connections to reach 2-5 per city
    for city_id in city_ids:
        current_connections = sum(1 for c in connections if city_id in c)
        target = random.randint(2, 5)
        
        while current_connections < target:
            other_id = random.choice([c for c in city_ids if c != city_id])
            edge = tuple(sorted([city_id, other_id]))
            
            if edge not in connections:
                connections.append(edge)
                current_connections += 1
    
    # Build graph
    graph = {
        "cities": cities,
        "connections": connections,
        "num_cities": num_cities,
        "num_seeds": num_seeds,
        "seed_names": seed_names
    }
    
    return graph


def generate_dot(graph: dict[str, Any]) -> str:
    """Generate DOT format for graphviz."""
    lines = [
        "graph world_map {",
        '  layout="neato";',
        '  overlap=false;',
        '  splines=true;',
        "",
        '  node [shape=circle, style=filled, fontname="Arial"];',
    ]
    
    # Define colors for capitals
    color_map = {
        "nation_1": "#4A90D9",  # Blue for Hodges
        "nation_2": "#D4A84B",  # Gold for Aksum
        "nation_3": "#8B4513",  # Brown for Urartu
        None: "#CCCCCC",        # Gray for unclaimed
    }
    
    # Add nodes
    for city_id, city in graph["cities"].items():
        owner = city.get("owner")
        color = color_map.get(owner, "#CCCCCC")
        
        # Capital gets larger size
        if city.get("is_capital"):
            size = "45"
            label = f'{city["name"]}\\n({city["size"]}/{city["fortification"]})'
        else:
            size = "30"
            label = f'{city["name"]}\\n({city["size"]}/{city["fortification"]})'
        
        lines.append(f'  "{city_id}" [label="{label}", fillcolor="{color}", width={size}, fontsize=10];')
    
    lines.append("")
    
    # Add edges
    for c1, c2 in graph["connections"]:
        lines.append(f'  "{c1}" -- "{c2}" [len=2];')
    
    lines.append("}")
    
    return "\n".join(lines)


def main():
    num_cities, seed_names = parse_args()
    
    # Generate map
    graph = generate_map(num_cities, seed_names)
    
    # Create output directory
    MAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = MAP_OUTPUT_DIR / "world-map.json"
    with open(json_path, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"  ✓ Saved JSON to {json_path}")
    
    # Save DOT
    dot_path = MAP_OUTPUT_DIR / "world-map.dot"
    dot_content = generate_dot(graph)
    with open(dot_path, "w") as f:
        f.write(dot_content)
    print(f"  ✓ Saved DOT to {dot_path}")
    
    # Try to generate PNG
    try:
        import subprocess
        result = subprocess.run(
            ["dot", "-Tpng", str(dot_path), "-o", str(MAP_OUTPUT_DIR / "world-map.png")],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✓ Generated PNG to {MAP_OUTPUT_DIR / 'world-map.png'}")
        else:
            print(f"  ! dot command failed (install graphviz to generate PNG)")
            print(f"    Run: sudo apt install graphviz")
    except FileNotFoundError:
        print(f"  ! graphviz not installed (dot command not found)")
        print(f"    Run: sudo apt install graphviz")
    
    print(f"\n=== Map Generated ===")
    print(f"Cities: {len(graph['cities'])}")
    print(f"Connections: {len(graph['connections'])}")
    print(f"Capitals: {', '.join(seed_names)}")


if __name__ == "__main__":
    main()