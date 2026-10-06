"""Run all methods on one lake and collect comparable rows."""
import numpy as np

from lake import make_lake, route_length
from classical import greedy, exact
from qaoa_tsp import solve_qaoa, decode


def random_sampling(dock, debris, shots=4096, seed=0):
    """Control: draw uniform random bitstrings, keep the best valid route.

    This uses the same shot count as QAOA, so it shows how much of QAOA's
    result is just luck from sampling many bitstrings.
    """
    k = len(debris)
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, size=(shots, k * k))
    best, valid = None, 0
    for row in bits:
        order = decode(row, k)
        if order is None:
            continue
        valid += 1
        length = route_length(dock, debris, order)
        if best is None or length < best[1]:
            best = (order, length)
    return {"best_order": best[0] if best else None,
            "best_length": best[1] if best else None,
            "valid_fraction": valid / shots}


def run_seed(seed, k=4, reps_list=(1, 2), shots=4096):
    """Return a list of row dicts, one per method, for this seed."""
    dock, debris = make_lake(seed, k=k)
    _, opt = exact(dock, debris)
    rows = []

    def row(method, length, **extra):
        rows.append({"seed": seed, "k": k, "method": method, "optimal": opt,
                     "length": length, "found_route": length is not None,
                     "ratio": (length / opt) if length is not None else None,
                     "is_optimal": length == opt, **extra})

    _, l = exact(dock, debris)
    row("exact", l)
    _, l = greedy(dock, debris)
    row("greedy", l)
    r = random_sampling(dock, debris, shots, seed)
    row("random_sampling", r["best_length"], valid_fraction=r["valid_fraction"])
    for reps in reps_list:
        r = solve_qaoa(dock, debris, reps=reps, shots=shots, seed=seed)
        row(f"qaoa_p{reps}", r["best_length"],
            valid_fraction=r["valid_fraction"], optimal_mass=r["optimal_mass"],
            top_is_valid=r["top_is_valid"], seconds=r["seconds"], evals=int(r["evals"]))
    return rows
