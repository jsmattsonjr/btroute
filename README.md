# btroute

A CLI tool to export [Biketerra](https://biketerra.com) routes as GPX files.

## Installation

Requires Python 3.10+.

```bash
pip install gpxpy requests
```

## Usage

```bash
python btroute.py <route_id> [-o output.gpx]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `route_id` | The Biketerra route ID (from the URL) |
| `-o`, `--out` | Output filename (default: `<route_id>.gpx`) |
| `-v`, `--version` | Show version and exit |

### Examples

Export route 8771 to the default filename:

```bash
python btroute.py 8771
# Creates 8771.gpx
```

Export with a custom filename:

```bash
python btroute.py 8771 -o my-route.gpx
```

## Output

The generated GPX file includes:

- Track points with latitude, longitude, and elevation
- Route name and description
- Location, distance, and elevation gain metadata
