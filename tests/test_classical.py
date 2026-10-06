import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lake import make_lake, manhattan, route_length, is_valid_order
from classical import greedy, exact


def test_manhattan():
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((2, 2), (2, 2)) == 0


def test_route_length_by_hand():
    # dock (0,0) -> (1,0) -> (1,2) -> dock = 1 + 2 + 3
    assert route_length((0, 0), [(1, 0), (1, 2)], [0, 1]) == 6


def test_lake_is_reproducible_and_distinct():
    a = make_lake(7)
    assert a == make_lake(7)
    dock, debris = a
    assert len(set(debris)) == 4 and dock not in debris


def test_exact_matches_manual_enumeration():
    # Collinear spots: the best route goes out and back, length 2 * farthest.
    order, length = exact((0, 0), [(3, 0), (1, 0), (2, 0)])
    assert length == 6 and is_valid_order(order, 3)


def test_greedy_valid_and_never_beats_exact():
    for seed in range(30):
        dock, debris = make_lake(seed)
        g_order, g_len = greedy(dock, debris)
        _, e_len = exact(dock, debris)
        assert is_valid_order(g_order, 4)
        assert g_len >= e_len
        assert route_length(dock, debris, g_order) == g_len
