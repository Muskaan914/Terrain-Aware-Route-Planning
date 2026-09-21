import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"


def load_dem(file_path):

    with rasterio.open(file_path) as dem:

        elevation = dem.read(1)

        metadata = {
            "width": dem.width,
            "height": dem.height,
            "crs": dem.crs,
            "transform": dem.transform,
            "resolution": dem.res,
            "bounds": dem.bounds,
            "nodata": dem.nodata,
        }

    return elevation, metadata


def print_dem_info(elevation, metadata):

    print("\n===== DEM INFORMATION =====")

    print(f"Width       : {metadata['width']} pixels")
    print(f"Height      : {metadata['height']} pixels")
    print(f"CRS         : {metadata['crs']}")
    print(f"Resolution  : {metadata['resolution']}")
    print(f"Bounds      : {metadata['bounds']}")
    print(f"NoData      : {metadata['nodata']}")

    print("\n===== ELEVATION INFORMATION =====")

    print(f"Minimum elevation : {np.nanmin(elevation):.2f}")
    print(f"Maximum elevation : {np.nanmax(elevation):.2f}")
    print(f"Mean elevation    : {np.nanmean(elevation):.2f}")

    print(f"\nDEM array shape   : {elevation.shape}")


def show_dem(elevation):

    plt.figure(figsize=(10, 7))

    plt.imshow(elevation)

    plt.colorbar(label="Elevation")

    plt.title("Digital Elevation Model")

    plt.xlabel("Column")
    plt.ylabel("Row")

    # Save figure
    FIGURE_DIR = BASE_DIR / "results" / "figures"
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FIGURE = FIGURE_DIR / "01_elevation.png"

    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()

def main():

    print("Loading DEM...")

    if not DEM_PATH.exists():

        print("\nERROR: DEM file not found.")
        print(f"Expected location: {DEM_PATH}")

        return

    elevation, metadata = load_dem(DEM_PATH)

    print_dem_info(elevation, metadata)

    show_dem(elevation)


if __name__ == "__main__":
    main()