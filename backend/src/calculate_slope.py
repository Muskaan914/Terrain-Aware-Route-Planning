import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from pyproj import Geod


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"
SLOPE_PATH = BASE_DIR / "data" / "dem" / "slope.tif"


# --------------------------------------------------
# Calculate slope
# --------------------------------------------------

def calculate_slope(elevation, transform, crs):

    # Pixel size in degrees
    pixel_width = transform.a
    pixel_height = abs(transform.e)

    # DEM center latitude
    center_lat = (
        transform.f + transform.e * (elevation.shape[0] / 2)
    )

    center_lon = (
        transform.c + transform.a * (elevation.shape[1] / 2)
    )

    # Convert one pixel from degrees to meters
    geod = Geod(ellps="WGS84")

    _, _, dx = geod.inv(
        center_lon,
        center_lat,
        center_lon + pixel_width,
        center_lat
    )

    _, _, dy = geod.inv(
        center_lon,
        center_lat,
        center_lon,
        center_lat + pixel_height
    )

    dx = abs(dx)
    dy = abs(dy)

    # Calculate elevation change in X and Y directions
    dz_dy, dz_dx = np.gradient(
        elevation,
        dy,
        dx
    )

    # Slope in radians
    slope_radians = np.arctan(
        np.sqrt(dz_dx ** 2 + dz_dy ** 2)
    )

    # Convert radians to degrees
    slope_degrees = np.degrees(slope_radians)

    return slope_degrees


# --------------------------------------------------
# Main program
# --------------------------------------------------

def main():

    print("Loading DEM...")

    if not DEM_PATH.exists():
        print("ERROR: DEM file not found.")
        print(f"Expected: {DEM_PATH}")
        return

    with rasterio.open(DEM_PATH) as dem:

        elevation = dem.read(1)

        transform = dem.transform
        crs = dem.crs

        profile = dem.profile.copy()

        nodata = dem.nodata

    print("DEM loaded successfully.")

    print("\nCalculating slope...")

    # Replace NoData values temporarily
    valid_mask = elevation != nodata

    elevation_float = elevation.astype(float)

    elevation_float[~valid_mask] = np.nan

    slope = calculate_slope(
        elevation_float,
        transform,
        crs
    )

    # Restore NoData
    slope[~valid_mask] = -9999

    print("Slope calculation completed.")

    # --------------------------------------------------
    # Print slope statistics
    # --------------------------------------------------

    valid_slope = slope[slope != -9999]

    print("\n===== SLOPE INFORMATION =====")

    print(f"Minimum slope : {np.min(valid_slope):.2f} degrees")
    print(f"Maximum slope : {np.max(valid_slope):.2f} degrees")
    print(f"Mean slope    : {np.mean(valid_slope):.2f} degrees")

    # --------------------------------------------------
    # Save slope GeoTIFF
    # --------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=-9999
    )

    with rasterio.open(SLOPE_PATH, "w", **profile) as dst:

        dst.write(
            slope.astype(rasterio.float32),
            1
        )

    print(f"\nSlope saved to:")
    print(SLOPE_PATH)

    # --------------------------------------------------
    # Display slope map
    # --------------------------------------------------

    display_slope = slope.copy()

    display_slope[display_slope == -9999] = np.nan

    plt.figure(figsize=(10, 7))

    plt.imshow(display_slope)

    plt.colorbar(label="Slope (degrees)")

    plt.title("Terrain Slope")

    plt.xlabel("Column")
    plt.ylabel("Row")

    # --------------------------------------------------
    # Save slope figure
    # --------------------------------------------------

    FIGURE_DIR = BASE_DIR / "results" / "figures"
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FIGURE = FIGURE_DIR / "02_slope.png"

    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()


if __name__ == "__main__":
    main()