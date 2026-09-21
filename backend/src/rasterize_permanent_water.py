import json
import rasterio
import numpy as np

from pathlib import Path
from shapely.geometry import shape, Polygon, MultiPolygon
from rasterio.features import rasterize


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

WATER_PATH = DATA_DIR / "water_osm.json"
DEM_PATH = DATA_DIR / "sample_dem.tif"

OUTPUT_PATH = DATA_DIR / "permanent_water_mask.tif"


# =========================================================
# Permanent water types
# =========================================================

PERMANENT_WATER_TYPES = {
    "lake",
    "pond",
    "reservoir"
}


# =========================================================
# Main
# =========================================================

def create_permanent_water_mask():

    print("=" * 60)
    print("CREATING PERMANENT WATER MASK")
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
    # Load OSM water
    # -----------------------------------------------------

    with open(
        WATER_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    elements = data.get("elements", [])

    print("\nTotal OSM water elements:", len(elements))

    # -----------------------------------------------------
    # Extract permanent water polygons
    # -----------------------------------------------------

    permanent_geometries = []

    counts = {}

    for element in elements:

        tags = element.get("tags", {})

        # We only want natural=water features
        if tags.get("natural") != "water":
            continue

        water_type = tags.get(
            "water",
            "unspecified"
        )

        if water_type not in PERMANENT_WATER_TYPES:
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

        # Need at least 3 points for a polygon
        if len(coordinates) < 3:
            continue

        try:

            polygon = Polygon(
                coordinates
            )

            if not polygon.is_valid:
                polygon = polygon.buffer(0)

            if not polygon.is_empty:

                permanent_geometries.append(
                    polygon
                )

                counts[water_type] = (
                    counts.get(water_type, 0) + 1
                )

        except Exception as e:

            print(
                "Skipping water feature:",
                element.get("id"),
                e
            )

    print(
        "\nValid permanent water geometries:",
        len(permanent_geometries)
    )

    print("\nWater type counts:")

    for water_type, count in counts.items():

        print(
            f"{water_type}: {count}"
        )

    # -----------------------------------------------------
    # Rasterize
    # -----------------------------------------------------

    permanent_water_mask = rasterize(
        [
            (geometry, 1)
            for geometry in permanent_geometries
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

    water_pixels = np.count_nonzero(
        permanent_water_mask == 1
    )

    total_pixels = (
        permanent_water_mask.size
    )

    coverage = (
        water_pixels /
        total_pixels *
        100
    )

    print("\nPermanent water statistics:")

    print(
        "Water pixels:",
        water_pixels
    )

    print(
        "Total pixels:",
        total_pixels
    )

    print(
        f"Coverage: {coverage:.2f}%"
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
            permanent_water_mask,
            1
        )

    print(
        "\nPermanent water mask created successfully!"
    )

    print("Output:")
    print(OUTPUT_PATH)

    print("=" * 60)


if __name__ == "__main__":
    create_permanent_water_mask()