import rasterio
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"
ROAD_COST_PATH = BASE_DIR / "data" / "dem" / "road_cost.tif"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("Loading DEM and road cost data...")

    # Read DEM
    with rasterio.open(DEM_PATH) as dem_src:

        elevation = dem_src.read(1).astype(float)

        dem_nodata = dem_src.nodata

        bounds = dem_src.bounds


    # Read road cost
    with rasterio.open(ROAD_COST_PATH) as road_src:

        road_cost = road_src.read(1).astype(float)


    # Remove DEM NoData
    if dem_nodata is not None:

        elevation[elevation == dem_nodata] = np.nan


    # Hide non-road pixels
    road_display = road_cost.copy()

    road_display[road_display <= 0] = np.nan


    # --------------------------------------------------
    # Create figure
    # --------------------------------------------------

    plt.figure(figsize=(12, 8))

    plt.imshow(
        elevation,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="terrain"
    )


    plt.imshow(
        road_display,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="viridis",
        alpha=0.75
    )


    plt.colorbar(
        label="Road Preference Cost"
    )


    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.title(
        "Manali Terrain with OpenStreetMap Road Preference"
    )


    plt.tight_layout()


    # --------------------------------------------------
    # Save figure
    # --------------------------------------------------

    FIGURE_DIR = BASE_DIR / "results" / "figures"

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FIGURE = (
        FIGURE_DIR / "06_roads.png"
    )


    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )


    print()
    print("Figure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")


    plt.show()


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    main()