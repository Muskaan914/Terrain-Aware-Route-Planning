import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize


BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"
ROADS_JSON = BASE_DIR / "data" / "dem" / "roads_osm.json"
OUTPUT_PATH = BASE_DIR / "data" / "dem" / "road_cost.tif"


# --------------------------------------------------
# Road preference values
# Lower value = more preferred
# --------------------------------------------------

ROAD_COSTS = {
    "motorway": 1.0,
    "motorway_link": 1.1,

    "trunk": 1.1,
    "trunk_link": 1.2,

    "primary": 1.2,
    "primary_link": 1.3,

    "secondary": 1.3,
    "secondary_link": 1.4,

    "tertiary": 1.4,
    "tertiary_link": 1.5,

    "unclassified": 1.5,
    "residential": 1.5,
    "living_street": 1.5,

    "service": 1.6,

    "track": 1.8,
    "cycleway": 1.8,
    "path": 2.0,
    "footway": 2.0,
    "bridleway": 2.0,

    "steps": 2.5
}


def create_road_cost():

    print("Loading DEM grid...")

    with rasterio.open(DEM_PATH) as dem:

        width = dem.width
        height = dem.height
        transform = dem.transform
        profile = dem.profile.copy()

        print(f"DEM size : {width} x {height}")
        print(f"CRS      : {dem.crs}")


    print("\nLoading OpenStreetMap road data...")

    with open(ROADS_JSON, "r", encoding="utf-8") as f:
        road_data = json.load(f)

    elements = road_data.get("elements", [])

    print(f"OSM road features : {len(elements)}")


    # --------------------------------------------------
    # Convert roads into raster shapes
    # --------------------------------------------------

    shapes = []

    skipped = 0

    for element in elements:

        geometry = element.get("geometry")

        if not geometry:
            skipped += 1
            continue

        highway_type = element.get("tags", {}).get("highway")

        if highway_type not in ROAD_COSTS:
            skipped += 1
            continue

        coordinates = []

        for point in geometry:

            lon = point.get("lon")
            lat = point.get("lat")

            if lon is not None and lat is not None:
                coordinates.append((lon, lat))

        if len(coordinates) < 2:
            skipped += 1
            continue


        # Use the road class as the raster value
        road_cost = ROAD_COSTS[highway_type]

        geometry_object = {
            "type": "LineString",
            "coordinates": coordinates
        }

        shapes.append(
            (geometry_object, road_cost)
        )


    print(f"Valid road geometries : {len(shapes)}")
    print(f"Skipped features      : {skipped}")


    if not shapes:
        raise RuntimeError("No valid road geometries found.")


    # --------------------------------------------------
    # Rasterize road costs
    # --------------------------------------------------

    print("\nCreating road preference raster...")

    road_cost = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype="float32"
    )


    # --------------------------------------------------
    # Save GeoTIFF
    # --------------------------------------------------

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        compress="lzw",
        nodata=0
    )


    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.write(road_cost, 1)


    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    road_pixels = road_cost > 0

    if np.any(road_pixels):

        values = road_cost[road_pixels]

        print("\n========================================")
        print("Road cost layer created successfully!")
        print("========================================")

        print(f"Road pixels : {int(road_pixels.sum())}")
        print(f"Minimum road cost : {values.min():.2f}")
        print(f"Maximum road cost : {values.max():.2f}")
        print(f"Mean road cost    : {values.mean():.2f}")

    else:

        print("No road pixels were created.")


    print("\nOutput file:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    create_road_cost()