import rasterio
import matplotlib.pyplot as plt


DEM_PATH = "data/dem/sample_dem.tif"
WATER_PATH = "data/dem/water_mask.tif"


with rasterio.open(DEM_PATH) as dem:
    elevation = dem.read(1)
    extent = [
        dem.bounds.left,
        dem.bounds.right,
        dem.bounds.bottom,
        dem.bounds.top
    ]


with rasterio.open(WATER_PATH) as water:
    water_mask = water.read(1)


plt.figure(figsize=(10, 7))

plt.imshow(
    elevation,
    extent=extent,
    cmap="terrain"
)

plt.imshow(
    water_mask,
    extent=extent,
    cmap="Blues",
    alpha=0.6
)

plt.title("Manali Terrain with OpenStreetMap Water Features")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.colorbar(label="Elevation (m)")

plt.tight_layout()

# --------------------------------------------------
# Save figure
# --------------------------------------------------

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FIGURE_DIR = BASE_DIR / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FIGURE = FIGURE_DIR / "04_water.png"

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight"
)

print("\nFigure saved successfully!")
print(f"Saved to: {OUTPUT_FIGURE}")

plt.show()