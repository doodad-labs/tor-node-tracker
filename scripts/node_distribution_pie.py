#!/usr/bin/env python3

import os
from pathlib import Path
import matplotlib.pyplot as plt

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ACTIVE_DIR = PROJECT_ROOT / "active"
OUTPUT_FILE = PROJECT_ROOT / "stats" / "node-distribution-pie.png"

# Colors with 60% opacity (alpha=1)
COLOURS = {
    "relay": (189/255, 97/255, 87/255, 1),  # red
    "exit": (86/255, 189/255, 164/255, 1),   # green
    "guard": (87/255, 148/255, 189/255, 1),  # blue
}

def count_nodes_in_file(filepath):
    """Count the number of lines (nodes) in a text file."""
    try:
        with open(filepath, 'r') as f:
            return len(f.readlines())
    except FileNotFoundError:
        return 0

def generate_pie_chart():
    """Generate and save the pie chart."""
    # Count nodes for each type
    relay_file = ACTIVE_DIR / "relay-nodes.txt"
    exit_file = ACTIVE_DIR / "exit-nodes.txt"
    guard_file = ACTIVE_DIR / "guard-nodes.txt"
    
    relay_count = count_nodes_in_file(relay_file)
    exit_count = count_nodes_in_file(exit_file)
    guard_count = count_nodes_in_file(guard_file)
    
    print(f"Node counts:")
    print(f"  Relay: {relay_count}")
    print(f"  Exit:  {exit_count}")
    print(f"  Guard: {guard_count}")
    print(f"  Total: {relay_count + exit_count + guard_count}\n")
    
    # Prepare data
    sizes = [relay_count, exit_count, guard_count]
    labels = ["Relay", "Exit", "Guard"]
    colors_list = [COLOURS["relay"], COLOURS["exit"], COLOURS["guard"]]
    
    # Create figure and axis
    plt.figure(figsize=(10, 8))
    
    # Create pie chart
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        colors=colors_list,
        autopct="%1.1f%%",
        startangle=90,
    )
    
    # Enhance autotext (percentage labels)
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")
    
    # Add title
    plt.title("Tor Network Node Distribution", pad=20)
    
    # Add legend with counts
    legend_labels = [
        f"Relay: {relay_count:,}",
        f"Exit: {exit_count:,}",
        f"Guard: {guard_count:,}"
    ]
    plt.legend(legend_labels, loc="upper left", bbox_to_anchor=(0.85, 1))
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis("equal")
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Save chart
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    print(f"✓ Pie chart saved: {OUTPUT_FILE}")
    plt.close()

if __name__ == "__main__":
    print("Generating Tor network node distribution pie chart...\n")
    generate_pie_chart()
