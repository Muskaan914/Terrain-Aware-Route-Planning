import rasterio
import numpy as np
from collections import deque
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_cost_slope_nogo.tif"


# ============================================================
# TEST COORDINATES
# ============================================================

START = (77.17, 32.22)
GOAL = (77.27, 32.28)


# ============================================================
# LOAD COST MAP
# ============================================================

with rasterio.open(COST_PATH) as src:

    cost = src.read(1).astype(np.float32)

    transform = src.transform

    height, width = cost.shape


# ============================================================
# CONVERT LON/LAT TO PIXEL
# ============================================================

def lonlat_to_pixel(lon, lat):

    col, row = ~transform * (lon, lat)

    return int(round(row)), int(round(col))


start = lonlat_to_pixel(*START)
goal = lonlat_to_pixel(*GOAL)


print("=" * 60)
print("TERRAIN CONNECTIVITY DIAGNOSTIC")
print("=" * 60)

print("\nStart cell:")
print(start)

print("\nGoal cell:")
print(goal)


# ============================================================
# TRAVERSABLE CELLS
# ============================================================

traversable = (
    np.isfinite(cost)
    &
    (cost > 0)
    &
    (cost != -9999)
)


print("\nTraversable cells:")
print(np.sum(traversable))

print("Blocked / invalid cells:")
print(np.sum(~traversable))

print("\nStart traversable:", traversable[start])
print("Goal traversable:", traversable[goal])


# ============================================================
# BFS CONNECTIVITY
# ============================================================

queue = deque()

visited = np.zeros(
    (height, width),
    dtype=bool
)


if traversable[start]:

    queue.append(start)
    visited[start] = True


directions = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]


while queue:

    r, c = queue.popleft()

    for dr, dc in directions:

        nr = r + dr
        nc = c + dc

        if (
            nr < 0
            or nr >= height
            or nc < 0
            or nc >= width
        ):
            continue

        if visited[nr, nc]:
            continue

        if not traversable[nr, nc]:
            continue

        visited[nr, nc] = True

        queue.append((nr, nc))


reachable = np.sum(visited)


print("\nCells reachable from start:")
print(reachable)

print("\nGoal reachable:")
print(visited[goal])


# ============================================================
# GOAL NEIGHBOUR DIAGNOSTIC
# ============================================================

print()
print("=" * 60)
print("GOAL NEIGHBOUR DIAGNOSTIC")
print("=" * 60)

gr, gc = goal


for dr, dc in directions:

    nr = gr + dr
    nc = gc + dc

    if (
        0 <= nr < height
        and 0 <= nc < width
    ):

        print(
            f"Cell ({nr}, {nc}) -> "
            f"cost={cost[nr, nc]:.3f}, "
            f"traversable={traversable[nr, nc]}, "
            f"reachable={visited[nr, nc]}"
        )


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)
print("CONNECTIVITY RESULT")
print("=" * 60)

print("Reachable component:", reachable)


if visited[goal]:

    print()
    print(
        "RESULT: START AND DESTINATION ARE CONNECTED."
    )

else:

    print()
    print(
        "RESULT: START AND DESTINATION ARE DISCONNECTED."
    )

print("=" * 60)