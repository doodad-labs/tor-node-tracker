#!/usr/bin/env python3
"""
Generate a world map with Tor node geolocation scatter plot.
Shows node density by country with bubble sizes representing node count.
Aggregates nodes by country and places them at country centroids.
"""

import json
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import os
import urllib.request

# Load geolocation data
with open("active/geo-location.json", "r") as f:
    geo_data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(geo_data)

# Get world map from Natural Earth dataset
try:
    cache_dir = os.path.expanduser("~/.cache/geopandas")
    zip_path = os.path.join(cache_dir, "naturalearth_lowres.zip")
    
    if os.path.exists(zip_path):
        worldmap = gpd.read_file(f"zip://{zip_path}!ne_110m_admin_0_countries.shp")
    else:
        # Fallback: download on demand
        os.makedirs(cache_dir, exist_ok=True)
        print("Downloading Natural Earth data...")
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        urllib.request.urlretrieve(url, zip_path)
        worldmap = gpd.read_file(f"zip://{zip_path}!ne_110m_admin_0_countries.shp")
except Exception as e:
    print(f"Warning: Could not load Natural Earth data: {e}")
    print("Continuing with map outline only...")
    worldmap = None

# Remove Antarctica if present
if worldmap is not None:
    # Filter out Antarctica and other polar regions
    worldmap = worldmap[~worldmap['NAME'].str.contains('Antarctica', case=False, na=False)]
    # Also filter by latitude to remove extreme southern regions
    worldmap = worldmap[worldmap.geometry.bounds['miny'] > -85]

# Create figure
fig, ax = plt.subplots(figsize=(16, 10))

# Plot world map
if worldmap is not None:
    worldmap.plot(color="lightgrey", ax=ax, edgecolor="white", linewidth=0.5)
else:
    ax.set_facecolor("#e6f2ff")

# Aggregate nodes by location (aggregate nearby points)
node_counts = df.groupby(['latitude', 'longitude']).size().reset_index(name='node_count')

print(f"Found {len(node_counts)} unique lat/lon locations with Tor nodes")
print(f"Total nodes: {node_counts['node_count'].sum()}")

# Extract coordinates
x = node_counts['longitude'].values
y = node_counts['latitude'].values
z = node_counts['node_count'].values

# Plot scatter points (with capped sizes for better visibility)
if len(x) > 0:
    # Scale and cap bubble sizes - min 10, max 50 for better visibility with many points
    bubble_sizes = z * 0.5
    bubble_sizes = bubble_sizes.clip(min=10, max=50)
    
    scatter = plt.scatter(
        x, y,
        s=bubble_sizes,      # Size between 10 and 50 for visibility
        c=z,                # Color by node count
        alpha=0.6,
        cmap='autumn',
        edgecolors='darkred',
        linewidth=0.5,
        vmin=0,
        vmax=z.max()
    )
    
    # Add colorbar with smaller size
    cbar = plt.colorbar(scatter, label='Number of Nodes', ax=ax, shrink=0.6, pad=0.02)
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label('Number of Nodes', fontsize=9)
else:
    print("No location data to plot")

# Set axis limits
plt.xlim([-180, 180])
plt.ylim([-60, 85])  # Exclude Antarctica

# Remove axis labels, title, grid, and spines for clean map
ax.set_xticks([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig("stats/geolocation-map.png", dpi=150, bbox_inches='tight')
print("✓ Geolocation map saved to stats/geolocation-map.png")

plt.close()
