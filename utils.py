from math import sqrt


def compute_route(coords):
    # Simple nearest neighbour heuristic for TSP-style route
    if not coords:
        return []
    unvisited = coords[:]
    route = [unvisited.pop(0)]
    while unvisited:
        last = route[-1]
        # find nearest
        dists = [(i, (last[0]-c[0])**2 + (last[1]-c[1])**2) for i, c in enumerate(unvisited)]
        i, _ = min(dists, key=lambda x: x[1])
        route.append(unvisited.pop(i))
    return route


def format_route(route):
    if not route:
        return 'No coordinates assigned.'
    lines = []
    for i, (lat, lon) in enumerate(route, 1):
        lines.append(f"{i}. {lat:.6f}, {lon:.6f}")
    return '\n'.join(lines)


def distance(a, b):
    return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
