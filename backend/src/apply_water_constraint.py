import rasterio
import numpy as np
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

COST_PATH = BASE_DIR / "data" / "dem" / "terrain_cost.tif"
WATER_PATH = BASE_DIR / "data" / "dem" / "water_mask.tif"
OUTPUT_PATH = BASE_DIR / "data" / "dem" / "terrain_cost_constrained.tif"


def apply_water_constraint():

    print("Loading terrain cost...")

    with rasterio.open(COST_PATH) as cost_src:

        cost = cost_src.read(1)

        profile = cost_src.profile.copy()

        cost_shape = cost.shape
        cost_transform = cost_src.transform
        cost_crs = cost_src.crs


    print("Loading water mask...")

    with rasterio.open(WATER_PATH) as water_src:

        water = water_src.read(1)

        water_shape = water.shape
        water_transform = water_src.transform
        water_crs = water_src.crs


    # --------------------------------------------------
    # Check that both rasters use the same grid
    # --------------------------------------------------

    if cost_shape != water_shape:
        raise ValueError(
            f"Dimension mismatch: "
            f"cost={cost_shape}, water={water_shape}"
        )

    if cost_transform != water_transform:
        raise ValueError("Terrain cost and water mask transforms do not match.")

    if cost_crs != water_crs:
        raise ValueError("Terrain cost and water mask CRS do not match.")


    # --------------------------------------------------
    # Apply water constraint
    # --------------------------------------------------

    constrained_cost = cost.astype(np.float32).copy()

    water_pixels = water == 1

    # Water is a hard constraint.
    # -9999 means NoData / blocked.
    constrained_cost[water_pixels] = -9999


    # --------------------------------------------------
    # Output metadata
    # --------------------------------------------------

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=-9999,
        compress="lzw"
    )


    # --------------------------------------------------
    # Save constrained cost map
    # --------------------------------------------------

    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:

        dst.write(constrained_cost, 1)


    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    blocked_pixels = int(water_pixels.sum())

    usable_pixels = int((~water_pixels).sum())

    total_pixels = water.size

    print("\n===== WATER CONSTRAINT INFORMATION =====")

    print(f"Total pixels    : {total_pixels}")
    print(f"Blocked pixels  : {blocked_pixels}")
    print(f"Usable pixels   : {usable_pixels}")

    print("\nWater constraint applied successfully.")

    print("Output file:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    apply_water_constraint()