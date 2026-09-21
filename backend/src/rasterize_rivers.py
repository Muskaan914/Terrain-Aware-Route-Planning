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

WATER_PATH = DATA_DIR / "water_osm.json"
DEM_PATH = DATA_DIR / "sample_dem.tif"

OUTPUT_PATH = DATA_DIR / "river_cost.tif"


# =========================================================
# Crossing penalties
# =========================================================

STREAM_COST = 0.5
RIVER_COST = 1.0
DRAIN_COST = 0.3


# =========================================================
# Main
# =========================================================

def create_river_cost():

    print("=" * 60)
    print("CREATING RIVER / STREAM CROSSING COST")
    print("=" * 60)

    # -----------------------------------------------------
    # Load DEM
    # -----------------------------------------------------

    with rasterio.open(DEM_PATH) as dem:

        height = dem.height
        width = dem.width
        transform = dem.transform
        profile = dem.profile.copy()

        print("\nDEM:")
        print("Width :", width)
        print("Height:", height)
        print("CRS   :", dem.crs)
        print("Bounds:", dem.bounds)

    # -----------------------------------------------------
    # Load water data
    # -----------------------------------------------------

    with open(
        WATER_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    elements = data.get("elements", [])

    print(
        "\nTotal water elements:",
        len(elements)
    )

    # -----------------------------------------------------
    # Separate waterways
    # -----------------------------------------------------

    stream_geometries = []
    river_geometries = []
    drain_geometries = []

    for element in elements:

        tags = element.get("tags", {})

        waterway = tags.get("waterway")

        if waterway not in {
            "stream",
            "river",
            "drain"
        }:
            continue

        geometry = element.get(
            "geometry",
            []
        )

        coordinates = []

        for point in geometry:

            lon = point.get("lon")
            lat = point.get("lat")

            if lon is not None and lat is not None:

                coordinates.append(
                    (lon, lat)
                )

        if len(coordinates) < 2:
            continue

        try:

            line = LineString(
                coordinates
            )

            if line.is_empty:
                continue

            if waterway == "stream":

                stream_geometries.append(line)

            elif waterway == "river":

                river_geometries.append(line)

            elif waterway == "drain":

                drain_geometries.append(line)

        except Exception as e:

            print(
                "Skipping element:",
                element.get("id"),
                e
            )

    print("\nValid waterways:")

    print(
        "Streams:",
        len(stream_geometries)
    )

    print(
        "Rivers:",
        len(river_geometries)
    )

    print(
        "Drains:",
        len(drain_geometries)
    )

    # -----------------------------------------------------
    # Create separate masks
    # -----------------------------------------------------

    stream_mask = rasterize(
        [
            (geometry, 1)
            for geometry in stream_geometries
        ],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True
    )

    river_mask = rasterize(
        [
            (geometry, 1)
            for geometry in river_geometries
        ],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True
    )

    drain_mask = rasterize(
        [
            (geometry, 1)
            for geometry in drain_geometries
        ],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True
    )

    # -----------------------------------------------------
    # Build crossing cost
    # -----------------------------------------------------

    river_cost = np.zeros(
        (height, width),
        dtype=np.float32
    )

    # Streams
    river_cost[
        stream_mask == 1
    ] = STREAM_COST

    # Rivers have higher priority
    river_cost[
        river_mask == 1
    ] = RIVER_COST

    # Drains
    # Only apply where no river exists
    drain_only = (
        (drain_mask == 1)
        &
        (river_mask == 0)
        &
        (stream_mask == 0)
    )

    river_cost[
        drain_only
    ] = DRAIN_COST

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    stream_pixels = np.count_nonzero(
        stream_mask == 1
    )

    river_pixels = np.count_nonzero(
        river_mask == 1
    )

    drain_pixels = np.count_nonzero(
        drain_only
    )

    crossing_pixels = np.count_nonzero(
        river_cost > 0
    )

    print("\nCrossing-cost statistics:")

    print(
        "Stream pixels:",
        stream_pixels
    )

    print(
        "River pixels:",
        river_pixels
    )

    print(
        "Drain pixels:",
        drain_pixels
    )

    print(
        "Total crossing pixels:",
        crossing_pixels
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
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
            river_cost,
            1
        )

    print(
        "\nRiver crossing cost created successfully!"
    )

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


if __name__ == "__main__":
    create_river_cost()