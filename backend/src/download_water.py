import requests
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_PATH = BASE_DIR / "data" / "dem" / "water_osm.json"


# Manali test region
SOUTH = 32.20
WEST = 77.15
NORTH = 32.30
EAST = 77.30


def download_water_data():

    query = f"""
    [out:json][timeout:300];

    (
      way["natural"="water"]({SOUTH},{WEST},{NORTH},{EAST});
      relation["natural"="water"]({SOUTH},{WEST},{NORTH},{EAST});
      way["waterway"]({SOUTH},{WEST},{NORTH},{EAST});
    );

    out geom;
    """

    url = "https://overpass.private.coffee/api/interpreter"

    print("Requesting water data from OpenStreetMap...")

    headers = {
        "User-Agent": "TerrainAwareRoutePlanning/1.0",
        "Accept": "application/json"
    }

    response = requests.post(
        url,
        data={"data": query},
        headers=headers,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    OUTPUT_PATH.write_text(
        response.text,
        encoding="utf-8"
    )

    print("\nWater data downloaded successfully.")
    print(f"Features found : {len(data['elements'])}")
    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    download_water_data()