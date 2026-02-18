#!/usr/bin/env python3

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
HISTORY_DIR = PROJECT_ROOT / "history"
OUTPUT_FILE = PROJECT_ROOT / "stats" / "network-chart.png"

COLOURS = {
    "relay": (189/255, 97/255, 87/255, 1),  # red
    "exit": (86/255, 189/255, 164/255, 1),   # green
    "guard": (87/255, 148/255, 189/255, 1),  # blue
    "all": (116/255, 87/255, 189/255, 1),  # purple
}

def count_nodes_in_file(filepath):
    """Count the number of lines (nodes) in a text file."""
    try:
        with open(filepath, 'r') as f:
            return len(f.readlines())
    except FileNotFoundError:
        return 0

def collect_data():
    """Collect node counts for each day from history directory."""
    data = defaultdict(lambda: {"relay": 0, "exit": 0, "guard": 0, "all": 0})
    
    # Find all date directories (YYYY/MM/YYYY-MM-DD pattern)
    date_dirs = sorted(HISTORY_DIR.glob("*/*/????-??-??"))
    
    for date_dir in date_dirs:
        # Extract date from path (YYYY-MM-DD)
        date_str = date_dir.name
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        
        # Count nodes for each type
        relay_file = date_dir / "relay-nodes.txt"
        exit_file = date_dir / "exit-nodes.txt"
        guard_file = date_dir / "guard-nodes.txt"
        
        relay_count = count_nodes_in_file(relay_file)
        exit_count = count_nodes_in_file(exit_file)
        guard_count = count_nodes_in_file(guard_file)
        
        data[date_obj]["relay"] = relay_count
        data[date_obj]["exit"] = exit_count
        data[date_obj]["guard"] = guard_count
        data[date_obj]["all"] = relay_count + exit_count + guard_count
        
        print(f"{date_str}: Relay={relay_count}, Exit={exit_count}, Guard={guard_count}, All={relay_count + exit_count + guard_count}")
    
    return data

def generate_chart(data):
    """Generate and save the line chart."""
    if not data:
        print("No data found!")
        return
    
    # Sort by date
    sorted_dates = sorted(data.keys())
    
    # Extract data for each line
    relay_counts = [data[d]["relay"] for d in sorted_dates]
    exit_counts = [data[d]["exit"] for d in sorted_dates]
    guard_counts = [data[d]["guard"] for d in sorted_dates]
    all_counts = [data[d]["all"] for d in sorted_dates]
    
    # Create figure and axis
    plt.figure(figsize=(14, 8))
    
    # Plot lines
    plt.plot(sorted_dates, relay_counts, color=COLOURS["relay"], label="Relay", linewidth=2.5)
    plt.plot(sorted_dates, exit_counts, color=COLOURS["exit"], label="Exit", linewidth=2.5)
    plt.plot(sorted_dates, guard_counts, color=COLOURS["guard"], label="Guard", linewidth=2.5)
    plt.plot(sorted_dates, all_counts, color=COLOURS["all"], label="All Nodes", linewidth=2.5)

    # Format the chart
    plt.ylabel("Node Count")
    plt.title("Tor Network Size Over Time")
    plt.legend(loc="best")
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely (start of each month)
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())  # Minor gridlines for weeks
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45, ha="right")
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Save chart
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    print(f"\n✓ Chart saved: {OUTPUT_FILE}")
    plt.close()

if __name__ == "__main__":
    print("Collecting Tor network data...\n")
    data = collect_data()
    
    print(f"\nTotal days tracked: {len(data)}")
    print("Generating chart...")
    generate_chart(data)
