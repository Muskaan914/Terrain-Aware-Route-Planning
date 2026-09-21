import rasterio
import numpy as np
import heapq
import math
from pathlib import Path
from pyproj import Geod


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = "data/dem/final_cost_slope_nogo.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"


# =========================================================
# Example start and destination
#
# IMPORTANT:
# These are only test coordinates.
# We will later select them from the map UI.
# =========================================================

START_LON = 77.17
START_LAT = 32.22

END_LON = 77.27
END_LAT = 32.28


# =========================================================
# A* planner
# =========================================================

class AStarPlanner:

    def __init__(self, cost, elevation, transform, bounds):

        self.cost = cost
        self.elevation = elevation
        self.transform = transform
        self.bounds = bounds

        self.height, self.width = cost.shape

        # WGS84 geodesic calculator
        self.geod = Geod(ellps="WGS84")

    # -----------------------------------------------------
    # Convert geographic coordinate to raster row/column
    # -----------------------------------------------------

    def coordinate_to_pixel(self, lon, lat):

        col, row = ~self.transform * (lon, lat)

        row = int(round(row))
        col = int(round(col))

        return row, col

    # -----------------------------------------------------
    # Convert raster row/column to geographic coordinate
    # -----------------------------------------------------

    def pixel_to_coordinate(self, row, col):

        lon, lat = self.transform * (col, row)

        return lon, lat

    # -----------------------------------------------------
    # Check whether pixel is inside grid
    # -----------------------------------------------------

    def valid_pixel(self, row, col):

        return (
            0 <= row < self.height
            and
            0 <= col < self.width
        )

    # -----------------------------------------------------
    # Check whether pixel can be traversed
    # -----------------------------------------------------

    def traversable(self, row, col):

        if not self.valid_pixel(row, col):
            return False

        value = self.cost[row, col]

        if not np.isfinite(value):
            return False

        if value <= 0:
            return False

        return True

    # -----------------------------------------------------
    # Find nearest traversable cell
    # -----------------------------------------------------

    def nearest_traversable(self, row, col, radius=20):

        if self.traversable(row, col):
            return row, col

        for r in range(1, radius + 1):

            for dr in range(-r, r + 1):

                for dc in range(-r, r + 1):

                    nr = row + dr
                    nc = col + dc

                    if self.traversable(nr, nc):
                        return nr, nc

        raise ValueError(
            "Could not find a traversable cell near the requested point."
        )

    # -----------------------------------------------------
    # Distance between two neighboring cells
    # -----------------------------------------------------

    def movement_distance(self, r1, c1, r2, c2):

        lon1, lat1 = self.pixel_to_coordinate(r1, c1)
        lon2, lat2 = self.pixel_to_coordinate(r2, c2)

        _, _, distance = self.geod.inv(
            lon1,
            lat1,
            lon2,
            lat2
        )

        return distance

    # -----------------------------------------------------
    # Heuristic
    #
    # Minimum traversal multiplier is 1.
    #
    # Therefore:
    #
    # heuristic = straight-line distance
    #
    # This remains admissible for our cost model.
    # -----------------------------------------------------

    def heuristic(self, row, col, goal_row, goal_col):

        return self.movement_distance(
            row,
            col,
            goal_row,
            goal_col
        )

    # -----------------------------------------------------
    # Generate 8 neighboring cells
    # -----------------------------------------------------

    def neighbors(self, row, col):

        directions = [
            (-1, -1),
            (-1,  0),
            (-1,  1),
            ( 0, -1),
            ( 0,  1),
            ( 1, -1),
            ( 1,  0),
            ( 1,  1)
        ]

        for dr, dc in directions:

            nr = row + dr
            nc = col + dc

            if self.traversable(nr, nc):

                yield nr, nc

    # -----------------------------------------------------
    # A* search
    # -----------------------------------------------------

    def find_path(
        self,
        start_row,
        start_col,
        goal_row,
        goal_col
    ):

        print("\nStarting A* search...")

        start = (start_row, start_col)
        goal = (goal_row, goal_col)

        # Priority queue:
        # (estimated_total_cost, row, col)

        open_set = []

        heapq.heappush(
            open_set,
            (
                0.0,
                start_row,
                start_col
            )
        )

        # Cost from start to each cell
        g_score = {
            start: 0.0
        }

        # Parent relationship
        came_from = {}

        visited = set()

        while open_set:

            _, current_row, current_col = heapq.heappop(
                open_set
            )

            current = (
                current_row,
                current_col
            )

            if current in visited:
                continue

            visited.add(current)

            # Goal reached
            if current == goal:

                print(
                    "Goal reached!"
                )

                print(
                    "Visited cells:",
                    len(visited)
                )

                return self.reconstruct_path(
                    came_from,
                    current
                )

            # Explore neighbors
            for nr, nc in self.neighbors(
                current_row,
                current_col
            ):

                neighbor = (nr, nc)

                if neighbor in visited:
                    continue

                distance = self.movement_distance(
                    current_row,
                    current_col,
                    nr,
                    nc
                )

                # Average traversal cost between cells
                average_cost = (
                    self.cost[
                        current_row,
                        current_col
                    ]
                    +
                    self.cost[
                        nr,
                        nc
                    ]
                ) / 2.0

                # Actual movement cost
                movement_cost = (
                    distance * average_cost
                )

                tentative_g = (
                    g_score[current]
                    +
                    movement_cost
                )

                if (
                    neighbor not in g_score
                    or
                    tentative_g < g_score[neighbor]
                ):

                    came_from[neighbor] = current

                    g_score[neighbor] = tentative_g

                    h = self.heuristic(
                        nr,
                        nc,
                        goal_row,
                        goal_col
                    )

                    f = tentative_g + h

                    heapq.heappush(
                        open_set,
                        (
                            f,
                            nr,
                            nc
                        )
                    )

        print(
            "No path could be found."
        )

        return None

    # -----------------------------------------------------
    # Reconstruct path
    # -----------------------------------------------------

    def reconstruct_path(
        self,
        came_from,
        current
    ):

        path = [current]

        while current in came_from:

            current = came_from[current]

            path.append(current)

        path.reverse()

        return path


# =========================================================
# Route statistics
# =========================================================

def calculate_route_statistics(
    path,
    cost,
    elevation,
    planner
):

    if not path:
        return None

    total_distance = 0.0
    elevation_gain = 0.0
    elevation_loss = 0.0
    total_cost = 0.0

    max_cell_cost = 0.0

    previous_elevation = None

    for i, (row, col) in enumerate(path):

        current_elevation = elevation[row, col]

        current_cost = cost[row, col]

        max_cell_cost = max(
            max_cell_cost,
            current_cost
        )

        total_cost += current_cost

        if previous_elevation is not None:

            elevation_change = (
                current_elevation
                -
                previous_elevation
            )

            if elevation_change > 0:

                elevation_gain += elevation_change

            elif elevation_change < 0:

                elevation_loss += abs(
                    elevation_change
                )

        previous_elevation = current_elevation

        if i > 0:

            previous_row, previous_col = path[i - 1]

            distance = planner.movement_distance(
                previous_row,
                previous_col,
                row,
                col
            )

            total_distance += distance

    average_cost = (
        total_cost / len(path)
    )

    return {
        "cells": len(path),
        "distance_m": total_distance,
        "distance_km": total_distance / 1000,
        "elevation_gain_m": elevation_gain,
        "elevation_loss_m": elevation_loss,
        "average_cost": average_cost,
        "maximum_cell_cost": max_cell_cost,
        "total_traversal_cost": total_cost
    }


# =========================================================
# Main
# =========================================================

def main():

    print("=" * 60)
    print("TERRAIN-AWARE A* ROUTE PLANNER")
    print("=" * 60)

    # -----------------------------------------------------
    # Load cost map
    # -----------------------------------------------------

    with rasterio.open(COST_PATH) as cost_src:

        cost = cost_src.read(1).astype(
            np.float32
        )

        transform = cost_src.transform

        bounds = cost_src.bounds

        nodata = cost_src.nodata

    # Convert NoData to infinity
    if nodata is not None:

        cost[
            cost == nodata
        ] = np.inf

    # -----------------------------------------------------
    # Load elevation
    # -----------------------------------------------------

    with rasterio.open(DEM_PATH) as dem_src:

        elevation = dem_src.read(1).astype(
            np.float32
        )

        dem_nodata = dem_src.nodata

    if dem_nodata is not None:

        elevation[
            elevation == dem_nodata
        ] = np.nan

    # -----------------------------------------------------
    # Create planner
    # -----------------------------------------------------

    planner = AStarPlanner(
        cost,
        elevation,
        transform,
        bounds
    )

    # -----------------------------------------------------
    # Convert coordinates to pixels
    # -----------------------------------------------------

    start_row, start_col = (
        planner.coordinate_to_pixel(
            START_LON,
            START_LAT
        )
    )

    goal_row, goal_col = (
        planner.coordinate_to_pixel(
            END_LON,
            END_LAT
        )
    )

    print("\nRequested start:")
    print(
        f"Longitude: {START_LON}"
    )
    print(
        f"Latitude : {START_LAT}"
    )

    print("\nRequested destination:")
    print(
        f"Longitude: {END_LON}"
    )
    print(
        f"Latitude : {END_LAT}"
    )

    # -----------------------------------------------------
    # Make sure start/end are traversable
    # -----------------------------------------------------

    start_row, start_col = (
        planner.nearest_traversable(
            start_row,
            start_col
        )
    )

    goal_row, goal_col = (
        planner.nearest_traversable(
            goal_row,
            goal_col
        )
    )

    print("\nActual start cell:")
    print(
        start_row,
        start_col
    )

    print("\nActual destination cell:")
    print(
        goal_row,
        goal_col
    )

    # -----------------------------------------------------
    # Run A*
    # -----------------------------------------------------

    path = planner.find_path(
        start_row,
        start_col,
        goal_row,
        goal_col
    )

    if path is None:

        print(
            "\nRoute planning failed."
        )

        return

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    stats = calculate_route_statistics(
        path,
        cost,
        elevation,
        planner
    )

    print("\n" + "=" * 60)
    print("ROUTE FOUND")
    print("=" * 60)

    print(
        "Path cells:",
        stats["cells"]
    )

    print(
        f"Distance: "
        f"{stats['distance_km']:.3f} km"
    )

    print(
        f"Elevation gain: "
        f"{stats['elevation_gain_m']:.1f} m"
    )

    print(
        f"Elevation loss: "
        f"{stats['elevation_loss_m']:.1f} m"
    )

    print(
        f"Average terrain cost: "
        f"{stats['average_cost']:.3f}"
    )

    print(
        f"Maximum cell cost: "
        f"{stats['maximum_cell_cost']:.3f}"
    )

    print(
        f"Total traversal cost: "
        f"{stats['total_traversal_cost']:.2f}"
    )

    # -----------------------------------------------------
    # Convert path to geographic coordinates
    # -----------------------------------------------------

    route_coordinates = []

    for row, col in path:

        lon, lat = planner.pixel_to_coordinate(
            row,
            col
        )

        route_coordinates.append(
            (lon, lat)
        )

    print("\nFirst route coordinate:")
    print(route_coordinates[0])

    print("\nLast route coordinate:")
    print(route_coordinates[-1])

    print("\nA* route planning completed successfully!")


if __name__ == "__main__":
    main()