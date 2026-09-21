import csv
import matplotlib.pyplot as plt
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

CSV_PATH = RESULTS_DIR / "route_comparison.csv"
OUTPUT_FIGURE = RESULTS_DIR / "figures" / "12_route_comparison.png"


def main():

    routes = []
    distances = []

    # Read CSV without pandas
    with open(CSV_PATH, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:
            routes.append(row["Route"])
            distances.append(float(row["Distance_km"]))

    # Create chart
    plt.figure(figsize=(10, 6))

    plt.bar(
        routes,
        distances
    )

    plt.ylabel("Distance (km)")
    plt.xlabel("Route")
    plt.title("Route Distance Comparison")

    plt.xticks(
        rotation=15,
        ha="right"
    )

    plt.tight_layout()

    # Save figure
    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()


if __name__ == "__main__":
    main()