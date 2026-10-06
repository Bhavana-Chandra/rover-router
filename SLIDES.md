# Slide outline (organisers' Canva template, make a copy first)

Template: https://canva.link/b51hvxu95kmz95f

Numbers are from `results/summary.txt` (20 random lakes per size) and the demo seed 16.

## 1. Title

- Quantum debris-sweep planner for a water-cleaning rover
- Q-Hack India 2026, Round 1, track: Quantum AI & Software
- Team: [FILL: names, college]
- Simulation only. Builds on our earlier Water_Rover project.

## 2. Problem

- Our Water_Rover collects floating debris, but a person steers it by hand.
- With several debris spots, the visiting order decides distance and battery use.
- Shortest route through all spots is the travelling salesman problem (NP-hard).
- Question: on a tiny simulated lake, can QAOA find good routes, and how does it
  compare with simple classical planners?

## 3. Why quantum

- QAOA is a quantum optimisation algorithm that researchers are testing on routing problems.
- Whether it helps on small, noisy-free simulated cases is an open question we can test ourselves.
- So this is a test, not a claim: we build it, run it, and report what happens.

## 4. Approach

- 5x5 lake grid, one dock, 4 debris spots, Manhattan distance.
- Route as a QUBO: variable x[i][t] = spot i visited at step t. 16 variables, 16 qubits.
- Penalties force each spot once and each step one spot. We scanned the penalty weight on 15 lakes: weights of 6 or more always gave the optimal route as the QUBO's best answer, 1 to 4 did not.
- QAOA (depth 1 and 2, COBYLA) on the Aer simulator.
- Compared with greedy nearest-neighbour, exact brute force, and a random-sampling control.

## 5. Results (20 random lakes, 4 spots)

| Method | Mean length / optimal | Found the optimum | Found a valid route |
|---|---|---|---|
| Exact | 1.00 | 100% | 100% |
| Greedy | 1.03 | 80% | 100% |
| Random sampling | 1.17 | 25% | 65% |
| QAOA p=1 | 1.13 | 45% | 75% |
| QAOA p=2 | 1.12 | 60% | 95% |

- Figure: `results/benchmark.png` and `results/route_comparison.png`.
- With 3 spots, random sampling already finds the optimum every time, so that size says little about QAOA.

## 6. Limitations

- Simulator only. No real quantum hardware. No noise model.
- Tiny grid, 3 to 4 spots. Only a small share of sampled bitstrings are valid routes (about 0.3% at 4 spots).
- Greedy beat QAOA. We make no claim of speedup or advantage.

## 7. Next steps

- Run on real IBM hardware through Qiskit.
- Study how noise changes the valid-route rate.
- Add currents, obstacles and battery limits.
- Send planned waypoints to the real rover.
