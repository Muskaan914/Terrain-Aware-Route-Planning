import rasterio
import numpy as np
from pathlib import Path
from rasterio.features import rasterize
from shapely.geometry import box


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

BASE_COST_PATH = DATA_DIR / "final_cost_slope_constrained.tif"

OUTPUT_PATH = DATA_DIR / "final_cost_with_no_go.tif"


# =========================================================
# Test No-Go Zone
# =========================================================
#
# IMPORTANT:
# These coordinates are only for testing.
# Later, the user will draw the no-go area on the map.
#
# Format:
# min_longitude, min_latitude,
# max_longitude, max_latitude
#
# This rectangle is placed roughly in the middle
# of the current start-to-destination region.
# =========================================================

NO_GO_MIN_LON = 77.205
NO_GO_MIN_LAT = 32.235

NO_GO_MAX_LON = 77.235
NO_GO_MAX_LAT = 32.265


NODATA = -9999.0


# =========================================================
# Main function
# =========================================================

def apply_no_go_zone():

    print("=" * 60)
    print("NO-GO / RESTRICTED ZONE")
    print("=" * 60)

    print("\nNo-Go zone:")
    print(
        f"Longitude: {NO_GO_MIN_LON} to {NO_GO_MAX_LON}"
    )
    print(
        f"Latitude : {NO_GO_MIN_LAT} to {NO_GO_MAX_LAT}"
    )

    # -----------------------------------------------------
    # Load slope-constrained cost map
    # -----------------------------------------------------

    with rasterio.open(BASE_COST_PATH) as src:

        cost = src.read(1).astype(np.float32)

        profile = src.profile.copy()

        transform = src.transform

        height = src.height
        width = src.width

        nodata = src.nodata

    # -----------------------------------------------------
    # Create rectangular no-go geometry
    # -----------------------------------------------------

    no_go_geometry = box(
        NO_GO_MIN_LON,
        NO_GO_MIN_LAT,
        NO_GO_MAX_LON,
        NO_GO_MAX_LAT
    )

    # -----------------------------------------------------
    # Rasterize no-go zone
    # -----------------------------------------------------

    no_go_mask = rasterize(
        [(no_go_geometry, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True
    )

    # -----------------------------------------------------
    # Apply hard constraint
    # -----------------------------------------------------

    constrained_cost = cost.copy()

    no_go_cells = (
        no_go_mask == 1
    )

    constrained_cost[
        no_go_cells
    ] = NODATA

    # Preserve existing invalid cells
    if nodata is not None:

        constrained_cost[
            cost == nodata
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
    print("NO-GO ZONE STATISTICS")
    print("=" * 60)

    print(
        "Total pixels:",
        constrained_cost.size
    )

    print(
        "No-Go zone pixels:",
        np.count_nonzero(no_go_cells)
    )

    print(
        "Usable pixels:",
        np.count_nonzero(usable)
    )

    print(
        "Blocked / invalid pixels:",
        np.count_nonzero(~usable)
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

    print("\nNo-Go constrained cost map created successfully!")

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    apply_no_go_zone()