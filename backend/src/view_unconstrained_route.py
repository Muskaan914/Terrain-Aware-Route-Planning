import rasterio
import numpy as np
import matplotlib.pyplot as plt
import heapq
import math


# ============================================================
# FILE PATH
# ============================================================

COST_PATH = "data/dem/final_terrain_cost_bridges.tif"
DEM_PATH = "data/dem/sample_dem.tif"


# ============================================================
# START AND GOAL
# ============================================================

START_LON = 77.17
START_LAT = 32.22

GOAL_LON = 77.27
GOAL_LAT = 32.28


# ============================================================
# LOAD DEM
# ============================================================

with rasterio.open(DEM_PATH) as src:
    dem = src.read(1).astype(float)
    transform = src.transform
    nodata = src.nodata

    height = src.height
    width = src.width


# ============================================================
# LOAD COST MAP
# ============================================================

with rasterio.open(COST_PATH) as src:
    cost = src.read(1).astype(float)


# ============================================================
# CONVERT LAT/LON TO PIXEL
# ============================================================

def latlon_to_pixel(lon, lat, transform):

    col = int((lon - transform.c) / transform.a)

    row = int((lat - transform.f) / transform.e)

    return row, col


# ============================================================
# CONVERT PIXEL TO LAT/LON
# ============================================================

def pixel_to_latlon(row, col, transform):

    lon = transform.c + (col + 0.5) * transform.a

    lat = transform.f + (row + 0.5) * transform.e

    return lon, lat


# ============================================================
# A* PATHFINDING
# ============================================================

def astar(cost, start, goal):

    rows, cols = cost.shape

    directions = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1)
    ]

    open_set = []

    heapq.heappush(open_set, (0, start))

    came_from = {}

    g_score = {
        start: 0
    }

    def heuristic(a, b):

        return math.sqrt(
            (a[0] - b[0]) ** 2 +
            (a[1] - b[1]) ** 2
        )

    while open_set:

        _, current = heapq.heappop(open_set)

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            return path

        for dr, dc in directions:

            nr = current[0] + dr
            nc = current[1] + dc

            if nr < 0 or nr >= rows:
                continue

            if nc < 0 or nc >= cols:
                continue

            # Block invalid / water cells
            if cost[nr, nc] <= 0 or cost[nr, nc] == -9999:
                continue

            distance = math.sqrt(dr ** 2 + dc ** 2)

            movement_cost = distance * cost[nr, nc]

            neighbor = (nr, nc)

            tentative_g = (
                g_score[current] + movement_cost
            )

            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g +
                    heuristic(neighbor, goal)
                )

                heapq.heappush(
                    open_set,
                    (f_score, neighbor)
                )

    return None


# ============================================================
# START / GOAL PIXELS
# ============================================================

start = latlon_to_pixel(
    START_LON,
    START_LAT,
    transform
)

goal = latlon_to_pixel(
    GOAL_LON,
    GOAL_LAT,
    transform
)

print("Start cell:", start)
print("Goal cell :", goal)


# ============================================================
# RUN A*
# ============================================================

print()
print("Running A*...")

path = astar(
    cost,
    start,
    goal
)

if path is None:

    print("No route found.")

    exit()


print("Route found!")
print("Path cells:", len(path))


# ============================================================
# PREPARE DEM
# ============================================================

if nodata is not None:

    dem[dem == nodata] = np.nan


# ============================================================
# PLOT
# ============================================================

plt.figure(figsize=(12, 8))

plt.imshow(
    dem,
    cmap="terrain",
    origin="upper"
)


# ============================================================
# ROUTE
# ============================================================

route_rows = [
    p[0]
    for p in path
]

route_cols = [
    p[1]
    for p in path
]

plt.plot(
    route_cols,
    route_rows,
    linewidth=2,
    label="A* Route"
)


# ============================================================
# START
# ============================================================

plt.scatter(
    start[1],
    start[0],
    s=120,
    marker="o",
    label="Start"
)


# ============================================================
# DESTINATION
# ============================================================

plt.scatter(
    goal[1],
    goal[0],
    s=120,
    marker="X",
    label="Destination"
)


# ============================================================
# LABELS
# ============================================================

plt.title(
    "Terrain-Aware A* Route"
)

plt.xlabel(
    "DEM Column"
)

plt.ylabel(
    "DEM Row"
)

plt.legend()

plt.colorbar(
    label="Elevation (m)"
)

plt.tight_layout()

# ============================================================
# SAVE FIGURE
# ============================================================

from pathlib import Path

FIGURE_DIR = Path("results/figures")

# Create folder if it does not exist
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FIGURE = FIGURE_DIR / "08_astar_unconstrained.png"

plt.savefig(
    OUTPUT_FIGURE,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Figure saved successfully!")
print("Saved to:", OUTPUT_FIGURE)

plt.show()