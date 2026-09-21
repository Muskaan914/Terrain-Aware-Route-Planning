import rasterio
import numpy as np
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

FOREST_MASK_PATH = DATA_DIR / "forest_mask.tif"
OUTPUT_PATH = DATA_DIR / "forest_cost.tif"


# ---------------------------------------------------------
# Configurable forest penalty
# ---------------------------------------------------------

FOREST_PENALTY = 0.5


# ---------------------------------------------------------
# Create forest cost
# ---------------------------------------------------------

def create_forest_cost():

    print("=" * 50)
    print("Creating forest cost layer")
    print("=" * 50)

    with rasterio.open(FOREST_MASK_PATH) as src:

        forest = src.read(1)

        profile = src.profile.copy()

        print("\nForest mask:")
        print("Width :", src.width)
        print("Height:", src.height)
        print("CRS   :", src.crs)
        print("Bounds:", src.bounds)

    # -----------------------------------------------------
    # Cost calculation
    #
    # Non-forest = 1.0
    # Forest     = 1.0 + penalty
    # -----------------------------------------------------

    forest_cost = np.ones(
        forest.shape,
        dtype=np.float32
    )

    forest_cost[forest == 1] = 1.0 + FOREST_PENALTY

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    forest_pixels = np.count_nonzero(forest == 1)
    non_forest_pixels = np.count_nonzero(forest == 0)

    print("\nForest cost results:")
    print("Non-forest pixels :", non_forest_pixels)
    print("Forest pixels     :", forest_pixels)
    print("Forest penalty    :", FOREST_PENALTY)

    print(
        "Minimum forest cost:",
        f"{forest_cost.min():.2f}"
    )

    print(
        "Maximum forest cost:",
        f"{forest_cost.max():.2f}"
    )

    print(
        "Mean forest cost   :",
        f"{forest_cost.mean():.2f}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(forest_cost, 1)

    print("\nForest cost layer created successfully!")

    print("Output file:")
    print(OUTPUT_PATH)

    print("=" * 50)


if __name__ == "__main__":
    create_forest_cost()