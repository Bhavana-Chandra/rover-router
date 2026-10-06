"""Many seeds, all methods. Writes results/benchmark.csv, benchmark.png, summary.txt."""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np

from benchmark import run_seed
from plotting import plot_benchmark


def summarise(rows):
    """Per method: mean ratio over seeds that gave a route, optimum rate, route-found rate."""
    out = {}
    for m in dict.fromkeys(r["method"] for r in rows):
        mine = [r for r in rows if r["method"] == m]
        found = [r for r in mine if r["found_route"]]
        has_vf = "valid_fraction" in mine[0]
        out[m] = {
            "mean_ratio": float(np.mean([r["ratio"] for r in found])) if found else None,
            "optimal_rate": sum(r["is_optimal"] for r in mine) / len(mine),
            "route_found_rate": len(found) / len(mine),
            "mean_valid_fraction": float(np.mean([r["valid_fraction"] for r in mine])) if has_vf else None,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ks", type=int, nargs="+", default=[3, 4])
    ap.add_argument("--seeds", type=int, default=20)
    args = ap.parse_args()

    os.makedirs("results", exist_ok=True)
    rows, summary, lines = [], {}, []
    for k in args.ks:
        print(f"K={k}: running {args.seeds} seeds ...", flush=True)
        krows = []
        for seed in range(args.seeds):
            krows += run_seed(seed, k=k)
            print(f"  seed {seed} done", flush=True)
        rows += krows
        s = summarise(krows)
        summary[k] = {m: v["mean_ratio"] for m, v in s.items()}
        lines.append(f"K={k}, {args.seeds} seeds")
        for m, v in s.items():
            mr = "n/a" if v["mean_ratio"] is None else f"{v['mean_ratio']:.3f}"
            vf = "" if v["mean_valid_fraction"] is None else f", mean valid shot fraction {v['mean_valid_fraction']:.4f}"
            lines.append(f"  {m:16s} mean ratio {mr}, optimal on {v['optimal_rate']:.0%}, "
                         f"route found on {v['route_found_rate']:.0%}{vf}")

    cols = ["seed", "k", "method", "optimal", "length", "found_route", "ratio", "is_optimal",
            "valid_fraction", "optimal_mass", "top_is_valid", "seconds", "evals"]
    with open("results/benchmark.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    plot_benchmark(summary)
    with open("results/summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
