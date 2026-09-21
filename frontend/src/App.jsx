import { useState, useMemo, useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  Popup,
  Polyline,
  CircleMarker,
  useMapEvents,
} from "react-leaflet";

import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

import "leaflet/dist/leaflet.css";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

// ============================================================
// MAP CLICK HANDLER
// ============================================================

function MapClickHandler({ mode, setStart, setDestination }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;

      if (mode === "start") {
        setStart({
          lat,
          lng,
        });
      }

      if (mode === "destination") {
        setDestination({
          lat,
          lng,
        });
      }
    },
  });

  return null;
}

// ============================================================
// 3D TERRAIN PREVIEW
// ============================================================

function TerrainSurface({ elevations }) {
  const geometry = useMemo(() => {
    if (!elevations || elevations.length === 0) {
      return null;
    }

    const rows = elevations.length;
    const cols = elevations[0].length;

    const width = 45;
    const depth = 32;
    const verticalScale = 12;

    let minElevation = Infinity;
    let maxElevation = -Infinity;

    for (let z = 0; z < rows; z++) {
      for (let x = 0; x < cols; x++) {
        const value = elevations[z][x];

        minElevation = Math.min(
          minElevation,
          value
        );

        maxElevation = Math.max(
          maxElevation,
          value
        );
      }
    }

    const elevationRange =
      maxElevation - minElevation || 1;

    const positions = [];
    const indices = [];
    const colors = [];

    // Create terrain vertices
    for (let z = 0; z < rows; z++) {
      for (let x = 0; x < cols; x++) {

        const px =
          (x / (cols - 1) - 0.5) * width;

        const pz =
          (z / (rows - 1) - 0.5) * depth;

        const normalized =
          (elevations[z][x] - minElevation) /
          elevationRange;

        const height =
          normalized * verticalScale;

        positions.push(
          px,
          height,
          pz
        );

        // Elevation-based terrain colors
        const color = new THREE.Color();

        if (normalized < 0.25) {
          color.setRGB(
            0.12,
            0.28,
            0.18
          );
        } else if (normalized < 0.5) {
          color.setRGB(
            0.28,
            0.42,
            0.20
          );
        } else if (normalized < 0.75) {
          color.setRGB(
            0.48,
            0.40,
            0.24
          );
        } else {
          color.setRGB(
            0.72,
            0.72,
            0.68
          );
        }

        colors.push(
          color.r,
          color.g,
          color.b
        );
      }
    }

    // Create triangles
    for (let z = 0; z < rows - 1; z++) {
      for (let x = 0; x < cols - 1; x++) {

        const a =
          z * cols + x;

        const b = a + 1;

        const c =
          a + cols;

        const d = c + 1;

        indices.push(a, c, b);
        indices.push(b, c, d);
      }
    }

    const buffer =
      new THREE.BufferGeometry();

    buffer.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        positions,
        3
      )
    );

    buffer.setAttribute(
      "color",
      new THREE.Float32BufferAttribute(
        colors,
        3
      )
    );

    buffer.setIndex(indices);

    buffer.computeVertexNormals();

    return buffer;
  }, [elevations]);

  if (!geometry) {
    return null;
  }

  return (
    <mesh
      geometry={geometry}
      rotation={[-0.02, 0, 0]}
    >
      <meshStandardMaterial
        vertexColors
        roughness={0.9}
        metalness={0}
      />
    </mesh>
  );
}

// ============================================================
// 3D A* ROUTE
// ============================================================

function Route3D({
  route,
  terrain
}) {
  const routeGeometry = useMemo(() => {

    if (
      !route ||
      route.length < 2 ||
      !terrain
    ) {
      return null;
    }

    const {
      west,
      south,
      east,
      north
    } = terrain.bounds;

    const rows =
      terrain.elevations.length;

    const cols =
      terrain.elevations[0].length;

    const width = 45;
    const depth = 32;
    const verticalScale = 12;

    const elevationGrid =
      terrain.elevations;

    let minElevation = Infinity;
    let maxElevation = -Infinity;

    for (let z = 0; z < rows; z++) {
      for (let x = 0; x < cols; x++) {

        const value =
          elevationGrid[z][x];

        minElevation =
          Math.min(
            minElevation,
            value
          );

        maxElevation =
          Math.max(
            maxElevation,
            value
          );
      }
    }

    const elevationRange =
      maxElevation - minElevation || 1;

    // Bilinear elevation interpolation
    function getElevation(
      normalizedX,
      normalizedZ
    ) {

      const gridX =
        normalizedX * (cols - 1);

      const gridZ =
        normalizedZ * (rows - 1);

      const x0 =
        Math.floor(gridX);

      const z0 =
        Math.floor(gridZ);

      const x1 =
        Math.min(
          x0 + 1,
          cols - 1
        );

      const z1 =
        Math.min(
          z0 + 1,
          rows - 1
        );

      const fx =
        gridX - x0;

      const fz =
        gridZ - z0;

      const h00 =
        elevationGrid[z0][x0];

      const h10 =
        elevationGrid[z0][x1];

      const h01 =
        elevationGrid[z1][x0];

      const h11 =
        elevationGrid[z1][x1];

      const h0 =
        h00 * (1 - fx) +
        h10 * fx;

      const h1 =
        h01 * (1 - fx) +
        h11 * fx;

      return (
        h0 * (1 - fz) +
        h1 * fz
      );
    }

    const points = [];

    for (const point of route) {

      // Leaflet route format:
      // [latitude, longitude]

      const lat = point[0];
      const lon = point[1];

      // Convert geographic coordinates
      // into normalized DEM coordinates.

      const normalizedX =
        (lon - west) /
        (east - west);

      const normalizedZ =
        1 -
        (lat - south) /
        (north - south);

      // Ignore points outside DEM
      if (
        normalizedX < 0 ||
        normalizedX > 1 ||
        normalizedZ < 0 ||
        normalizedZ > 1
      ) {
        continue;
      }

      const px =
        (normalizedX - 0.5) *
        width;

      const pz =
        (normalizedZ - 0.5) *
        depth;

      const elevation =
        getElevation(
          normalizedX,
          normalizedZ
        );

      const normalizedElevation =
        (elevation - minElevation) /
        elevationRange;

      const py =
        normalizedElevation *
          verticalScale +
        0.35;

      points.push(
        new THREE.Vector3(
          px,
          py,
          pz
        )
      );
    }

    if (points.length < 2) {
      return null;
    }

    const geometry =
      new THREE.BufferGeometry();

    geometry.setFromPoints(points);

    return geometry;

  }, [route, terrain]);

  if (!routeGeometry) {
    return null;
  }

  return (
    <primitive
      object={
        new THREE.Line(
          routeGeometry,
          new THREE.LineBasicMaterial({
            color: "#f3b63f",
            linewidth: 4,
          })
        )
      }
    />
  );
}

// ============================================================
// 3D POINT MARKERS
// ============================================================

function PointMarker({
  position,
  type
}) {
  const color =
    type === "start"
      ? "#39d98a"
      : "#ff6b5f";

  return (
    <mesh position={position}>
      <sphereGeometry
        args={[0.45, 24, 24]}
      />

      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.6}
      />
    </mesh>
  );
}


// ============================================================
// 3D VIEW
// ============================================================

function Terrain3D({ route = [] }) {
  const [terrain, setTerrain] =
    useState(null);

  const [error, setError] =
    useState(null);

  useEffect(() => {

    async function loadTerrain() {

      try {

        setError(null);

        const response =
          await fetch(
            `${API_URL}/terrain/grid`
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
            "Failed to load terrain."
          );
        }

        if (
          !data.success ||
          !data.elevations
        ) {
          throw new Error(
            "Invalid terrain data received."
          );
        }

        setTerrain(data);

      } catch (err) {

        console.error(
          "Terrain loading error:",
          err
        );

        setError(
          err.message
        );
      }
    }

    loadTerrain();

  }, []);

  // ----------------------------------------------------------
  // Calculate 3D start/end positions from the route
  // ----------------------------------------------------------

  const markerPositions =
    useMemo(() => {

      if (
        !terrain ||
        !route ||
        route.length === 0
      ) {
        return null;
      }

      const {
        west,
        south,
        east,
        north
      } = terrain.bounds;

      const rows =
        terrain.elevations.length;

      const cols =
        terrain.elevations[0].length;

      const width = 45;
      const depth = 32;
      const verticalScale = 12;

      let minElevation = Infinity;
      let maxElevation = -Infinity;

      for (let z = 0; z < rows; z++) {
        for (let x = 0; x < cols; x++) {

          const value =
            terrain.elevations[z][x];

          minElevation =
            Math.min(
              minElevation,
              value
            );

          maxElevation =
            Math.max(
              maxElevation,
              value
            );
        }
      }

      const elevationRange =
        maxElevation - minElevation || 1;

      function positionFromRoutePoint(
        point
      ) {

        const lat = point[0];
        const lon = point[1];

        const x =
          (lon - west) /
          (east - west);

        const z =
          1 -
          (lat - south) /
          (north - south);

        const gridX =
          Math.max(
            0,
            Math.min(
              cols - 1,
              x * (cols - 1)
            )
          );

        const gridZ =
          Math.max(
            0,
            Math.min(
              rows - 1,
              z * (rows - 1)
            )
          );

        const xIndex =
          Math.round(gridX);

        const zIndex =
          Math.round(gridZ);

        const elevation =
          terrain.elevations[
            zIndex
          ][xIndex];

        const px =
          (x - 0.5) * width;

        const pz =
          (z - 0.5) * depth;

        const py =
          (
            (elevation -
              minElevation) /
            elevationRange
          ) *
          verticalScale +
          0.7;

        return [
          px,
          py,
          pz
        ];
      }

      return {
        start:
          positionFromRoutePoint(
            route[0]
          ),

        destination:
          positionFromRoutePoint(
            route[route.length - 1]
          ),
      };

    }, [terrain, route]);

  return (
    <div className="terrain-3d">

      {!terrain && !error && (
        <div className="terrain-loading">

          <div className="loading-spinner">
            ⟳
          </div>

          <strong>
            Loading real terrain...
          </strong>

          <small>
            Reading Manali DEM elevation data
          </small>

        </div>
      )}

      {error && (
        <div className="terrain-loading">

          <div className="loading-spinner">
            ⚠
          </div>

          <strong>
            Terrain loading failed
          </strong>

          <small>
            {error}
          </small>

        </div>
      )}

      {terrain && (
        <Canvas
          camera={{
            position: [
              25,
              18,
              28
            ],
            fov: 45,
          }}
        >

          {/* Lighting */}

          <ambientLight
            intensity={1.1}
          />

          <directionalLight
            position={[
              10,
              25,
              15
            ]}
            intensity={2.5}
          />

          <directionalLight
            position={[
              -15,
              10,
              -10
            ]}
            intensity={0.8}
          />

          {/* REAL DEM */}

          <TerrainSurface
            elevations={
              terrain.elevations
            }
          />

          {/* A* ROUTE */}

          <Route3D
            route={route}
            terrain={terrain}
          />

          {/* START */}

          {markerPositions && (
            <PointMarker
              position={
                markerPositions.start
              }
              type="start"
            />
          )}

          {/* DESTINATION */}

          {markerPositions && (
            <PointMarker
              position={
                markerPositions.destination
              }
              type="destination"
            />
          )}

          {/* Ground grid */}

          <gridHelper
            args={[60, 30]}
            position={[
              0,
              -1,
              0
            ]}
          />

          {/* Camera controls */}

          <OrbitControls
            enableDamping
            dampingFactor={0.08}
            minDistance={10}
            maxDistance={70}
          />

        </Canvas>
      )}

      {/* 3D LABEL */}

      <div className="three-label">

        <span>
          3D TERRAIN
        </span>

        <small>
          Real DEM • A* Route • Drag to rotate • Scroll to zoom
        </small>

      </div>

      {/* DEM INFORMATION */}

      {terrain && (
        <div className="dem-info">

          <span>
            REAL DEM
          </span>

          <strong>
            {terrain.elevation_min.toFixed(0)}
            –
            {terrain.elevation_max.toFixed(0)}
            {" "}m
          </strong>

          <small>
            Manali Region
          </small>

        </div>
      )}

      {/* ROUTE LEGEND */}

            {/* ROUTE LEGEND */}

      {route && route.length > 0 && (
        <div className="route-3d-legend">

          <div>
            <span className="legend-circle start-3d"></span>
            Start
          </div>

          <div>
            <span className="legend-circle route-3d"></span>
            A* Route
          </div>

          <div>
            <span className="legend-circle destination-3d"></span>
            Destination
          </div>

        </div>
      )}

    </div>
  );
}

// ============================================================
// MAIN APP
// ============================================================

function App() {
  const [start, setStart] = useState({
    lat: 32.22,
    lng: 77.17,
  });

  const [destination, setDestination] =
    useState({
      lat: 32.28,
      lng: 77.27,
    });

  const [preference, setPreference] =
    useState("terrain");

  const [maxSlope, setMaxSlope] =
    useState(45);

  const [mode, setMode] =
    useState("start");

  const [view, setView] =
    useState("2d");

  const [route, setRoute] =
    useState([]);

  const [stats, setStats] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [layers, setLayers] =
    useState({
      water: true,
      forest: true,
      roads: true,
      slope: false,
    });

  // ============================================================
  // GENERATE ROUTE
  // ============================================================

  async function generateRoute() {
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/route/plan`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            start_lon: start.lng,
            start_lat: start.lat,

            goal_lon: destination.lng,
            goal_lat: destination.lat,

            preference: preference,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Route calculation failed"
        );
      }

      if (
        !data.route_coordinates ||
        data.route_coordinates.length === 0
      ) {
        throw new Error(
          "No route was returned by the server."
        );
      }

      const coordinates =
        data.route_coordinates.map(
          ([lng, lat]) => [lat, lng]
        );

      setRoute(coordinates);

      if (data.statistics) {
        setStats(data.statistics);
      } else {
        setStats({
          distance_km:
            data.distance_km ?? 0,

          elevation_gain_m:
            data.elevation_gain_m ?? 0,

          elevation_loss_m:
            data.elevation_loss_m ?? 0,

          average_terrain_cost:
            data.average_terrain_cost ?? 0,

          maximum_terrain_cost:
            data.maximum_terrain_cost ?? 0,
        });
      }
    } catch (error) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // CLEAR ROUTE
  // ============================================================

  function clearRoute() {
    setRoute([]);
    setStats(null);
  }

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="app">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-icon">
            ⛰
          </div>

          <div>
            <h1>
              Terrain<span>Route</span>
            </h1>

            <p>
              Terrain-Aware Route Planning System
            </p>
          </div>

        </div>

        <div className="header-right">

          <div className="location">
            📍 Manali Region
          </div>

          <div className="api-status">
            <span></span>
            API ONLINE
          </div>

        </div>

      </header>

      {/* ================================================== */}
      {/* MAIN */}
      {/* ================================================== */}

      <div className="main-layout">

        {/* ================================================== */}
        {/* SIDEBAR */}
        {/* ================================================== */}

        <aside className="sidebar">

          <div className="panel-title">

            <div>
              <span className="eyebrow">
                ROUTE PLANNER
              </span>

              <h2>
                Plan your route
              </h2>
            </div>

          </div>

          {/* START */}

          <div className="point-card">

            <div className="point-icon start-icon">
              ●
            </div>

            <div className="point-content">

              <span>
                START POINT
              </span>

              <strong>
                {start.lat.toFixed(5)},{" "}
                {start.lng.toFixed(5)}
              </strong>

            </div>

            <button
              onClick={() =>
                setMode("start")
              }
              className={
                mode === "start"
                  ? "active-mini"
                  : ""
              }
            >
              Set
            </button>

          </div>

          {/* DESTINATION */}

          <div className="point-card">

            <div className="point-icon end-icon">
              ◆
            </div>

            <div className="point-content">

              <span>
                DESTINATION
              </span>

              <strong>
                {destination.lat.toFixed(5)},{" "}
                {destination.lng.toFixed(5)}
              </strong>

            </div>

            <button
              onClick={() =>
                setMode("destination")
              }
              className={
                mode === "destination"
                  ? "active-mini"
                  : ""
              }
            >
              Set
            </button>

          </div>

          {/* PREFERENCE */}

          <div className="control-section">

            <label>
              OPTIMIZATION PREFERENCE
            </label>

            <select
              value={preference}
              onChange={(e) =>
                setPreference(e.target.value)
              }
            >
              <option value="shortest">
                Shortest Route
              </option>

              <option value="terrain">
                Terrain-Friendly
              </option>

              <option value="elevation">
                Lowest Elevation Gain
              </option>

              <option value="balanced">
                Balanced
              </option>
            </select>

          </div>

          {/* SLOPE */}

          <div className="control-section">

            <div className="slider-header">

              <label>
                MAXIMUM SLOPE
              </label>

              <strong>
                {maxSlope}°
              </strong>

            </div>

            <input
              type="range"
              min="20"
              max="60"
              value={maxSlope}
              onChange={(e) =>
                setMaxSlope(
                  Number(e.target.value)
                )
              }
            />

            <div className="slider-labels">
              <span>20°</span>
              <span>60°</span>
            </div>

          </div>

          {/* GENERATE */}

          <button
            className="generate-button"
            onClick={generateRoute}
            disabled={loading}
          >
            <span>
              {loading ? "⟳" : "✦"}
            </span>

            {loading
              ? "CALCULATING ROUTE..."
              : "FIND OPTIMAL ROUTE"}
          </button>

          {route.length > 0 && (
            <button
              className="clear-button"
              onClick={clearRoute}
            >
              Clear Route
            </button>
          )}

          {/* MAP INSTRUCTION */}

          <div className="instruction-card">

            <div className="instruction-icon">
              ⓘ
            </div>

            <div>

              <strong>
                Map interaction
              </strong>

              <p>
                Select <b>Set</b> beside Start or
                Destination, then click anywhere
                on the map.
              </p>

            </div>

          </div>

          {/* LAYERS */}

          <div className="layers-section">

            <label>
              MAP LAYERS
            </label>

            <LayerToggle
              label="Water Bodies"
              checked={layers.water}
              onChange={() =>
                setLayers({
                  ...layers,
                  water: !layers.water,
                })
              }
              icon="💧"
            />

            <LayerToggle
              label="Forest / Vegetation"
              checked={layers.forest}
              onChange={() =>
                setLayers({
                  ...layers,
                  forest: !layers.forest,
                })
              }
              icon="🌲"
            />

            <LayerToggle
              label="Road Network"
              checked={layers.roads}
              onChange={() =>
                setLayers({
                  ...layers,
                  roads: !layers.roads,
                })
              }
              icon="🛣"
            />

            <LayerToggle
              label="Slope Danger"
              checked={layers.slope}
              onChange={() =>
                setLayers({
                  ...layers,
                  slope: !layers.slope,
                })
              }
              icon="▲"
            />

          </div>

        </aside>

        {/* ================================================== */}
        {/* RIGHT CONTENT */}
        {/* ================================================== */}

        <main className="content">

          {/* VIEW SWITCHER */}

          <div className="view-toolbar">

            <div className="view-tabs">

              <button
                className={
                  view === "2d"
                    ? "view-active"
                    : ""
                }
                onClick={() =>
                  setView("2d")
                }
              >
                ◫ 2D MAP
              </button>

              <button
                className={
                  view === "3d"
                    ? "view-active"
                    : ""
                }
                onClick={() =>
                  setView("3d")
                }
              >
                ◈ 3D TERRAIN
              </button>

            </div>

            <div className="view-info">
              {view === "2d"
                ? "Interactive terrain map"
                : "Interactive elevation model"}
            </div>

          </div>

          {/* MAP */}

          <div className="map-card">

            {view === "2d" ? (

              <MapContainer
                center={[32.25, 77.22]}
                zoom={11}
                className="map"
              >

                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapClickHandler
                  mode={mode}
                  setStart={setStart}
                  setDestination={setDestination}
                />

                {/* START */}

                <CircleMarker
                  center={[
                    start.lat,
                    start.lng,
                  ]}
                  radius={9}
                  pathOptions={{
                    color: "#ffffff",
                    weight: 3,
                    fillColor: "#39d98a",
                    fillOpacity: 1,
                  }}
                >
                  <Popup>
                    <b>Start Point</b>
                  </Popup>
                </CircleMarker>

                {/* DESTINATION */}

                <CircleMarker
                  center={[
                    destination.lat,
                    destination.lng,
                  ]}
                  radius={9}
                  pathOptions={{
                    color: "#ffffff",
                    weight: 3,
                    fillColor: "#ff6b5f",
                    fillOpacity: 1,
                  }}
                >
                  <Popup>
                    <b>Destination</b>
                  </Popup>
                </CircleMarker>

                {/* ROUTE */}

                {route.length > 0 && (
                  <Polyline
                    positions={route}
                    pathOptions={{
                      color: "#f3b63f",
                      weight: 6,
                    }}
                  />
                )}

              </MapContainer>

            ) : (

              <Terrain3D route={route} />

            )}

            {/* MAP OVERLAY */}

            <div className="map-overlay">

              <div className="legend-item">
                <span className="legend-dot start-dot"></span>
                Start
              </div>

              <div className="legend-item">
                <span className="legend-dot end-dot"></span>
                Destination
              </div>

              {route.length > 0 && (
                <div className="legend-item">
                  <span className="legend-line"></span>
                  A* Route
                </div>
              )}

            </div>

          </div>

          {/* ================================================== */}
          {/* RESULTS */}
          {/* ================================================== */}

          <section className="analysis-panel">

            <div className="analysis-header">

              <div>

                <span className="eyebrow">
                  ROUTE ANALYSIS
                </span>

                <h2>
                  Planning results
                </h2>

              </div>

              {stats && (
                <div className="recommendation-badge">
                  ✓ Route calculated
                </div>
              )}

            </div>

            {!stats ? (

              <div className="empty-results">

                <div className="empty-icon">
                  ⛰
                </div>

                <h3>
                  Ready to plan
                </h3>

                <p>
                  Set your start and destination,
                  choose a preference and find a
                  route.
                </p>

              </div>

            ) : (

              <>

                <div className="stats-grid">

                  <StatCard
                    icon="↔"
                    label="DISTANCE"
                    value={`${Number(
                      stats.distance_km
                    ).toFixed(2)} km`}
                  />

                  <StatCard
                    icon="↗"
                    label="ELEVATION GAIN"
                    value={`${Number(
                      stats.elevation_gain_m
                    ).toFixed(0)} m`}
                  />

                  <StatCard
                    icon="↘"
                    label="ELEVATION LOSS"
                    value={`${Number(
                      stats.elevation_loss_m
                    ).toFixed(0)} m`}
                  />

                  <StatCard
                    icon="◈"
                    label="AVG TERRAIN COST"
                    value={Number(
                      stats.average_terrain_cost
                    ).toFixed(3)}
                  />

                  <StatCard
                    icon="▲"
                    label="MAX TERRAIN COST"
                    value={Number(
                      stats.maximum_terrain_cost
                    ).toFixed(3)}
                  />

                  <StatCard
                    icon="⌁"
                    label="PATH CELLS"
                    value={route.length}
                  />

                </div>

                <div className="recommendation">

                  <div className="recommendation-icon">
                    ✓
                  </div>

                  <div>

                    <span>
                      RECOMMENDED ROUTE
                    </span>

                    <h3>
                      {preference === "terrain"
                        ? "Terrain-Friendly Route"
                        : preference === "shortest"
                          ? "Shortest Route"
                          : preference === "elevation"
                            ? "Low Elevation-Gain Route"
                            : "Balanced Route"}
                    </h3>

                    <p>
                      Route generated using terrain
                      cost analysis, configured
                      constraints and A* pathfinding.
                    </p>

                  </div>

                </div>

              </>

            )}

          </section>

        </main>

      </div>

    </div>
  );
}

// ============================================================
// LAYER TOGGLE
// ============================================================

function LayerToggle({
  label,
  checked,
  onChange,
  icon,
}) {
  return (
    <button
      className="layer-toggle"
      onClick={onChange}
    >

      <span className="layer-icon">
        {icon}
      </span>

      <span>
        {label}
      </span>

      <span
        className={
          checked
            ? "checkbox checked"
            : "checkbox"
        }
      >
        {checked ? "✓" : ""}
      </span>

    </button>
  );
}

// ============================================================
// STAT CARD
// ============================================================

function StatCard({
  icon,
  label,
  value,
}) {
  return (
    <div className="stat-card">

      <div className="stat-icon">
        {icon}
      </div>

      <div>

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </div>

    </div>
  );
}

export default App;