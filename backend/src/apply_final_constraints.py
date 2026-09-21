import rasterio
import numpy as np
from pathlib import Path


BASE_COST = Path("data/dem/final_terrain_cost.tif")
PERMANENT_WATER = Path("data/dem/permanent_water_mask.tif")
RIVER_COST = Path("data/dem/river_cost.tif")
BRIDGE_MASK = Path("data/dem/bridge_mask.tif")

OUTPUT = Path("data/dem/final_terrain_cost_constrained.tif")

NODATA = -9999.0


print("=" * 60)
print("BUILDING FINAL CONSTRAINED COST MAP")
print("=" * 60)


# ------------------------------------------------------------
# Load base cost map
# ------------------------------------------------------------
with rasterio.open(BASE_COST) as src:
    cost = src.read(1).astype(np.float32)
    profile = src.profile.copy()

# ------------------------------------------------------------
# Load permanent water
# ------------------------------------------------------------
with rasterio.open(PERMANENT_WATER) as src:
    permanent_water = src.read(1)

# ------------------------------------------------------------
# Load river / stream cost
# ------------------------------------------------------------
with rasterio.open(RIVER_COST) as src:
    river_cost = src.read(1).astype(np.float32)

# ------------------------------------------------------------
# Load bridge mask
# ------------------------------------------------------------
with rasterio.open(BRIDGE_MASK) as src:
    bridge = src.read(1)


# ------------------------------------------------------------
# Identify valid cells
# ------------------------------------------------------------
valid = (
    np.isfinite(cost)
    & (cost > 0)
    & (cost != NODATA)
)


# ------------------------------------------------------------
# Add river / stream crossing penalty
# ------------------------------------------------------------
RIVER_WEIGHT = 1.0

river_cells = river_cost > 0

cost[river_cells & valid] += (
    RIVER_WEIGHT * river_cost[river_cells & valid]
)


# ------------------------------------------------------------
# Bridges should not receive river penalty
# ------------------------------------------------------------
bridge_cells = bridge == 1

cost[bridge_cells & valid] = (
    cost[bridge_cells & valid]
    - RIVER_WEIGHT * river_cost[bridge_cells & valid]
)

# Make sure costs never become less than 1
cost[valid] = np.maximum(cost[valid], 1.0)


# ------------------------------------------------------------
# Hard constraint:
# Permanent water is completely blocked
# ------------------------------------------------------------
blocked = (permanent_water == 1) & valid

cost[blocked] = NODATA


# ------------------------------------------------------------
# Remove invalid / original NoData cells
# ------------------------------------------------------------
cost[~valid] = NODATA


# ------------------------------------------------------------
# Statistics
# ------------------------------------------------------------
usable = cost != NODATA

print()
print("Final constraint statistics:")
print(f"Permanent water pixels: {np.sum(permanent_water == 1)}")
print(f"River/stream pixels: {np.sum(river_cost > 0)}")
print(f"Bridge pixels: {np.sum(bridge == 1)}")
print(f"Blocked pixels: {np.sum(blocked)}")
print(f"Usable pixels: {np.sum(usable)}")
print(f"Total pixels: {cost.size}")

if np.any(usable):
    print()
    print("Cost range on usable cells:")
    print(f"Minimum: {cost[usable].min():.3f}")
    print(f"Maximum: {cost[usable].max():.3f}")
    print(f"Mean: {cost[usable].mean():.3f}")


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------
profile.update(
    dtype="float32",
    nodata=NODATA,
    compress="lzw"
)

with rasterio.open(OUTPUT, "w", **profile) as dst:
    dst.write(cost, 1)


print()
print("Final constrained cost map created successfully!")
print("Output:")
print(OUTPUT.resolve())
print("=" * 60)