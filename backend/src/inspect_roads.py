import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

ROADS_PATH = DATA_DIR / "roads_osm.json"


print("=" * 60)
print("INSPECTING ROAD OSM DATA")
print("=" * 60)


with open(ROADS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


print("\nTop-level data type:")
print(type(data).__name__)


if isinstance(data, dict):

    print("\nTop-level keys:")
    print(list(data.keys()))

elif isinstance(data, list):

    print("\nNumber of top-level items:")
    print(len(data))


# ---------------------------------------------------------
# Inspect first item
# ---------------------------------------------------------

if isinstance(data, dict):

    if "features" in data:

        items = data["features"]

        print("\nDetected GeoJSON FeatureCollection")
        print("Number of features:", len(items))

    elif "elements" in data:

        items = data["elements"]

        print("\nDetected OSM/Overpass format")
        print("Number of elements:", len(items))

    else:

        items = []

        print("\nNo 'features' or 'elements' key found.")


elif isinstance(data, list):

    items = data


# ---------------------------------------------------------
# Show first few items
# ---------------------------------------------------------

print("\nFirst item:")

if items:

    first = items[0]

    print(json.dumps(
        first,
        indent=2
    )[:3000])

else:

    print("No items found.")


print("\n" + "=" * 60)