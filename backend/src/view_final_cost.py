import rasterio
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_terrain_cost.tif"


def view_final_cost():

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(float)
        bounds = src.bounds
        nodata = src.nodata

    # Hide blocked cells
    if nodata is not None:
        cost[cost == nodata] = np.nan

    plt.figure(figsize=(12, 8))

    image = plt.imshow(
        cost,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="hot"
    )

    plt.colorbar(
        image,
        label="Traversal Cost"
    )

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.title(
        "Final Multi-Factor Terrain Cost Map"
    )

    plt.tight_layout()

# --------------------------------------------------
# Save figure
# --------------------------------------------------

FIGURE_DIR = BASE_DIR / "results" / "figures"

FIGURE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FIGURE = FIGURE_DIR / "07_final_cost.png"

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight"
)

print("\nFigure saved successfully!")
print(f"Saved to: {OUTPUT_FIGURE}")

plt.show()


if __name__ == "__main__":
    view_final_cost()