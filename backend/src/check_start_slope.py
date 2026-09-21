import rasterio
import numpy as np

SLOPE_PATH = "data/dem/slope.tif"

START_ROW = 288
START_COL = 72

with rasterio.open(SLOPE_PATH) as src:
    slope = src.read(1).astype(float)

print("=" * 60)
print("START SLOPE DIAGNOSTIC")
print("=" * 60)

print("\nStart cell:")
print("Row:", START_ROW)
print("Column:", START_COL)

print(
    f"\nStart slope: {slope[START_ROW, START_COL]:.2f} degrees"
)

print("\n8 neighboring cells:")
print("-" * 60)

for dr in [-1, 0, 1]:

    for dc in [-1, 0, 1]:

        if dr == 0 and dc == 0:
            continue

        row = START_ROW + dr
        col = START_COL + dc

        value = slope[row, col]

        print(
            f"Cell ({row}, {col}) -> "
            f"slope = {value:.2f}° | "
            f"<= 40°: {value <= 40}"
        )

print("\n" + "=" * 60)