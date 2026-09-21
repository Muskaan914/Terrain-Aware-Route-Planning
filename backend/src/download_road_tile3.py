import json
import time
import requests
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_PATH = BASE_DIR / "data" / "dem" / "roads_tile3.json"


# Failed Tile 3:
# 32.250,77.150 → 32.300,77.225

SOUTH = 32.250
WEST = 77.150
NORTH = 32.300
EAST = 77.225

MID_LAT = (SOUTH + NORTH) / 2


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


def query_area(south, west, north, east):

    query = f"""
    [out:json][timeout:180];

    way["highway"~"^({HIGHWAY_TYPES})$"]
        ({south},{west},{north},{east});

    out geom qt;
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


def main():

    print("Retrying failed road Tile 3...")
    print("Splitting Tile 3 into 2 smaller areas.\n")

    tiles = [
        (SOUTH, WEST, MID_LAT, EAST),
        (MID_LAT, WEST, NORTH, EAST)
    ]

    all_elements = []

    for i, (south, west, north, east) in enumerate(tiles, start=1):

        print(
            f"Sub-tile {i}/2: "
            f"{south:.3f},{west:.3f} → "
            f"{north:.3f},{east:.3f}"
        )

        try:

            data = query_area(
                south,
                west,
                north,
                east
            )

            elements = data.get("elements", [])

            print(f"  Features found: {len(elements)}")

            all_elements.extend(elements)

        except requests.exceptions.RequestException as error:

            print(f"  Sub-tile {i} failed: {error}")

        if i < len(tiles):
            time.sleep(10)


    # Remove duplicate OSM ways
    unique_elements = {}

    for element in all_elements:

        element_id = element.get("id")

        if element_id is not None:
            unique_elements[element_id] = element


    final_elements = list(unique_elements.values())


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
    print("Tile 3 download finished")
    print("========================================")

    print(f"Unique Tile 3 features : {len(final_elements)}")

    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()