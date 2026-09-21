import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

OUTPUT_FILE = RESULTS_DIR / "all_route_preferences.csv"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ACTUAL TEST RESULTS
# ============================================================

results = [
    {
        "Preference": "Shortest",
        "Distance_km": 14.872,
        "Elevation_gain_m": 2860.0,
        "Elevation_loss_m": 1642.0,
        "Average_terrain_cost": 3.336,
        "Maximum_terrain_cost": 4.399
    },
    {
        "Preference": "Terrain-Friendly",
        "Distance_km": 18.089,
        "Elevation_gain_m": 2511.0,
        "Elevation_loss_m": 1293.0,
        "Average_terrain_cost": 2.395,
        "Maximum_terrain_cost": 4.345
    },
    {
        "Preference": "Lowest Elevation Gain",
        "Distance_km": 15.109,
        "Elevation_gain_m": 2461.0,
        "Elevation_loss_m": 1243.0,
        "Average_terrain_cost": 3.367,
        "Maximum_terrain_cost": 4.399
    },
    {
        "Preference": "Balanced",
        "Distance_km": 15.705,
        "Elevation_gain_m": 2735.0,
        "Elevation_loss_m": 1517.0,
        "Average_terrain_cost": 2.794,
        "Maximum_terrain_cost": 4.399
    }
]


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [
    "Preference",
    "Distance_km",
    "Elevation_gain_m",
    "Elevation_loss_m",
    "Average_terrain_cost",
    "Maximum_terrain_cost"
]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("=" * 60)
print("ALL ROUTE PREFERENCES")
print("=" * 60)

for route in results:

    print(f"\n{route['Preference']}")
    print("-" * 40)

    print(
        f"Distance             : "
        f"{route['Distance_km']:.3f} km"
    )

    print(
        f"Elevation gain       : "
        f"{route['Elevation_gain_m']:.1f} m"
    )

    print(
        f"Elevation loss       : "
        f"{route['Elevation_loss_m']:.1f} m"
    )

    print(
        f"Average terrain cost : "
        f"{route['Average_terrain_cost']:.3f}"
    )

    print(
        f"Maximum terrain cost : "
        f"{route['Maximum_terrain_cost']:.3f}"
    )


print("\n" + "=" * 60)
print("CSV SAVED SUCCESSFULLY")
print("=" * 60)

print(f"\nSaved to:")
print(OUTPUT_FILE)