import json
from pathlib import Path

import rasterio
from rasterio.features import rasterize


BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"
ROADS_JSON = BASE_DIR / "data" / "dem" / "roads_osm.json"
OUTPUT_PATH = BASE_DIR / "data" / "dem" / "road_mask.tif"


def rasterize_roads():

    print("Loading DEM grid...")

    # Use the DEM as the exact spatial template.
    with rasterio.open(DEM_PATH) as dem:

        width = dem.width
        height = dem.height
        transform = dem.transform
        crs = dem.crs
        profile = dem.profile.copy()

        print(f"DEM size : {width} x {height}")
        print(f"CRS      : {crs}")


    print("\nLoading OpenStreetMap road data...")

    with open(ROADS_JSON, "r", encoding="utf-8") as f:
        road_data = json.load(f)

    elements = road_data.get("elements", [])

    print(f"OSM road features found : {len(elements)}")


    # --------------------------------------------------
    # Convert OSM ways into GeoJSON-like LineStrings
    # --------------------------------------------------

    shapes = []

    skipped = 0

    for element in elements:

        geometry = element.get("geometry")

        if not geometry:
            skipped += 1
            continue

        coordinates = []

        for point in geometry:

            lon = point.get("lon")
            lat = point.get("lat")

            if lon is not None and lat is not None:
                coordinates.append([lon, lat])


        if len(coordinates) < 2:
            skipped += 1
            continue


        highway_type = element.get("tags", {}).get("highway")

        if not highway_type:
            skipped += 1
            continue


        geometry_object = {
            "type": "LineString",
            "coordinates": coordinates
        }

        shapes.append((geometry_object, 1))


    print(f"Valid road geometries : {len(shapes)}")
    print(f"Skipped features      : {skipped}")


    if not shapes:
        raise RuntimeError("No valid road geometries found.")


    # --------------------------------------------------
    # Rasterize
    # --------------------------------------------------

    print("\nRasterizing roads...")

    road_mask = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        default_value=1,
        all_touched=True,
        dtype="uint8"
    )


    # --------------------------------------------------
    # Save GeoTIFF
    # --------------------------------------------------

    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        compress="lzw",
        nodata=0
    )


    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.write(road_mask, 1)


    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    road_pixels = int((road_mask == 1).sum())
    total_pixels = road_mask.size

    percentage = (road_pixels / total_pixels) * 100


    print("\n========================================")
    print("Road raster created successfully!")
    print("========================================")

    print(f"Road pixels   : {road_pixels}")
    print(f"Total pixels  : {total_pixels}")
    print(f"Road coverage : {percentage:.2f}%")

    print("\nOutput file:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    rasterize_roads()