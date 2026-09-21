import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MAIN_PATH = BASE_DIR / "data" / "dem" / "roads_osm.json"
TILE3_PATH = BASE_DIR / "data" / "dem" / "roads_tile3.json"


def merge_road_data():

    print("Loading existing road data...")

    with open(MAIN_PATH, "r", encoding="utf-8") as f:
        main_data = json.load(f)

    print(f"Existing features : {len(main_data['elements'])}")


    print("\nLoading recovered Tile 3 data...")

    with open(TILE3_PATH, "r", encoding="utf-8") as f:
        tile3_data = json.load(f)

    print(f"Tile 3 features   : {len(tile3_data['elements'])}")


    # Combine both datasets
    all_elements = (
        main_data["elements"]
        + tile3_data["elements"]
    )


    # Remove duplicates using OSM element ID
    unique_elements = {}

    for element in all_elements:

        element_id = element.get("id")

        if element_id is not None:
            unique_elements[element_id] = element


    final_elements = list(unique_elements.values())


    # Save merged dataset
    merged_data = {
        "version": 0.6,
        "generator": "Terrain-Aware-Route-Planning",
        "elements": final_elements
    }


    with open(MAIN_PATH, "w", encoding="utf-8") as f:

        json.dump(
            merged_data,
            f
        )


    print("\n========================================")
    print("Road datasets merged successfully!")
    print("========================================")

    print(f"Original features : {len(main_data['elements'])}")
    print(f"Tile 3 features   : {len(tile3_data['elements'])}")
    print(f"Final unique      : {len(final_elements)}")

    print("\nUpdated file:")
    print(MAIN_PATH)


if __name__ == "__main__":
    merge_road_data()