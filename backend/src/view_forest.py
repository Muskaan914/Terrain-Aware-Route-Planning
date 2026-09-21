import rasterio
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

DEM_PATH = DATA_DIR / "sample_dem.tif"
FOREST_PATH = DATA_DIR / "forest_mask.tif"


def view_forest():

    # Read DEM
    with rasterio.open(DEM_PATH) as dem_src:
        elevation = dem_src.read(1).astype(float)
        dem_nodata = dem_src.nodata
        bounds = dem_src.bounds

    # Read forest mask
    with rasterio.open(FOREST_PATH) as forest_src:
        forest = forest_src.read(1)

    # Remove DEM NoData from visualization
    if dem_nodata is not None:
        elevation[elevation == dem_nodata] = np.nan

    # Create plot
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

    # Forest pixels
    forest_display = np.where(
        forest == 1,
        1,
        np.nan
    )

    plt.imshow(
        forest_display,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="Greens",
        alpha=0.45
    )

    plt.colorbar(label="Elevation (m)")

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Manali Terrain with Forest / Tree Cover")

    plt.tight_layout()

    # --------------------------------------------------
    # Save figure
    # --------------------------------------------------

    FIGURE_DIR = BASE_DIR / "results" / "figures"
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FIGURE = FIGURE_DIR / "05_forest.png"

    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()


if __name__ == "__main__":
    view_forest()