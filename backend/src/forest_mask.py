import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
from pathlib import Path


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

WORLDCOVER_PATH = DATA_DIR / "ESA_WorldCover_10m_2021_v200_N30E075_Map.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"
OUTPUT_PATH = DATA_DIR / "forest_mask.tif"


# WorldCover class:
# 10 = Tree Cover
TREE_COVER_CLASS = 10


# ---------------------------------------------------------
# Create forest mask
# ---------------------------------------------------------

def create_forest_mask():

    print("=" * 50)
    print("Creating forest / tree-cover mask")
    print("=" * 50)

    # Open DEM to use its grid as the target grid
    with rasterio.open(DEM_PATH) as dem:

        target_height = dem.height
        target_width = dem.width
        target_transform = dem.transform
        target_crs = dem.crs
        target_profile = dem.profile.copy()

        print("\nDEM grid:")
        print("Width :", target_width)
        print("Height:", target_height)
        print("CRS   :", target_crs)
        print("Bounds:", dem.bounds)

    # Open WorldCover
    with rasterio.open(WORLDCOVER_PATH) as wc:

        print("\nWorldCover:")
        print("Width :", wc.width)
        print("Height:", wc.height)
        print("CRS   :", wc.crs)
        print("Resolution:", wc.res)
        print("Bounds:", wc.bounds)

        # Empty target array matching DEM
        aligned_worldcover = np.zeros(
            (target_height, target_width),
            dtype=np.uint8
        )

        # Reproject/resample WorldCover onto DEM grid
        reproject(
            source=rasterio.band(wc, 1),
            destination=aligned_worldcover,
            src_transform=wc.transform,
            src_crs=wc.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            src_nodata=wc.nodata,
            dst_nodata=0,
            resampling=Resampling.mode
        )

    # -----------------------------------------------------
    # Extract Tree Cover
    # -----------------------------------------------------

    forest_mask = np.where(
        aligned_worldcover == TREE_COVER_CLASS,
        1,
        0
    ).astype(np.uint8)

    total_pixels = forest_mask.size
    forest_pixels = np.count_nonzero(forest_mask)

    forest_percentage = (
        forest_pixels / total_pixels
    ) * 100

    print("\nForest / Tree Cover results:")
    print("Total pixels :", total_pixels)
    print("Forest pixels:", forest_pixels)
    print(f"Forest coverage: {forest_percentage:.2f}%")

    # -----------------------------------------------------
    # Save output
    # -----------------------------------------------------

    target_profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **target_profile
    ) as dst:

        dst.write(forest_mask, 1)

    print("\nForest mask created successfully!")
    print("Output file:")
    print(OUTPUT_PATH)

    print("=" * 50)


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":
    create_forest_mask()