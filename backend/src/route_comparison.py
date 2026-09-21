from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

OUTPUT_FILE = RESULTS_DIR / "route_comparison.csv"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ROUTE RESULTS
# ============================================================

routes = [
    {
        "Route": "Unconstrained Terrain-Aware",
        "Distance_km": 14.288,
        "Elevation_gain_m": 2966.0,
        "Elevation_loss_m": 1748.0,
        "Average_terrain_cost": 2.768,
        "Maximum_cell_cost": 4.797,
        "Total_traversal_cost": 1226.25,
    },
    {
        "Route": "45° Slope-Constrained",
        "Distance_km": 18.057,
        "Elevation_gain_m": 2499.0,
        "Elevation_loss_m": 1281.0,
        "Average_terrain_cost": 2.397,
        "Maximum_cell_cost": 4.345,
        "Total_traversal_cost": 1280.15,
    },
    {
        "Route": "45° + No-Go Constrained",
        "Distance_km": 18.057,
        "Elevation_gain_m": 2499.0,
        "Elevation_loss_m": 1281.0,
        "Average_terrain_cost": 2.397,
        "Maximum_cell_cost": 4.345,
        "Total_traversal_cost": 1280.15,
    },
]


# ============================================================
# SAVE COMPARISON
# ============================================================

def save_comparison():

    fieldnames = [
        "Route",
        "Distance_km",
        "Elevation_gain_m",
        "Elevation_loss_m",
        "Average_terrain_cost",
        "Maximum_cell_cost",
        "Total_traversal_cost",
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
        writer.writerows(routes)

    print("=" * 60)
    print("ROUTE COMPARISON")
    print("=" * 60)

    for route in routes:

        print(f"\n{route['Route']}")
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
            f"Maximum cell cost    : "
            f"{route['Maximum_cell_cost']:.3f}"
        )

        print(
            f"Total traversal cost : "
            f"{route['Total_traversal_cost']:.2f}"
        )

    print("\nComparison saved successfully!")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    save_comparison()