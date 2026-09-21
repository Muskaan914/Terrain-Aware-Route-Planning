import rasterio
import numpy as np
import matplotlib.pyplot as plt
import heapq
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_cost_slope_nogo.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"
NO_GO_PATH = DATA_DIR / "no_go_mask.tif"

FIGURE_DIR = BASE_DIR / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FIGURE = FIGURE_DIR / "11_astar_route_nogo.png"


# ============================================================
# START / GOAL
# ============================================================

START_LON = 77.17
START_LAT = 32.22

GOAL_LON = 77.27
GOAL_LAT = 32.28

NODATA = -9999


# ============================================================
# CONVERT LAT/LON TO RASTER CELL
# ============================================================

def latlon_to_pixel(transform, lon, lat):

    col, row = ~transform * (lon, lat)

    return int(round(row)), int(round(col))


# ============================================================
# HEURISTIC
# ============================================================

def heuristic(a, b):

    return np.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2
    )


# ============================================================
# A* SEARCH
# ============================================================

def astar(cost):

    rows, cols = cost.shape

    start = latlon_to_pixel(
        transform,
        START_LON,
        START_LAT
    )

    goal = latlon_to_pixel(
        transform,
        GOAL_LON,
        GOAL_LAT
    )

    print("Start cell:", start)
    print("Goal cell :", goal)

    if cost[start] == NODATA:
        raise ValueError("Start cell is blocked.")

    if cost[goal] == NODATA:
        raise ValueError("Goal cell is blocked.")

    open_set = []

    heapq.heappush(
        open_set,
        (0, start)
    )

    came_from = {}

    g_score = {
        start: 0.0
    }

    visited = 0

    neighbors = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1)
    ]

    while open_set:

        _, current = heapq.heappop(open_set)

        visited += 1

        if current == goal:

            print("Goal reached!")
            print("Visited cells:", visited)

            path = []

            while current in came_from:

                path.append(current)
                current = came_from[current]

            path.append(start)

            path.reverse()

            return path

        for dr, dc in neighbors:

            nr = current[0] + dr
            nc = current[1] + dc

            if nr < 0 or nr >= rows:
                continue

            if nc < 0 or nc >= cols:
                continue

            if cost[nr, nc] == NODATA:
                continue

            neighbor = (nr, nc)

            movement_distance = np.sqrt(
                dr ** 2 + dc ** 2
            )

            movement_cost = (
                movement_distance *
                (
                    cost[current] +
                    cost[neighbor]
                ) / 2
            )

            tentative_g = (
                g_score[current] +
                movement_cost
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
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NO-GO CONSTRAINED A* ROUTE VISUALIZATION")
    print("=" * 60)

    global transform

    # --------------------------------------------------------
    # Load cost map
    # --------------------------------------------------------

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(float)

        transform = src.transform

        bounds = src.bounds

    # --------------------------------------------------------
    # Load DEM
    # --------------------------------------------------------

    with rasterio.open(DEM_PATH) as src:

        dem = src.read(1).astype(float)

    # --------------------------------------------------------
    # Load No-Go mask
    # --------------------------------------------------------

    with rasterio.open(NO_GO_PATH) as src:

        no_go = src.read(1)

    # --------------------------------------------------------
    # Replace NoData
    # --------------------------------------------------------

    dem[dem == -32768] = np.nan

    # --------------------------------------------------------
    # Run A*
    # --------------------------------------------------------

    path = astar(cost)

    if path is None:

        print("No route found.")
        return

    print("Route found!")
    print("Path cells:", len(path))

    # --------------------------------------------------------
    # Convert route cells to coordinates
    # --------------------------------------------------------

    route_lons = []
    route_lats = []

    for row, col in path:

        lon, lat = transform * (col, row)

        route_lons.append(lon)
        route_lats.append(lat)

    # --------------------------------------------------------
    # Plot terrain
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Plot No-Go Zone
    # --------------------------------------------------------

    plt.imshow(
        np.where(no_go == 1, 1, np.nan),
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap="Reds",
        alpha=0.55
    )

    # --------------------------------------------------------
    # Plot route
    # --------------------------------------------------------

    plt.plot(
        route_lons,
        route_lats,
        linewidth=2.5,
        label="A* Route"
    )

    # Start
    plt.scatter(
        START_LON,
        START_LAT,
        s=80,
        marker="o",
        label="Start"
    )

    # Destination
    plt.scatter(
        GOAL_LON,
        GOAL_LAT,
        s=100,
        marker="*",
        label="Destination"
    )

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.title(
        "A* Route with 45° Slope Constraint and No-Go Zone"
    )

    plt.legend()

    plt.tight_layout()

    # --------------------------------------------------------
    # Save figure
    # --------------------------------------------------------

    plt.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight"
    )

    print("\nFigure saved successfully!")
    print(f"Saved to: {OUTPUT_FIGURE}")

    plt.show()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()