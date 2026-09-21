import json
from pathlib import Path

import rasterio
from rasterio.features import rasterize


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DEM_PATH = BASE_DIR / "data" / "dem" / "sample_dem.tif"
WATER_JSON = BASE_DIR / "data" / "dem" / "water_osm.json"
OUTPUT_PATH = BASE_DIR / "data" / "dem" / "water_mask.tif"


# --------------------------------------------------
# Rasterize water data
# --------------------------------------------------

def rasterize_water():

    print("Loading DEM grid...")

    # Open DEM so that the water raster uses
    # exactly the same grid, CRS, resolution and extent.
    with rasterio.open(DEM_PATH) as dem:

        profile = dem.profile.copy()

        width = dem.width
        height = dem.height
        transform = dem.transform
        crs = dem.crs

        print(f"DEM size : {width} x {height}")
        print(f"CRS      : {crs}")


    print("\nLoading OpenStreetMap water data...")

    with open(WATER_JSON, "r", encoding="utf-8") as f:
        water_data = json.load(f)

    elements = water_data.get("elements", [])

    print(f"OSM features found : {len(elements)}")


    # --------------------------------------------------
    # Convert OSM geometries into GeoJSON-like shapes
    # --------------------------------------------------

    shapes = []

    for element in elements:

        geometry = element.get("geometry")

        if not geometry:
            continue

        coordinates = []

        for point in geometry:
            lon = point.get("lon")
            lat = point.get("lat")

            if lon is not None and lat is not None:
                coordinates.append([lon, lat])

        if len(coordinates) < 2:
            continue


        element_type = element.get("type")


        # Water polygons
        if element.get("tags", {}).get("natural") == "water":

            if len(coordinates) >= 3:

                # Close polygon if necessary
                if coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])

                geometry_object = {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                }

                shapes.append((geometry_object, 1))


        # Rivers / streams / waterways
        elif "waterway" in element.get("tags", {}):

            geometry_object = {
                "type": "LineString",
                "coordinates": coordinates
            }

            shapes.append((geometry_object, 1))


    print(f"Valid geometries : {len(shapes)}")


    if not shapes:
        raise RuntimeError("No valid water geometries found.")


    # --------------------------------------------------
    # Rasterize
    # --------------------------------------------------

    print("\nRasterizing water features...")

    water_mask = rasterize(
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
        dst.write(water_mask, 1)


    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    water_pixels = int((water_mask == 1).sum())
    total_pixels = water_mask.size

    percentage = (water_pixels / total_pixels) * 100


    print("\nWater raster created successfully!")

    print(f"Output file   : {OUTPUT_PATH}")
    print(f"Water pixels  : {water_pixels}")
    print(f"Total pixels  : {total_pixels}")
    print(f"Water coverage: {percentage:.2f}%")


if __name__ == "__main__":
    rasterize_water()