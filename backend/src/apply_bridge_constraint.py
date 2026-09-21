import rasterio
import numpy as np
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_terrain_cost.tif"
WATER_PATH = DATA_DIR / "water_mask.tif"
BRIDGE_PATH = DATA_DIR / "bridge_mask.tif"

OUTPUT_PATH = DATA_DIR / "final_terrain_cost_bridges.tif"


def apply_bridge_constraint():

    print("=" * 60)
    print("APPLYING BRIDGE-AWARE WATER CONSTRAINT")
    print("=" * 60)

    # -----------------------------------------------------
    # Read final cost
    # -----------------------------------------------------

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(np.float32)
        profile = src.profile.copy()

    # -----------------------------------------------------
    # Read water
    # -----------------------------------------------------

    with rasterio.open(WATER_PATH) as src:

        water = src.read(1)

    # -----------------------------------------------------
    # Read bridges
    # -----------------------------------------------------

    with rasterio.open(BRIDGE_PATH) as src:

        bridges = src.read(1)

    # -----------------------------------------------------
    # Validate grids
    # -----------------------------------------------------

    if not (
        cost.shape == water.shape == bridges.shape
    ):
        raise ValueError(
            "Cost, water and bridge grids must match."
        )

    # -----------------------------------------------------
    # Water without bridge = blocked
    # Water with bridge = allowed
    # -----------------------------------------------------

    blocked_water = (
        (water == 1)
        &
        (bridges == 0)
    )

    bridge_water = (
        (water == 1)
        &
        (bridges == 1)
    )

    # Block water cells that don't contain a bridge
    cost[blocked_water] = -9999

    # Bridge cells are made traversable.
    # Give them a normal base traversal multiplier.
    cost[bridge_water] = 1.0

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    total_pixels = cost.size

    blocked_count = np.count_nonzero(
        blocked_water
    )

    bridge_count = np.count_nonzero(
        bridge_water
    )

    usable_count = np.count_nonzero(
        cost != -9999
    )

    print("\nResults:")
    print("Total pixels:", total_pixels)
    print("Blocked water pixels:", blocked_count)
    print("Water bridge pixels:", bridge_count)
    print("Usable pixels:", usable_count)

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

        dst.write(cost, 1)

    print("\nBridge-aware cost map created successfully!")
    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


if __name__ == "__main__":
    apply_bridge_constraint()