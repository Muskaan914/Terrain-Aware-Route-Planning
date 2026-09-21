import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

ROADS_PATH = DATA_DIR / "roads_osm.json"


print("=" * 60)
print("CHECKING OSM ROAD BRIDGE INFORMATION")
print("=" * 60)


with open(ROADS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


elements = data.get("elements", [])

print("\nTotal OSM elements:", len(elements))


bridge_count = 0
bridge_examples = []


for element in elements:

    tags = element.get("tags", {})

    if "bridge" in tags:

        bridge_count += 1

        if len(bridge_examples) < 10:

            bridge_examples.append({
                "id": element.get("id"),
                "type": element.get("type"),
                "bridge": tags.get("bridge"),
                "highway": tags.get("highway"),
                "name": tags.get("name")
            })


print("\nElements containing bridge tag:", bridge_count)


if bridge_examples:

    print("\nBridge examples:")

    for example in bridge_examples:
        print(example)

else:

    print("\nNo bridge-tagged road elements found.")


# ---------------------------------------------------------
# Also show highway classes
# ---------------------------------------------------------

highway_counts = {}

for element in elements:

    tags = element.get("tags", {})

    highway = tags.get("highway")

    if highway:

        highway_counts[highway] = (
            highway_counts.get(highway, 0) + 1
        )


print("\nHighway classes found:")

for highway, count in sorted(
    highway_counts.items(),
    key=lambda x: -x[1]
):

    print(f"{highway}: {count}")


print("\n" + "=" * 60)