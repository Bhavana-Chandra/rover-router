"""Classical baselines: nearest-neighbour greedy and brute-force exact."""
from itertools import permutations

from lake import manhattan, route_length


def greedy(dock, debris):
    """Always go to the nearest unvisited spot. Ties go to the lower index."""
    remaining = list(range(len(debris)))
    here, order = dock, []
    while remaining:
        nxt = min(remaining, key=lambda i: (manhattan(here, debris[i]), i))
        order.append(nxt)
        remaining.remove(nxt)
        here = debris[nxt]
    return order, route_length(dock, debris, order)


def exact(dock, debris):
    """Try all K! orders. Fine for K <= 8, and it gives us the true optimum."""
    best = min(permutations(range(len(debris))),
               key=lambda o: route_length(dock, debris, o))
    return list(best), route_length(dock, debris, best)
