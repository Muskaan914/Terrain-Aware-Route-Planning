import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SLOPE_PATH = BASE_DIR / "data" / "dem" / "slope.tif"

DIFFICULTY_PATH = BASE_DIR / "data" / "dem" / "terrain_difficulty.tif"


# --------------------------------------------------
# Terrain difficulty calculation
# --------------------------------------------------

def calculate_difficulty(slope, reference_slope=60.0):

    """
    Convert slope in degrees into a normalized
    terrain difficulty score between 0 and 1.

    0   = easy terrain
    1   = extremely difficult terrain
    """

    difficulty = slope / reference_slope

    # Keep values between 0 and 1
    difficulty = np.clip(difficulty, 0, 1)

    return difficulty


# --------------------------------------------------
# Main program
# --------------------------------------------------

def main():

    print("Loading slope data...")

    if not SLOPE_PATH.exists():

        print("ERROR: slope.tif not found.")

        print(f"Expected location: {SLOPE_PATH}")

        return

    with rasterio.open(SLOPE_PATH) as src:

        slope = src.read(1)

        profile = src.profile.copy()

        nodata = src.nodata

    print("Slope data loaded successfully.")

    # --------------------------------------------------
    # Handle NoData
    # --------------------------------------------------

    valid_mask = slope != nodata

    slope_float = slope.astype(float)

    slope_float[~valid_mask] = np.nan

    # --------------------------------------------------
    # Calculate difficulty
    # --------------------------------------------------

    print("\nCalculating terrain difficulty...")

    difficulty = calculate_difficulty(
        slope_float,
        reference_slope=60.0
    )

    # Restore NoData
    difficulty[~valid_mask] = -9999

    print("Terrain difficulty calculation completed.")

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    valid_difficulty = difficulty[difficulty != -9999]

    print("\n===== TERRAIN DIFFICULTY =====")

    print(
        f"Minimum difficulty : "
        f"{np.min(valid_difficulty):.3f}"
    )

    print(
        f"Maximum difficulty : "
        f"{np.max(valid_difficulty):.3f}"
    )

    print(
        f"Mean difficulty    : "
        f"{np.mean(valid_difficulty):.3f}"
    )

    # --------------------------------------------------
    # Save GeoTIFF
    # --------------------------------------------------

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=-9999
    )

    with rasterio.open(
        DIFFICULTY_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(
            difficulty.astype(rasterio.float32),
            1
        )

    print("\nTerrain difficulty saved to:")

    print(DIFFICULTY_PATH)

    # --------------------------------------------------
    # Visualization
    # --------------------------------------------------

    display = difficulty.copy()

    display[display == -9999] = np.nan

    plt.figure(figsize=(10, 7))

    plt.imshow(
        display,
        vmin=0,
        vmax=1
    )

    plt.colorbar(
        label="Terrain Difficulty (0–1)"
    )

    plt.title("Terrain Difficulty Map")

    plt.xlabel("Column")
    plt.ylabel("Row")

    # --------------------------------------------------
    # Save figure
    # --------------------------------------------------

    FIGURE_DIR = BASE_DIR / "results" / "figures"
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FIGURE = FIGURE_DIR / "03_terrain_difficulty.png"

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