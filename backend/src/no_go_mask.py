import rasterio
from rasterio.features import rasterize
from shapely.geometry import box
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

DEM_PATH = DATA_DIR / "sample_dem.tif"
OUTPUT_PATH = DATA_DIR / "no_go_mask.tif"

FIGURE_DIR = BASE_DIR / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FIGURE = FIGURE_DIR / "10_no_go_zone.png"


# ============================================================
# TEST NO-GO ZONE
# ============================================================
# Rectangle defined using:
# min longitude, min latitude, max longitude, max latitude

NO_GO_ZONE = box(
    77.205, 32.245,
    77.225, 32.265
)


# ============================================================
# CREATE NO-GO MASK
# ============================================================

def create_no_go_mask():

    print("Loading DEM...")

    with rasterio.open(DEM_PATH) as src:

        dem = src.read(1)

        profile = src.profile.copy()
        transform = src.transform
        height = src.height
        width = src.width
        bounds = src.bounds

    print(f"DEM size: {width} x {height}")
    print(f"DEM bounds: {bounds}")

    # Rasterize polygon
    mask = rasterize(
        [(NO_GO_ZONE, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8"
    )

    # Save GeoTIFF
    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.write(mask, 1)

    # Statistics
    total_pixels = mask.size
    blocked_pixels = np.sum(mask == 1)
    usable_pixels = np.sum(mask == 0)

    print("\nNO-GO ZONE CREATED")
    print("-----------------------------")
    print(f"Total pixels      : {total_pixels}")
    print(f"No-Go pixels      : {blocked_pixels}")
    print(f"Usable pixels     : {usable_pixels}")
    print(
        f"No-Go coverage    : "
        f"{blocked_pixels / total_pixels * 100:.2f}%"
    )

    print(f"\nSaved to:")
    print(OUTPUT_PATH)

    # ========================================================
    # VISUALIZATION
    # ========================================================

    plt.figure(figsize=(12, 8))

    plt.imshow(
        dem,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="terrain"
    )

    # Show No-Go zone
    plt.imshow(
        np.where(mask == 1, 1, np.nan),
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="Reds",
        alpha=0.6
    )

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Test No-Go Zone on Terrain")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    create_no_go_mask()