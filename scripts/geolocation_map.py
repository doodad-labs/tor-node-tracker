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

# Aggregate nodes by country
node_by_country = df.groupby('country').size().reset_index(name='node_count')

print(f"Found {len(node_by_country)} countries with Tor nodes")
print(f"Total nodes: {node_by_country['node_count'].sum()}")

# Calculate country centroids from the world map
if worldmap is not None:
    # Create a mapping of country ISO codes to centroids
    worldmap['centroid'] = worldmap.geometry.centroid
    centroid_map = dict(zip(worldmap['ISO_A2'], worldmap['centroid']))
    
    # Map country codes to centroids
    node_by_country['geometry'] = node_by_country['country'].map(centroid_map)
    
    # Remove any countries that couldn't be mapped
    node_by_country = node_by_country.dropna(subset=['geometry'])
    
    # Extract latitude and longitude from centroids
    node_by_country['longitude'] = node_by_country['geometry'].apply(lambda geom: geom.x)
    node_by_country['latitude'] = node_by_country['geometry'].apply(lambda geom: geom.y)
    
    x = node_by_country['longitude'].values
    y = node_by_country['latitude'].values
    z = node_by_country['node_count'].values
    
    print(f"Successfully mapped {len(node_by_country)} countries to centroids")
else:
    print("Warning: Could not use country centroids without world map data")
    x = []
    y = []
    z = []

# Plot scatter points (with larger sizes for better visibility)
if len(x) > 0:
    scatter = plt.scatter(
        x, y,
        s=z * 2,            # Size proportional to number of nodes (multiplied by 2 for visibility)
        c=z,                # Color by node count
        alpha=0.7,
        cmap='autumn',
        edgecolors='darkred',
        linewidth=1,
        vmin=0,
        vmax=z.max()
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, label='Number of Nodes', ax=ax)
else:
    print("No country data to plot")

# Set axis limits and labels
plt.xlim([-180, 180])
plt.ylim([-60, 85])  # Exclude Antarctica
plt.xlabel("Longitude", fontsize=12)
plt.ylabel("Latitude", fontsize=12)
plt.title("Tor Network Node Distribution by Country\nBubble size and color represent node count per country", fontsize=14, fontweight='bold')

# Add grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig("stats/geolocation-map.png", dpi=150, bbox_inches='tight')
print("✓ Geolocation map saved to stats/geolocation-map.png")

plt.close()
