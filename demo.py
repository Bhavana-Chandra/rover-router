"""One-command demo on a single fixed seed.

python demo.py            run everything live
python demo.py --cached   reuse the QAOA result saved by the last live run
python demo.py --k 3      smaller problem (9 qubits)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lake import make_lake, route_length
from classical import greedy, exact
from qaoa_tsp import build_qubo, solve_qaoa
from plotting import plot_routes

# Hand-picked for a readable picture: the exact route is shorter than greedy and QAOA. QAOA p=1
# finds no valid route on 5 of 20 K=4 seeds, so this is not typical. See results/benchmark.csv.
DEMO_SEED = 16
CACHE = "results/demo_cached.json"


def heading(text):
    print(f"\n=== {text} ===")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=DEMO_SEED)
    ap.add_argument("--cached", action="store_true")
    ap.add_argument("--no-show", action="store_true")
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)

    heading("Lake")
    dock, debris = make_lake(args.seed, k=args.k)
    print(f"Seed {args.seed}. Dock at {dock}. Debris at {debris}.")

    heading("Building QUBO")
    Q, _ = build_qubo(dock, debris)
    print(f"{args.k} spots x {args.k} steps = {Q.shape[0]} binary variables = {Q.shape[0]} qubits")

    heading("Classical baselines")
    e_order, e_len = exact(dock, debris)
    g_order, g_len = greedy(dock, debris)
    print(f"Exact (brute force): {e_order}, length {e_len}")
    print(f"Greedy:              {g_order}, length {g_len}")

    heading("Running QAOA, p=1")
    cache_key = f"k{args.k}_seed{args.seed}"
    r = None
    if args.cached and os.path.exists(CACHE):
        saved = json.load(open(CACHE))
        r = saved.get(cache_key)
        if r:
            print("CACHED result from an earlier live run (not recomputed).")
    if r is None:
        r = solve_qaoa(dock, debris, reps=1, seed=args.seed)
        r["evals"] = int(r["evals"])
        saved = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
        saved[cache_key] = r
        json.dump(saved, open(CACHE, "w"), indent=2)
    print(f"Best valid route:        {r['best_order']}, length {r['best_length']}")
    print(f"Top sampled bitstring valid: {r['top_is_valid']}")
    print(f"Valid shots:             {r['valid_fraction']:.2%}")
    print(f"Probability on optimum:  {r['optimal_mass']:.2%}")
    print(f"Time {r['seconds']:.1f}s, optimiser evaluations {r['evals']}")

    heading("Comparing with classical")
    q_len = r["best_length"]
    print(f"{'Method':8s} {'Length':>6s} {'Ratio':>6s}")
    for name, length in (("Exact", e_len), ("Greedy", g_len), ("QAOA", q_len)):
        shown = "none" if length is None else f"{length:6d}"
        ratio = "-" if length is None else f"{length / e_len:6.2f}"
        print(f"{name:8s} {shown:>6s} {ratio:>6s}")

    plot_routes(dock, debris,
                {"exact": (e_order, e_len), "greedy": (g_order, g_len),
                 "qaoa": (r["best_order"], q_len)},
                path="results/route_comparison.png", show=not args.no_show)
    heading("Summary")
    print(f"Simulated lake, {args.k} debris spots, QAOA on a simulator. Exact {e_len}, "
          f"greedy {g_len}, QAOA {q_len}. No hardware, no speedup claimed.")


if __name__ == "__main__":
    main()
