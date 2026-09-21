import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from astar_planner import (
    AStarPlanner,
    START_LON,
    START_LAT,
    END_LON,
    END_LAT,
    calculate_route_statistics
)


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dem"

COST_PATH = DATA_DIR / "final_cost_with_no_go.tif"
DEM_PATH = DATA_DIR / "sample_dem.tif"

OUTPUT_PATH = DATA_DIR / "astar_route_visualization.png"


# =========================================================
# Main
# =========================================================

def main():

    print("=" * 60)
    print("A* ROUTE VISUALIZATION")
    print("=" * 60)

    # -----------------------------------------------------
    # Load cost map
    # -----------------------------------------------------

    with rasterio.open(COST_PATH) as src:

        cost = src.read(1).astype(np.float32)

        transform = src.transform
        bounds = src.bounds

        nodata = src.nodata

    if nodata is not None:
        cost[cost == nodata] = np.inf

    # -----------------------------------------------------
    # Load DEM
    # -----------------------------------------------------

    with rasterio.open(DEM_PATH) as src:

        elevation = src.read(1).astype(np.float32)

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
    # Convert start/end coordinates
    # -----------------------------------------------------

    start_row, start_col = planner.coordinate_to_pixel(
        START_LON,
        START_LAT
    )

    goal_row, goal_col = planner.coordinate_to_pixel(
        END_LON,
        END_LAT
    )

    # -----------------------------------------------------
    # Make sure points are traversable
    # -----------------------------------------------------

    start_row, start_col = planner.nearest_traversable(
        start_row,
        start_col
    )

    goal_row, goal_col = planner.nearest_traversable(
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

        print("\nNo route found.")
        return

    # -----------------------------------------------------
    # Route statistics
    # -----------------------------------------------------

    stats = calculate_route_statistics(
        path,
        cost,
        elevation,
        planner
    )

    print("\nRoute found successfully.")

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

    # -----------------------------------------------------
    # Convert route to geographic coordinates
    # -----------------------------------------------------

    route_lons = []
    route_lats = []

    for row, col in path:

        lon, lat = planner.pixel_to_coordinate(
            row,
            col
        )

        route_lons.append(lon)
        route_lats.append(lat)

    # -----------------------------------------------------
    # Create elevation map
    # -----------------------------------------------------

    plt.figure(figsize=(12, 8))

    plt.imshow(
        elevation,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper"
    )

    # -----------------------------------------------------
    # Plot route
    # -----------------------------------------------------

    plt.plot(
        route_lons,
        route_lats,
        linewidth=2.5,
        label="A* Recommended Route"
    )

    # -----------------------------------------------------
    # Start point
    # -----------------------------------------------------

    plt.scatter(
        START_LON,
        START_LAT,
        s=100,
        marker="o",
        label="Start"
    )

    # -----------------------------------------------------
    # Destination
    # -----------------------------------------------------

    plt.scatter(
        END_LON,
        END_LAT,
        s=100,
        marker="X",
        label="Destination"
    )

    # -----------------------------------------------------
    # Labels
    # -----------------------------------------------------

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.title(
        "Terrain-Aware A* Route Planning"
    )

    plt.colorbar(
        label="Elevation (m)"
    )

    plt.legend()

    plt.grid(
        alpha=0.3
    )

    plt.tight_layout()

    # -----------------------------------------------------
    # Save figure
    # -----------------------------------------------------

    plt.savefig(
        OUTPUT_PATH,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()

    print("\nRoute visualization saved:")
    print(OUTPUT_PATH)

    print("=" * 60)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    main()