import rasterio
import numpy as np
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

BASE_COST_PATH = DATA_DIR / "final_cost_slope_constrained.tif"
NO_GO_PATH = DATA_DIR / "no_go_mask.tif"

OUTPUT_PATH = DATA_DIR / "final_cost_slope_nogo.tif"


# ============================================================
# NODATA VALUE
# ============================================================

NODATA = -9999


# ============================================================
# APPLY NO-GO CONSTRAINT
# ============================================================

def apply_no_go_constraint():

    print("Loading slope-constrained terrain cost...")
    
    with rasterio.open(BASE_COST_PATH) as src:
        cost = src.read(1).astype(float)
        profile = src.profile.copy()

    print("Loading No-Go mask...")

    with rasterio.open(NO_GO_PATH) as src:
        no_go = src.read(1)

    # Check dimensions
    if cost.shape != no_go.shape:
        raise ValueError(
            f"Dimension mismatch: cost={cost.shape}, "
            f"no_go={no_go.shape}"
        )

    # Existing invalid cells
    invalid_before = cost == NODATA

    # Apply No-Go Zone as hard constraint
    no_go_cells = no_go == 1
    cost[no_go_cells] = NODATA

    # Preserve existing invalid cells
    cost[invalid_before] = NODATA

    # Update metadata
    profile.update(
        dtype="float32",
        nodata=NODATA,
        compress="lzw"
    )

    # Save output
    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.write(cost.astype("float32"), 1)

    # ========================================================
    # STATISTICS
    # ========================================================

    total_pixels = cost.size
    blocked_pixels = np.sum(cost == NODATA)
    usable_pixels = np.sum(cost != NODATA)

    print("\nNO-GO CONSTRAINT APPLIED")
    print("--------------------------------")
    print(f"Total pixels       : {total_pixels}")
    print(f"Blocked/invalid    : {blocked_pixels}")
    print(f"Usable pixels      : {usable_pixels}")
    print(f"No-Go cells        : {np.sum(no_go_cells)}")

    valid_cost = cost[cost != NODATA]

    if valid_cost.size > 0:
        print(f"Cost minimum       : {valid_cost.min():.3f}")
        print(f"Cost maximum       : {valid_cost.max():.3f}")
        print(f"Cost mean          : {valid_cost.mean():.3f}")

    print("\nSaved to:")
    print(OUTPUT_PATH)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    apply_no_go_constraint()