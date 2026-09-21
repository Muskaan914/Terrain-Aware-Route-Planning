import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DIFFICULTY_PATH = (
    BASE_DIR / "data" / "dem" / "terrain_difficulty.tif"
)

COST_PATH = (
    BASE_DIR / "data" / "dem" / "terrain_cost.tif"
)


# --------------------------------------------------
# Cost model
# --------------------------------------------------

def calculate_cost(difficulty, penalty=4.0):
    """
    Convert terrain difficulty into a traversal-cost
    multiplier.

    Difficulty:
        0 = easy
        1 = very difficult

    Cost:
        1 = normal movement cost
        higher values = more expensive terrain
    """

    cost = 1.0 + (penalty * difficulty)

    return cost


# --------------------------------------------------
# Main program
# --------------------------------------------------

def main():

    print("Loading terrain difficulty...")

    if not DIFFICULTY_PATH.exists():

        print("ERROR: terrain_difficulty.tif not found.")
        print(f"Expected location: {DIFFICULTY_PATH}")

        return

    with rasterio.open(DIFFICULTY_PATH) as src:

        difficulty = src.read(1)

        profile = src.profile.copy()

        nodata = src.nodata

    print("Terrain difficulty loaded successfully.")

    # --------------------------------------------------
    # Handle NoData
    # --------------------------------------------------

    valid_mask = difficulty != nodata

    difficulty_float = difficulty.astype(float)

    difficulty_float[~valid_mask] = np.nan

    # --------------------------------------------------
    # Calculate cost
    # --------------------------------------------------

    print("\nBuilding terrain cost map...")

    cost = calculate_cost(
        difficulty_float,
        penalty=4.0
    )

    # Restore NoData
    cost[~valid_mask] = -9999

    print("Terrain cost map created.")

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    valid_cost = cost[cost != -9999]

    print("\n===== TERRAIN COST INFORMATION =====")

    print(
        f"Minimum cost : "
        f"{np.min(valid_cost):.3f}"
    )

    print(
        f"Maximum cost : "
        f"{np.max(valid_cost):.3f}"
    )

    print(
        f"Mean cost    : "
        f"{np.mean(valid_cost):.3f}"
    )

    # --------------------------------------------------
    # Save cost GeoTIFF
    # --------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=-9999
    )

    with rasterio.open(
        COST_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(
            cost.astype(rasterio.float32),
            1
        )

    print("\nTerrain cost map saved to:")

    print(COST_PATH)

    # --------------------------------------------------
    # Visualization
    # --------------------------------------------------

    display = cost.copy()

    display[display == -9999] = np.nan

    plt.figure(figsize=(10, 7))

    plt.imshow(
        display,
        vmin=1,
        vmax=5
    )

    plt.colorbar(
        label="Traversal Cost"
    )

    plt.title("Terrain Cost Map")

    plt.xlabel("Column")
    plt.ylabel("Row")

    plt.show()


if __name__ == "__main__":
    main()