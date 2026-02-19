#!/usr/bin/env python3

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.constants import COLOURS
from utils.utils import count_nodes_in_file

YEAR = datetime.now().year
MONTH = datetime.now().month
DAY = datetime.now().day

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
HISTORY_DIR = PROJECT_ROOT / "history"
OUTPUT_FILE = PROJECT_ROOT / "stats" / "network-chart.png"
HISTORY_OUTPUT_FILE = HISTORY_DIR / f"{YEAR}" / f"{MONTH:02d}" / f"{YEAR}-{MONTH:02d}-{DAY:02d}" / "network-chart.png"

def read_nodes_from_file(filepath):
    """Read nodes from a text file and return as a set."""
    try:
        with open(filepath, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

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

def collect_ipv4_ipv6_data():
    """Collect IPv4 and IPv6 counts for each day from history directory."""
    data = defaultdict(lambda: {"ipv4": 0, "ipv6": 0})
    
    # Find all date directories (YYYY/MM/YYYY-MM-DD pattern)
    date_dirs = sorted(HISTORY_DIR.glob("*/*/????-??-??"))
    
    for date_dir in date_dirs:
        # Extract date from path (YYYY-MM-DD)
        date_str = date_dir.name
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        
        # Read all node files for this date
        relay_file = date_dir / "relay-nodes.txt"
        exit_file = date_dir / "exit-nodes.txt"
        guard_file = date_dir / "guard-nodes.txt"
        
        # Combine all nodes into one set (automatic deduplication)
        all_nodes = set()
        all_nodes.update(read_nodes_from_file(relay_file))
        all_nodes.update(read_nodes_from_file(exit_file))
        all_nodes.update(read_nodes_from_file(guard_file))
        
        # Separate into IPv4 and IPv6 by checking for colons
        ipv4_count = 0
        ipv6_count = 0
        
        for node in all_nodes:
            if ':' in node:
                ipv6_count += 1
            else:
                ipv4_count += 1
        
        data[date_obj]["ipv4"] = ipv4_count
        data[date_obj]["ipv6"] = ipv6_count
        
        print(f"{date_str}: IPv4={ipv4_count}, IPv6={ipv6_count}, Total={ipv4_count + ipv6_count}")
    
    return data

def generate_chart(data, ipv4_ipv6_data):
    """Generate and save the dual-chart visualization."""
    if not data or not ipv4_ipv6_data:
        print("No data found!")
        return
    
    # Sort by date
    sorted_dates = sorted(data.keys())
    
    # Extract data for each line - network chart
    relay_counts = [data[d]["relay"] for d in sorted_dates]
    exit_counts = [data[d]["exit"] for d in sorted_dates]
    guard_counts = [data[d]["guard"] for d in sorted_dates]
    all_counts = [data[d]["all"] for d in sorted_dates]
    
    # Extract data for IPv4/IPv6 chart
    ipv4_counts = [ipv4_ipv6_data[d]["ipv4"] for d in sorted_dates]
    ipv6_counts = [ipv4_ipv6_data[d]["ipv6"] for d in sorted_dates]
    
    # Create figure with two subplots (stacked vertically)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # ===== TOP CHART: Network Size =====
    # Plot lines
    ax1.plot(sorted_dates, relay_counts, color=COLOURS["relay"], label="Relay", linewidth=2.5)
    ax1.plot(sorted_dates, exit_counts, color=COLOURS["exit"], label="Exit", linewidth=2.5)
    ax1.plot(sorted_dates, guard_counts, color=COLOURS["guard"], label="Guard", linewidth=2.5)
    ax1.plot(sorted_dates, all_counts, color=COLOURS["all"], label="All Nodes", linewidth=2.5)

    # Format the chart
    ax1.set_ylabel("Node Count")
    ax1.set_title("Tor Network Size Over Time")
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.xaxis.set_minor_locator(mdates.WeekdayLocator())
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # ===== BOTTOM CHART: IPv4 vs IPv6 =====
    # Plot lines
    ax2.plot(sorted_dates, ipv4_counts, color=COLOURS["ipv4"], label="IPv4", linewidth=2.5)
    ax2.plot(sorted_dates, ipv6_counts, color=COLOURS["ipv6"], label="IPv6", linewidth=2.5)
    
    # Format the chart
    ax2.set_ylabel("Node Count")
    ax2.set_xlabel("Date")
    ax2.set_title("IPv4 vs IPv6 Growth")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis (same as top chart)
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax2.xaxis.set_minor_locator(mdates.WeekdayLocator())
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Add generated date text in bottom right of image (outside chart area)
    generated_text = f"generated: {datetime.now().strftime('%Y-%m-%d')}"
    fig.text(0.98, 0.02, generated_text, fontsize=9, ha='right', va='bottom',
            color='gray', alpha=0.7)
    
    # Save chart
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.savefig(HISTORY_OUTPUT_FILE, dpi=300, bbox_inches="tight")
    print(f"\n✓ Chart saved: {OUTPUT_FILE}")
    plt.close()

if __name__ == "__main__":
    print("Collecting Tor network data...\n")
    data = collect_data()
    
    print(f"\nTotal days tracked: {len(data)}")
    
    print("\nCollecting IPv4/IPv6 data...\n")
    ipv4_ipv6_data = collect_ipv4_ipv6_data()
    
    print(f"\nTotal days tracked for IPv4/IPv6: {len(ipv4_ipv6_data)}")
    print("Generating dual chart...")
    generate_chart(data, ipv4_ipv6_data)
