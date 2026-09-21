import rasterio
import numpy as np
import heapq
import math
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_cost_slope_nogo.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"


# ============================================================
# START / DESTINATION
# ============================================================

START_LON = 77.17
START_LAT = 32.22

GOAL_LON = 77.27
GOAL_LAT = 32.28

NODATA = -9999


# ============================================================
# ROUTE PREFERENCE
# ============================================================

# Change this value to:
#
# "shortest"
# "terrain"
# "elevation"
# "balanced"
#

PREFERENCE = "balanced"


# ============================================================
# LAT/LON → RASTER CELL
# ============================================================

def latlon_to_pixel(transform, lon, lat):

    col, row = ~transform * (lon, lat)

    return int(round(row)), int(round(col))


# ============================================================
# HEURISTIC
# ============================================================

def heuristic(current, goal):

    return math.sqrt(
        (current[0] - goal[0]) ** 2 +
        (current[1] - goal[1]) ** 2
    )


# ============================================================
# EDGE COST
# ============================================================

def calculate_edge_cost(
    current,
    neighbor,
    terrain_cost,
    elevation,
    preference,
    cell_size
):

    r1, c1 = current
    r2, c2 = neighbor

    dr = r2 - r1
    dc = c2 - c1

    # Cell-to-cell distance in pixels
    distance_cells = math.sqrt(
        dr ** 2 + dc ** 2
    )

    # Average terrain multiplier
    terrain_factor = (
        terrain_cost[current] +
        terrain_cost[neighbor]
    ) / 2.0

    # Elevation change
    elevation_change = (
        elevation[r2, c2] -
        elevation[r1, c1]
    )

    positive_gain = max(
        elevation_change,
        0
    )

    # Convert elevation gain to approximately
    # cell-distance units.
    elevation_factor = (
        positive_gain / cell_size
    )

    # --------------------------------------------------------
    # 1. SHORTEST
    # --------------------------------------------------------

    if preference == "shortest":

        return distance_cells


    # --------------------------------------------------------
    # 2. TERRAIN-FRIENDLY
    # --------------------------------------------------------

    elif preference == "terrain":

        return (
            distance_cells *
            terrain_factor
        )


    # --------------------------------------------------------
    # 3. LOWEST ELEVATION GAIN
    # --------------------------------------------------------

    elif preference == "elevation":

        return (
            distance_cells +
            2.0 * elevation_factor
        )


    # --------------------------------------------------------
    # 4. BALANCED
    # --------------------------------------------------------

    elif preference == "balanced":

        distance_component = distance_cells

        terrain_component = (
            distance_cells *
            terrain_factor
        )

        elevation_component = (
            2.0 *
            elevation_factor
        )

        return (
            0.4 * distance_component +
            0.4 * terrain_component +
            0.2 * elevation_component
        )


    else:

        raise ValueError(
            "Invalid preference. "
            "Use shortest, terrain, elevation, or balanced."
        )


# ============================================================
# A* PLANNER
# ============================================================

def astar(
    cost,
    elevation,
    transform,
    preference
):

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

    print("\nPreference:", preference)

    print("Start cell:", start)
    print("Goal cell :", goal)

    if cost[start] == NODATA:

        raise ValueError(
            "Start cell is blocked."
        )

    if cost[goal] == NODATA:

        raise ValueError(
            "Goal cell is blocked."
        )

    # Approximate cell size in meters
    latitude = START_LAT

    cell_size = (
        111320 *
        math.cos(
            math.radians(latitude)
        ) *
        abs(transform.a)
    )

    open_set = []

    heapq.heappush(
        open_set,
        (0.0, start)
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

        _, current = heapq.heappop(
            open_set
        )

        visited += 1

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            print(
                "Goal reached!"
            )

            print(
                "Visited cells:",
                visited
            )

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

            edge_cost = calculate_edge_cost(
                current,
                neighbor,
                cost,
                elevation,
                preference,
                cell_size
            )

            tentative_g = (
                g_score[current] +
                edge_cost
            )

            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g +
                    heuristic(
                        neighbor,
                        goal
                    )
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score,
                        neighbor
                    )
                )

    return None


# ============================================================
# ROUTE STATISTICS
# ============================================================

def calculate_statistics(
    path,
    elevation,
    cost,
    transform
):

    distance = 0.0
    gain = 0.0
    loss = 0.0
    terrain_values = []

    for i in range(len(path) - 1):

        r1, c1 = path[i]
        r2, c2 = path[i + 1]

        dr = r2 - r1
        dc = c2 - c1

        # Approximate geographic distance
        lat = transform.f + (
            r1 * transform.e
        )

        cell_width = (
            111320 *
            math.cos(
                math.radians(lat)
            ) *
            abs(transform.a)
        )

        cell_height = (
            111320 *
            abs(transform.e)
        )

        step_distance = math.sqrt(
            (dc * cell_width) ** 2 +
            (dr * cell_height) ** 2
        )

        distance += step_distance

        elevation_change = (
            elevation[r2, c2] -
            elevation[r1, c1]
        )

        if elevation_change > 0:

            gain += elevation_change

        else:

            loss += abs(
                elevation_change
            )

        terrain_values.append(
            cost[r2, c2]
        )

    return {
        "distance_km": distance / 1000,
        "elevation_gain_m": gain,
        "elevation_loss_m": loss,
        "average_cost": np.mean(
            terrain_values
        ),
        "maximum_cost": np.max(
            terrain_values
        )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ROUTE PREFERENCE A* PLANNER")
    print("=" * 60)

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(float)

        transform = src.transform

    with rasterio.open(DEM_PATH) as src:

        elevation = src.read(1).astype(float)

    elevation[
        elevation == -32768
    ] = np.nan

    path = astar(
        cost,
        elevation,
        transform,
        PREFERENCE
    )

    if path is None:

        print("\nNo route found.")

        return

    stats = calculate_statistics(
        path,
        elevation,
        cost,
        transform
    )

    print("\n" + "=" * 60)
    print("ROUTE RESULT")
    print("=" * 60)

    print(
        f"Preference           : {PREFERENCE}"
    )

    print(
        f"Path cells           : {len(path)}"
    )

    print(
        f"Distance             : "
        f"{stats['distance_km']:.3f} km"
    )

    print(
        f"Elevation gain       : "
        f"{stats['elevation_gain_m']:.1f} m"
    )

    print(
        f"Elevation loss       : "
        f"{stats['elevation_loss_m']:.1f} m"
    )

    print(
        f"Average terrain cost : "
        f"{stats['average_cost']:.3f}"
    )

    print(
        f"Maximum terrain cost : "
        f"{stats['maximum_cost']:.3f}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()