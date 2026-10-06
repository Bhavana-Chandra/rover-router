import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lake import make_lake, route_length
from classical import exact
from qaoa_tsp import build_qubo, decode, all_energies, default_penalty


def best_bitstring_route(dock, debris, penalty=None):
    k = len(debris)
    Q, c = build_qubo(dock, debris, penalty)
    e = all_energies(Q, c)
    best = int(np.argmin(e))
    bits = [(best >> v) & 1 for v in range(k * k)]
    return decode(bits, k), e[best]


def test_qubo_minimum_is_the_exact_route_k3():
    for seed in range(20):
        dock, debris = make_lake(seed, k=3)
        order, e = best_bitstring_route(dock, debris)
        assert order is not None
        _, opt = exact(dock, debris)
        assert route_length(dock, debris, order) == opt
        assert abs(e - opt) < 1e-9  # valid routes have zero penalty


def test_qubo_minimum_is_the_exact_route_k4():
    for seed in range(10):
        dock, debris = make_lake(seed, k=4)
        order, e = best_bitstring_route(dock, debris)
        assert order is not None
        _, opt = exact(dock, debris)
        assert route_length(dock, debris, order) == opt


def test_decode_rejects_invalid():
    assert decode([1, 0, 0, 0, 1, 0, 0, 0, 1], 3) == [0, 1, 2]
    assert decode([1, 1, 0, 0, 0, 0, 0, 0, 1], 3) is None
    assert decode([0] * 9, 3) is None
