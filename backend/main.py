from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import rasterio
import os
import numpy as np
import heapq
import math
from pathlib import Path


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Terrain-Aware Route Planning API",
    description="Terrain-aware route planning and risk analysis system",
    version="1.0.0"
)
# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://terrain-aware-route-planning.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_cost_slope_nogo.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"

NODATA = -9999


# ============================================================
# REQUEST MODEL
# ============================================================

class RouteRequest(BaseModel):

    start_lon: float
    start_lat: float

    goal_lon: float
    goal_lat: float

    preference: str = "terrain"


# ============================================================
# LAT/LON → PIXEL
# ============================================================

def latlon_to_pixel(transform, lon, lat):

    col, row = ~transform * (lon, lat)

    return int(round(row)), int(round(col))


# ============================================================
# HEURISTIC
# ============================================================

def heuristic(a, b):

    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2
    )


# ============================================================
# A* ROUTE
# ============================================================

def find_route(cost, start, goal, preference):

    rows, cols = cost.shape

    open_set = []

    heapq.heappush(
        open_set,
        (0.0, start)
    )

    came_from = {}

    g_score = {
        start: 0.0
    }

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

    visited = 0

    while open_set:

        _, current = heapq.heappop(open_set)

        visited += 1

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            return path, visited

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

            distance = math.sqrt(
                dr ** 2 + dc ** 2
            )

            terrain_factor = (
                cost[current] +
                cost[neighbor]
            ) / 2.0

            # ------------------------------------------------
            # Preference-based edge cost
            # ------------------------------------------------

            if preference == "shortest":

                edge_cost = distance

            elif preference == "terrain":

                edge_cost = (
                    distance *
                    terrain_factor
                )

            elif preference == "elevation":

                # Terrain-aware approximation.
                # Elevation statistics are calculated separately.

                edge_cost = (
                    distance *
                    terrain_factor
                )

            elif preference == "balanced":

                edge_cost = (
                    0.5 * distance +
                    0.5 * distance * terrain_factor
                )

            else:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid preference. "
                        "Use shortest, terrain, "
                        "elevation, or balanced."
                    )
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
                    heuristic(neighbor, goal)
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score,
                        neighbor
                    )
                )

    return None, visited


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

    elevation_gain = 0.0

    elevation_loss = 0.0

    terrain_values = []

    for i in range(len(path) - 1):

        r1, c1 = path[i]

        r2, c2 = path[i + 1]

        dr = r2 - r1
        dc = c2 - c1

        # Approximate cell dimensions in meters

        lat = (
            transform.f +
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

        change = (
            elevation[r2, c2] -
            elevation[r1, c1]
        )

        if not np.isnan(change):

            if change > 0:

                elevation_gain += change

            else:

                elevation_loss += abs(change)

        terrain_values.append(
            cost[r2, c2]
        )

    return {
        "distance_km": distance / 1000,

        "elevation_gain_m":
            float(elevation_gain),

        "elevation_loss_m":
            float(elevation_loss),

        "average_terrain_cost":
            float(np.mean(terrain_values)),

        "maximum_terrain_cost":
            float(np.max(terrain_values))
    }


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():

    return {
        "message":
            "Terrain-Aware Route Planning API is running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }

# ============================================================
# REAL DEM TERRAIN GRID
# ============================================================

@app.get("/terrain/grid")
def get_terrain_grid():
    """
    Return a downsampled elevation grid from the real DEM.
    Used by the React 3D terrain viewer.
    """

    if not DEM_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="DEM file not found."
        )

    try:

        with rasterio.open(DEM_PATH) as src:

            # Keep the grid small enough for browser 3D rendering
            max_size = 60

            scale = max(
                src.width / max_size,
                src.height / max_size,
                1
            )

            out_width = max(
                2,
                int(src.width / scale)
            )

            out_height = max(
                2,
                int(src.height / scale)
            )

            elevation = src.read(
                1,
                out_shape=(
                    out_height,
                    out_width
                ),
                resampling=rasterio.enums.Resampling.bilinear
            ).astype(float)

            # Convert DEM NoData to NaN
            nodata = src.nodata

            if nodata is not None:
                elevation[
                    elevation == nodata
                ] = np.nan

            # Make sure valid elevation values exist
            valid = np.isfinite(elevation)

            if not np.any(valid):
                raise HTTPException(
                    status_code=500,
                    detail="DEM contains no valid elevation data."
                )

            # Replace invalid cells with mean elevation
            mean_elevation = float(
                np.nanmean(elevation)
            )

            elevation[~valid] = mean_elevation

            # Geographic bounds of DEM
            bounds = src.bounds

            return {
                "success": True,

                "width": out_width,

                "height": out_height,

                "elevations": elevation.tolist(),

                "bounds": {
                    "west": float(bounds.left),
                    "south": float(bounds.bottom),
                    "east": float(bounds.right),
                    "north": float(bounds.top)
                },

                "elevation_min": float(
                    np.min(elevation)
                ),

                "elevation_max": float(
                    np.max(elevation)
                ),

                "elevation_mean": float(
                    np.mean(elevation)
                )
            }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to read DEM: {str(e)}"
        )

@app.get("/route/preferences")
def route_preferences():

    return {
        "preferences": [
            "shortest",
            "terrain",
            "elevation",
            "balanced"
        ]
    }


# ============================================================
# ACTUAL ROUTE PLANNING
# ============================================================

@app.post("/route/plan")
def plan_route(request: RouteRequest):

    allowed_preferences = [
        "shortest",
        "terrain",
        "elevation",
        "balanced"
    ]

    if request.preference not in allowed_preferences:

        raise HTTPException(
            status_code=400,
            detail="Invalid route preference"
        )

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

        elevation = src.read(1).astype(float)

    elevation[
        elevation == -32768
    ] = np.nan

    # --------------------------------------------------------
    # Convert coordinates
    # --------------------------------------------------------

    start = latlon_to_pixel(
        transform,
        request.start_lon,
        request.start_lat
    )

    goal = latlon_to_pixel(
        transform,
        request.goal_lon,
        request.goal_lat
    )

    rows, cols = cost.shape

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    if not (
        0 <= start[0] < rows
        and
        0 <= start[1] < cols
    ):

        raise HTTPException(
            status_code=400,
            detail="Start point is outside the DEM."
        )

    if not (
        0 <= goal[0] < rows
        and
        0 <= goal[1] < cols
    ):

        raise HTTPException(
            status_code=400,
            detail="Destination is outside the DEM."
        )

    # --------------------------------------------------------
    # Validate traversability
    # --------------------------------------------------------

    if cost[start] == NODATA:

        raise HTTPException(
            status_code=400,
            detail="Start point is blocked."
        )

    if cost[goal] == NODATA:

        raise HTTPException(
            status_code=400,
            detail="Destination is blocked."
        )

    # --------------------------------------------------------
    # Run A*
    # --------------------------------------------------------

    path, visited = find_route(
        cost,
        start,
        goal,
        request.preference
    )

    if path is None:

        raise HTTPException(
            status_code=404,
            detail="No feasible route could be found."
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    stats = calculate_statistics(
        path,
        elevation,
        cost,
        transform
    )

    # --------------------------------------------------------
    # Convert path to coordinates
    # --------------------------------------------------------

    coordinates = []

    for row, col in path:

        lon, lat = transform * (
            col,
            row
        )

        coordinates.append([
            float(lon),
            float(lat)
        ])

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "success": True,

        "preference":
            request.preference,

        "start": {
            "longitude":
                request.start_lon,
            "latitude":
                request.start_lat
        },

        "destination": {
            "longitude":
                request.goal_lon,
            "latitude":
                request.goal_lat
        },

        "actual_start_cell": [
            start[0],
            start[1]
        ],

        "actual_goal_cell": [
            goal[0],
            goal[1]
        ],

        "visited_cells":
            visited,

        "path_cells":
            len(path),

        "route_coordinates":
            coordinates,

        "statistics":
            stats
    }