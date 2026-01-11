#!/usr/bin/env python3
"""
Biketerra GPX Exporter CLI

Fetches route data from Biketerra and exports it as a GPX file.
"""

import argparse
import sys
from datetime import datetime, timezone

import gpxpy
import gpxpy.gpx
import requests


def fetch_route_data(route_id: str) -> dict:
    """Fetch route data from Biketerra's API endpoint."""
    url = f"https://biketerra.com/routes/{route_id}/__data.json"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def deref(data: list, index: int):
    """Dereference a pointer index in the Biketerra data array."""
    return data[index]


def extract_route_info(data: dict) -> tuple[list[dict], dict, str]:
    """
    Extract route data from Biketerra JSON structure.

    Returns:
        tuple of (points, metadata, route_name)
    """
    route_data = data["nodes"][2]["data"]
    route_info = route_data[0]

    lat_lng_idx = route_info["latLngData"]
    route_meta_idx = route_info["route"]

    # Extract metadata
    route_meta_struct = deref(route_data, route_meta_idx)
    metadata = {}

    fields = ["id", "title", "distance", "elevation",
              "geo_city", "geo_county", "geo_state", "geo_country"]

    for field in fields:
        if field in route_meta_struct:
            idx = route_meta_struct[field]
            if isinstance(idx, int) and idx > 0:
                metadata[field] = deref(route_data, idx)

    route_name = metadata.get("title") or f"Route {metadata.get('id', 'Unknown')}"

    # Extract track points
    point_indices = deref(route_data, lat_lng_idx)
    points = []

    for point_idx in point_indices:
        point_refs = deref(route_data, point_idx)

        lat = deref(route_data, point_refs[0])
        lng = deref(route_data, point_refs[1])
        ele = deref(route_data, point_refs[2])

        points.append({"lat": lat, "lng": lng, "ele": ele})

    return points, metadata, route_name


def build_gpx(points: list[dict], route_name: str, metadata: dict) -> gpxpy.gpx.GPX:
    """Build a GPX object from track points and metadata."""
    gpx = gpxpy.gpx.GPX()
    gpx.creator = "Biketerra GPX Exporter"

    # Build description
    desc_parts = []
    if metadata.get("geo_city"):
        location_parts = [
            metadata.get("geo_city"),
            metadata.get("geo_state"),
            metadata.get("geo_country")
        ]
        location = ", ".join(filter(None, location_parts))
        if location:
            desc_parts.append(f"Location: {location}")

    if metadata.get("distance"):
        dist_km = metadata["distance"] / 100000  # centimeters to km
        desc_parts.append(f"Distance: {dist_km:.2f} km")

    if metadata.get("elevation"):
        ele_m = metadata["elevation"] / 100  # centimeters to meters
        desc_parts.append(f"Elevation gain: {round(ele_m)} m")

    description = "; ".join(desc_parts)

    # Set metadata
    gpx.name = route_name
    gpx.description = description
    gpx.time = datetime.now(timezone.utc)

    # Create track
    track = gpxpy.gpx.GPXTrack()
    track.name = route_name
    gpx.tracks.append(track)

    # Create segment
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    # Add track points
    for point in points:
        track_point = gpxpy.gpx.GPXTrackPoint(
            latitude=point["lat"],
            longitude=point["lng"],
            elevation=point["ele"]
        )
        segment.points.append(track_point)

    return gpx


def main():
    parser = argparse.ArgumentParser(
        description="Export a Biketerra route as a GPX file."
    )
    parser.add_argument(
        "route_id",
        help="The Biketerra route ID (e.g., 8771)"
    )
    parser.add_argument(
        "-o", "--out",
        dest="output",
        help="Output filename (default: <route_id>.gpx)"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    args = parser.parse_args()

    route_id = args.route_id
    output_file = args.output or f"{route_id}.gpx"

    try:
        print(f"Fetching route {route_id}...")
        data = fetch_route_data(route_id)

        points, metadata, route_name = extract_route_info(data)

        if not points:
            print("Error: No track points found in route data", file=sys.stderr)
            sys.exit(1)

        gpx = build_gpx(points, route_name, metadata)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(gpx.to_xml())

        print(f"Wrote {output_file} ({len(points)} points)")
        print(f"Route: {route_name}")
        if metadata.get("distance"):
            print(f"Distance: {metadata['distance'] / 100000:.2f} km")
        if metadata.get("elevation"):
            print(f"Elevation: {metadata['elevation'] / 100:.0f} m")

    except requests.HTTPError as e:
        print(f"Error fetching route: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing route data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
