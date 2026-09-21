import rasterio
import numpy as np
from pathlib import Path


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

DIFFICULTY_PATH = DATA_DIR / "terrain_difficulty.tif"
FOREST_PATH = DATA_DIR / "forest_mask.tif"
ROAD_COST_PATH = DATA_DIR / "road_cost.tif"

OUTPUT_PATH = DATA_DIR / "final_terrain_cost.tif"


# =========================================================
# Model parameters
# =========================================================

TERRAIN_WEIGHT = 0.60
FOREST_WEIGHT = 0.20
ROAD_WEIGHT = 0.20

MAX_PENALTY = 4.0

NODATA = -9999.0


# =========================================================
# Main function
# =========================================================

def create_final_cost_map():

    print("=" * 60)
    print("FINAL MULTI-FACTOR TERRAIN COST MAP")
    print("=" * 60)

    # -----------------------------------------------------
    # Read terrain difficulty
    # -----------------------------------------------------

    with rasterio.open(DIFFICULTY_PATH) as src:

        difficulty = src.read(1).astype(np.float32)

        profile = src.profile.copy()

        reference_shape = difficulty.shape

        print("\nTerrain difficulty:")
        print("Shape:", difficulty.shape)
        print(
            "Range:",
            f"{np.nanmin(difficulty):.3f}",
            "to",
            f"{np.nanmax(difficulty):.3f}"
        )

    # -----------------------------------------------------
    # Read forest mask
    # -----------------------------------------------------

    with rasterio.open(FOREST_PATH) as src:

        forest = src.read(1).astype(np.float32)

        print("\nForest layer:")
        print("Shape:", forest.shape)
        print(
            "Forest pixels:",
            np.count_nonzero(forest == 1)
        )

    # -----------------------------------------------------
    # Read road cost
    # -----------------------------------------------------

    with rasterio.open(ROAD_COST_PATH) as src:

        road_cost = src.read(1).astype(np.float32)

        print("\nRoad layer:")
        print("Shape:", road_cost.shape)

    # =====================================================
    # Validate dimensions
    # =====================================================

    if (
        forest.shape != reference_shape
        or road_cost.shape != reference_shape
    ):
        raise ValueError(
            "All raster layers must have the same dimensions."
        )

    # =====================================================
    # Handle invalid / NoData cells
    # =====================================================

    terrain_valid = (
        np.isfinite(difficulty)
        & (difficulty != NODATA)
    )

    forest_valid = np.isfinite(forest)
    road_valid = np.isfinite(road_cost)

    valid = (
        terrain_valid
        & forest_valid
        & road_valid
    )

    # =====================================================
    # Normalize / prepare factors
    # =====================================================

    # -----------------------------------------------------
    # 1. Terrain difficulty
    #
    # Already normalized between 0 and 1
    # -----------------------------------------------------

    terrain_factor = np.zeros(
        reference_shape,
        dtype=np.float32
    )

    terrain_factor[terrain_valid] = np.clip(
        difficulty[terrain_valid],
        0,
        1
    )

    # -----------------------------------------------------
    # 2. Forest
    #
    # 0 = no tree cover
    # 1 = tree cover
    # -----------------------------------------------------

    forest_factor = np.zeros(
        reference_shape,
        dtype=np.float32
    )

    forest_factor[forest == 1] = 1.0

    # -----------------------------------------------------
    # 3. Road preference
    #
    # Lower road_cost = better road
    # Higher road_cost = less preferred road/path
    #
    # Non-road pixels receive maximum road penalty.
    # -----------------------------------------------------

    road_factor = np.ones(
        reference_shape,
        dtype=np.float32
    )

    road_pixels = (
        (road_cost > 0)
        & road_valid
    )

    if np.any(road_pixels):

        min_road = np.min(
            road_cost[road_pixels]
        )

        max_road = np.max(
            road_cost[road_pixels]
        )

        if max_road > min_road:

            normalized_road = (
                (road_cost - min_road)
                / (max_road - min_road)
            )

        else:

            normalized_road = np.zeros(
                reference_shape,
                dtype=np.float32
            )

        # Better road -> smaller penalty
        road_factor[road_pixels] = (
            normalized_road[road_pixels]
        )

        # No road -> maximum road penalty
        road_factor[~road_pixels] = 1.0

    else:

        print("\nWARNING: No road pixels found.")

    # =====================================================
    # Weighted terrain model
    # =====================================================

    combined_factor = (
        TERRAIN_WEIGHT * terrain_factor
        +
        FOREST_WEIGHT * forest_factor
        +
        ROAD_WEIGHT * road_factor
    )

    # =====================================================
    # Final traversal multiplier
    #
    # Cost range is approximately 1 to 5
    # =====================================================

    final_cost = (
        1.0
        +
        MAX_PENALTY * combined_factor
    )

    final_cost = final_cost.astype(
        np.float32
    )

    # =====================================================
    # IMPORTANT:
    #
    # DO NOT APPLY WATER CONSTRAINT HERE.
    #
    # Water is handled separately by:
    # apply_final_constraints.py
    #
    # Permanent water -> hard constraint
    # Rivers/streams -> crossing penalty
    # Bridges -> allow crossing
    # =====================================================

    # Invalid cells remain NoData
    final_cost[~valid] = NODATA

    # =====================================================
    # Statistics
    # =====================================================

    usable = (
        np.isfinite(final_cost)
        & (final_cost != NODATA)
        & (final_cost > 0)
    )

    print("\n" + "=" * 60)
    print("FINAL COST STATISTICS")
    print("=" * 60)

    if np.any(usable):

        print(
            "Minimum cost:",
            f"{final_cost[usable].min():.3f}"
        )

        print(
            "Maximum cost:",
            f"{final_cost[usable].max():.3f}"
        )

        print(
            "Mean cost:",
            f"{final_cost[usable].mean():.3f}"
        )

    print(
        "Blocked / invalid pixels:",
        np.count_nonzero(~usable)
    )

    print(
        "Usable pixels:",
        np.count_nonzero(usable)
    )

    print(
        "Total pixels:",
        final_cost.size
    )

    # =====================================================
    # Save final base cost map
    # =====================================================

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=NODATA,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(final_cost, 1)

    print("\nFinal terrain cost map created successfully!")

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    create_final_cost_map()