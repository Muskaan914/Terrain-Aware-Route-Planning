import json
import rasterio
import numpy as np

from pathlib import Path
from shapely.geometry import LineString
from rasterio.features import rasterize


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

ROADS_PATH = DATA_DIR / "roads_osm.json"
DEM_PATH = DATA_DIR / "sample_dem.tif"

OUTPUT_PATH = DATA_DIR / "bridge_mask.tif"


# =========================================================
# Main
# =========================================================

def create_bridge_mask():

    print("=" * 60)
    print("CREATING BRIDGE MASK")
    print("=" * 60)

    # -----------------------------------------------------
    # Load DEM
    # -----------------------------------------------------

    with rasterio.open(DEM_PATH) as dem:

        height = dem.height
        width = dem.width
        transform = dem.transform
        crs = dem.crs
        profile = dem.profile.copy()

        print("\nDEM:")
        print("Width :", width)
        print("Height:", height)
        print("CRS   :", crs)
        print("Bounds:", dem.bounds)

    # -----------------------------------------------------
    # Load OSM roads
    # -----------------------------------------------------

    with open(
        ROADS_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    elements = data.get("elements", [])

    print("\nTotal OSM elements:", len(elements))

    # -----------------------------------------------------
    # Extract bridges
    # -----------------------------------------------------

    bridge_geometries = []

    for element in elements:

        tags = element.get("tags", {})

        if "bridge" not in tags:
            continue

        geometry = element.get("geometry", [])

        coordinates = []

        for point in geometry:

            lon = point.get("lon")
            lat = point.get("lat")

            if lon is not None and lat is not None:

                coordinates.append(
                    (lon, lat)
                )

        # Need at least two points for a line
        if len(coordinates) >= 2:

            try:

                line = LineString(
                    coordinates
                )

                bridge_geometries.append(
                    line
                )

            except Exception as e:

                print(
                    "Skipping bridge:",
                    element.get("id"),
                    e
                )

    print(
        "Valid bridge geometries:",
        len(bridge_geometries)
    )

    # -----------------------------------------------------
    # Rasterize bridges
    # -----------------------------------------------------

    bridge_mask = rasterize(
        [
            (geometry, 1)
            for geometry in bridge_geometries
        ],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True
    )

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    bridge_pixels = np.count_nonzero(
        bridge_mask == 1
    )

    print("\nBridge pixels:", bridge_pixels)

    print(
        "Total pixels:",
        bridge_mask.size
    )

    print(
        "Bridge coverage:",
        f"{bridge_pixels / bridge_mask.size * 100:.3f}%"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(
            bridge_mask,
            1
        )

    print("\nBridge mask created successfully!")

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


if __name__ == "__main__":
    create_bridge_mask()