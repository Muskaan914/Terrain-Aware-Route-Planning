import json
import time
import requests
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_PATH = BASE_DIR / "data" / "dem" / "roads_osm.json"


# --------------------------------------------------
# Manali test region
# --------------------------------------------------

SOUTH = 32.20
WEST = 77.15
NORTH = 32.30
EAST = 77.30


# --------------------------------------------------
# Useful road/path types for terrain routing
# --------------------------------------------------

HIGHWAY_TYPES = (
    "motorway|motorway_link|"
    "trunk|trunk_link|"
    "primary|primary_link|"
    "secondary|secondary_link|"
    "tertiary|tertiary_link|"
    "unclassified|residential|living_street|"
    "service|track|path|footway|"
    "bridleway|cycleway|steps"
)


def query_tile(south, west, north, east):

    query = f"""
    [out:json][timeout:180];

    way["highway"~"^({HIGHWAY_TYPES})$"]
        ({south},{west},{north},{east});

    out geom;
    """

    url = "https://overpass.private.coffee/api/interpreter"

    headers = {
        "User-Agent": "TerrainAwareRoutePlanning/1.0",
        "Accept": "application/json"
    }

    response = requests.post(
        url,
        data={"data": query},
        headers=headers,
        timeout=240
    )

    response.raise_for_status()

    return response.json()


def download_road_data():

    print("Downloading OpenStreetMap road data...")
    print("Region will be divided into 4 smaller tiles.\n")

    mid_lat = (SOUTH + NORTH) / 2
    mid_lon = (WEST + EAST) / 2

    tiles = [
        (SOUTH, WEST, mid_lat, mid_lon),
        (SOUTH, mid_lon, mid_lat, EAST),
        (mid_lat, WEST, NORTH, mid_lon),
        (mid_lat, mid_lon, NORTH, EAST)
    ]

    all_elements = []

    for i, (south, west, north, east) in enumerate(tiles, start=1):

        print(
            f"Tile {i}/4: "
            f"{south:.3f},{west:.3f} → "
            f"{north:.3f},{east:.3f}"
        )

        try:

            data = query_tile(
                south,
                west,
                north,
                east
            )

            elements = data.get("elements", [])

            print(f"  Features found: {len(elements)}")

            all_elements.extend(elements)

        except requests.exceptions.RequestException as error:

            print(f"  Tile {i} failed: {error}")

        # Small pause between requests
        if i < len(tiles):
            time.sleep(5)


    # --------------------------------------------------
    # Remove duplicate OSM ways
    # --------------------------------------------------

    unique_elements = {}

    for element in all_elements:

        element_id = element.get("id")

        if element_id is not None:
            unique_elements[element_id] = element


    final_elements = list(unique_elements.values())


    # --------------------------------------------------
    # Save combined data
    # --------------------------------------------------

    output_data = {
        "version": 0.6,
        "generator": "Terrain-Aware-Route-Planning",
        "elements": final_elements
    }


    OUTPUT_PATH.write_text(
        json.dumps(output_data),
        encoding="utf-8"
    )


    print("\n========================================")
    print("Road data downloaded successfully!")
    print("========================================")

    print(f"Total unique features : {len(final_elements)}")

    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    download_road_data()