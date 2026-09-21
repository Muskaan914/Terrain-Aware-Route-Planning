import rasterio
import numpy as np
from pathlib import Path


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_terrain_cost.tif"
WATER_PATH = DATA_DIR / "water_mask.tif"
BRIDGE_PATH = DATA_DIR / "bridge_mask.tif"

OUTPUT_PATH = DATA_DIR / "final_terrain_cost_constrained.tif"


# =========================================================
# Main
# =========================================================

def apply_constraint():

    print("=" * 60)
    print("APPLYING WATER + BRIDGE CONSTRAINT")
    print("=" * 60)

    # -----------------------------------------------------
    # Load cost
    # -----------------------------------------------------

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(np.float32)

        profile = src.profile.copy()

        original_nodata = src.nodata

    # -----------------------------------------------------
    # Load water
    # -----------------------------------------------------

    with rasterio.open(WATER_PATH) as src:

        water = src.read(1).astype(np.uint8)

    # -----------------------------------------------------
    # Load bridge
    # -----------------------------------------------------

    with rasterio.open(BRIDGE_PATH) as src:

        bridge = src.read(1).astype(np.uint8)

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    if (
        cost.shape != water.shape
        or
        cost.shape != bridge.shape
    ):

        raise ValueError(
            "Cost, water and bridge rasters "
            "must have identical dimensions."
        )

    # -----------------------------------------------------
    # Water without bridge = blocked
    #
    # Water + bridge = allowed
    # -----------------------------------------------------

    blocked = (
        (water == 1)
        &
        (bridge == 0)
    )

    cost[blocked] = -9999

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    water_pixels = np.count_nonzero(
        water == 1
    )

    bridge_pixels = np.count_nonzero(
        bridge == 1
    )

    blocked_pixels = np.count_nonzero(
        blocked
    )

    allowed_bridge_pixels = np.count_nonzero(
        (water == 1) & (bridge == 1)
    )

    usable_pixels = np.count_nonzero(
        cost != -9999
    )

    print("\nStatistics:")

    print(
        "Water pixels:",
        water_pixels
    )

    print(
        "Bridge pixels:",
        bridge_pixels
    )

    print(
        "Blocked water pixels:",
        blocked_pixels
    )

    print(
        "Water + bridge pixels allowed:",
        allowed_bridge_pixels
    )

    print(
        "Usable pixels:",
        usable_pixels
    )

    print(
        "Total pixels:",
        cost.size
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=-9999,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(
            cost,
            1
        )

    print(
        "\nConstrained cost map created successfully!"
    )

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


if __name__ == "__main__":
    apply_constraint()