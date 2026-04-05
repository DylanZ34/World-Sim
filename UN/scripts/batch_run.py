#!/usr/bin/env python3
"""Batch run - runs multiple turns sequentially."""

import subprocess
import sys

# Simple batch runner - calls run_discord_turn.py directly
def main():
    # Only takes one argument for turns
    num_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print(f"=== Batch Run: {num_turns} turns ===")
    
    for i in range(num_turns):
        print(f"--- Turn {i+1} ---")
        result = subprocess.run(
            ["python3", "UN/scripts/run_discord_turn.py"],
            capture_output=True, text=True, cwd="/home/bzh/World-Sim"
        )
        if result.returncode != 0:
            print(f"Turn {i+1} failed: {result.stderr[:200]}")
            break
        # Print the summary line
        for line in result.stdout.split('\n')[-5:]:
            if 'done' in line.lower() or 'effects' in line.lower():
                print(f"  {line}")
    
    print(f"\n=== Batch Complete ===")

if __name__ == "__main__":
    main()