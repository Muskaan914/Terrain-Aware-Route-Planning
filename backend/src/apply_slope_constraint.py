import rasterio
import numpy as np
from pathlib import Path


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

BASE_COST_PATH = DATA_DIR / "final_terrain_cost_bridges.tif"
SLOPE_PATH = DATA_DIR / "slope.tif"

OUTPUT_PATH = DATA_DIR / "final_cost_slope_constrained.tif"


# =========================================================
# User constraint
# =========================================================

# Maximum allowed slope in degrees
MAX_SLOPE = 45.0

NODATA = -9999.0


# =========================================================
# Main function
# =========================================================

def apply_slope_constraint():

    print("=" * 60)
    print("MAXIMUM SLOPE CONSTRAINT")
    print("=" * 60)

    print(f"\nMaximum allowed slope: {MAX_SLOPE:.1f} degrees")

    # -----------------------------------------------------
    # Load base constrained cost
    # -----------------------------------------------------

    with rasterio.open(BASE_COST_PATH) as src:

        cost = src.read(1).astype(np.float32)

        profile = src.profile.copy()

        cost_nodata = src.nodata

    # -----------------------------------------------------
    # Load slope
    # -----------------------------------------------------

    with rasterio.open(SLOPE_PATH) as src:

        slope = src.read(1).astype(np.float32)

        slope_nodata = src.nodata

    # -----------------------------------------------------
    # Validate dimensions
    # -----------------------------------------------------

    if cost.shape != slope.shape:

        raise ValueError(
            "Cost map and slope map must have the same dimensions."
        )

    # -----------------------------------------------------
    # Identify valid cells
    # -----------------------------------------------------

    valid_cost = (
        np.isfinite(cost)
        & (cost > 0)
        & (cost != NODATA)
    )

    if cost_nodata is not None:

        valid_cost &= (
            cost != cost_nodata
        )

    valid_slope = (
        np.isfinite(slope)
        & (slope != NODATA)
    )

    if slope_nodata is not None:

        valid_slope &= (
            slope != slope_nodata
        )

    valid = valid_cost & valid_slope

    # -----------------------------------------------------
    # Find cells exceeding maximum slope
    # -----------------------------------------------------

    steep_cells = (
        slope > MAX_SLOPE
    ) & valid

    # -----------------------------------------------------
    # Apply hard constraint
    # -----------------------------------------------------

    constrained_cost = cost.copy()

    constrained_cost[
        steep_cells
    ] = NODATA

    # Preserve existing invalid cells
    constrained_cost[
        ~valid_cost
    ] = NODATA

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    usable = (
        np.isfinite(constrained_cost)
        & (constrained_cost != NODATA)
        & (constrained_cost > 0)
    )

    print("\n" + "=" * 60)
    print("SLOPE CONSTRAINT STATISTICS")
    print("=" * 60)

    print(
        "Total pixels:",
        constrained_cost.size
    )

    print(
        "Previously usable pixels:",
        np.count_nonzero(valid_cost)
    )

    print(
        "Cells above maximum slope:",
        np.count_nonzero(steep_cells)
    )

    print(
        "Usable pixels after constraint:",
        np.count_nonzero(usable)
    )

    print(
        "Blocked / invalid pixels:",
        np.count_nonzero(~usable)
    )

    print(
        "Slope range:",
        f"{np.nanmin(slope[valid_slope]):.2f}°",
        "to",
        f"{np.nanmax(slope[valid_slope]):.2f}°"
    )

    # -----------------------------------------------------
    # Cost statistics
    # -----------------------------------------------------

    if np.any(usable):

        print("\nCost range after slope constraint:")

        print(
            "Minimum:",
            f"{constrained_cost[usable].min():.3f}"
        )

        print(
            "Maximum:",
            f"{constrained_cost[usable].max():.3f}"
        )

        print(
            "Mean:",
            f"{constrained_cost[usable].mean():.3f}"
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

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

        dst.write(
            constrained_cost,
            1
        )

    print("\nSlope-constrained cost map created successfully!")

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    apply_slope_constraint()