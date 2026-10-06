"""Simulated lake: a small grid with a dock and some floating debris."""
import random

DOCK = (0, 0)  # the rover starts and ends here


def make_lake(seed, size=5, k=4):
    """Return (dock, debris) with k distinct debris cells, reproducible by seed."""
    rng = random.Random(seed)
    cells = [(x, y) for x in range(size) for y in range(size) if (x, y) != DOCK]
    debris = rng.sample(cells, k)
    return DOCK, debris


def manhattan(a, b):
    # The rover moves along grid lines, so Manhattan distance is the real travel cost.
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def route_length(dock, debris, order):
    """Length of dock -> debris[order[0]] -> ... -> debris[order[-1]] -> dock."""
    pts = [dock] + [debris[i] for i in order] + [dock]
    return sum(manhattan(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def is_valid_order(order, k):
    return sorted(order) == list(range(k))
