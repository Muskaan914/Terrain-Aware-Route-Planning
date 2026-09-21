import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

WATER_PATH = DATA_DIR / "water_osm.json"


print("=" * 60)
print("INSPECTING OSM WATER DATA")
print("=" * 60)


with open(
    WATER_PATH,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


elements = data.get("elements", [])

print("\nTotal water elements:", len(elements))


natural_water = 0
waterways = 0
other = 0

natural_types = {}
waterway_types = {}


for element in elements:

    tags = element.get("tags", {})

    natural = tags.get("natural")
    waterway = tags.get("waterway")

    if natural == "water":

        natural_water += 1

        water_type = tags.get(
            "water",
            "unspecified"
        )

        natural_types[water_type] = (
            natural_types.get(water_type, 0) + 1
        )

    elif waterway:

        waterways += 1

        waterway_types[waterway] = (
            waterway_types.get(waterway, 0) + 1
        )

    else:

        other += 1


print("\nNatural water features:", natural_water)

print("\nNatural water types:")

for water_type, count in sorted(
    natural_types.items(),
    key=lambda x: -x[1]
):

    print(
        f"{water_type}: {count}"
    )


print("\nWaterway features:", waterways)

print("\nWaterway types:")

for waterway_type, count in sorted(
    waterway_types.items(),
    key=lambda x: -x[1]
):

    print(
        f"{waterway_type}: {count}"
    )


print("\nOther features:", other)


# ---------------------------------------------------------
# Show examples
# ---------------------------------------------------------

print("\nExample elements:")

shown = 0

for element in elements:

    tags = element.get("tags", {})

    if (
        tags.get("natural") == "water"
        or
        tags.get("waterway")
    ):

        print({
            "id": element.get("id"),
            "natural": tags.get("natural"),
            "water": tags.get("water"),
            "waterway": tags.get("waterway"),
            "name": tags.get("name")
        })

        shown += 1

        if shown >= 10:
            break


print("\n" + "=" * 60)