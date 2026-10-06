# Quantum debris-sweep planner for Water Rover

This is a small simulation where a quantum algorithm (QAOA, run on a simulator) plans the order in which a rover visits floating debris on a lake. I compare it with two simple classical planners and report what happened, including where it did badly.

## Where it came from

This grows out of our first hackathon project, [Water_Rover](https://github.com/Bhavana-Chandra/Water_Rover). It is a rover built around a NodeMCU and a motor controller, driven from the Blynk IoT app. It collects floating debris with an escalator mechanism and a net, and a Raspberry Pi Zero 2W streams live video from it. I set up the Raspberry Pi and the live stream on that project.

The weak point of that rover was that a person steers it by hand. The rover collects debris fine, but where it goes and in what order is the operator's guess. If debris is scattered over a lake, a bad order wastes battery and time. So I asked whether the "where next" decision could be computed instead of guessed, and since this hackathon is about quantum software, whether a quantum optimisation algorithm could do it.

**The rover is not part of this prototype.** I do not have it with me for this hackathon. Everything here is a simulation on a laptop: no hardware, no Blynk, no Pi, no camera.

[FILL: one or two sentences in my own words about why I care about water pollution or why I picked this.]

## The problem and the question

Given a dock and several debris spots, find the shortest route that visits every spot and returns to the dock. That is the Travelling Salesman Problem (TSP). It is NP-hard, so the work grows quickly as spots are added. QAOA is one of the quantum algorithms researchers are testing on problems of this shape.

The question I tried to answer: on a tiny simulated lake, can a QAOA planner find good sweep routes, and how does it compare with simple classical planners? I am not claiming a speedup.

## What I built

- **The lake** (`src/lake.py`): a 5x5 grid, the dock at a corner, and K randomly placed debris spots. A seed makes every run reproducible. Distance is Manhattan distance, because the rover moves along grid lines.
- **Classical baselines** (`src/classical.py`): greedy nearest-neighbour, and brute force over every ordering. Brute force is the true optimum at this size and is what everything else is measured against.
- **The quantum version** (`src/qaoa_tsp.py`): described below.
- **Benchmark** (`src/benchmark.py`, `run_benchmark.py`): all methods on 20 random lakes at K=3 and K=4.
- **Demo** (`demo.py`): one command, one fixed lake, readable output and a route figure.

## How the quantum part works

**1. Turn the route into bits.** For K spots I use K x K binary variables, `x[i][t] = 1` meaning "spot i is visited at step t". The dock is always the start and end, so it needs no variables. K=4 gives 16 variables, which is 16 qubits.

**2. Write the cost as a QUBO.** The cost of a route is the sum of the distances between consecutive stops, including dock to first spot and last spot back to dock. Each such leg becomes a term that is only "on" when the two spots are at consecutive steps. This is built directly as a matrix in `build_qubo`, so I control every term.

**3. Add penalties for invalid routes.** A random bitstring is almost never a real route. Two penalty groups push the cost up when a spot is visited zero or two times, or when a step holds zero or two spots. The weight matters:

- Too small, and the lowest-energy bitstring is an invalid route that "cheats".
- Too large, and the distance term is drowned out.

I checked this by brute force: I computed the energy of all 2^16 bitstrings on 15 lakes and looked at whether the lowest one was the optimal route. Weights of 1 and 2 never gave the optimal route, 4 gave it on 6 of 15 lakes, and 6 or more gave it on all 15. I use 2x the longest distance between any two points, which is above that threshold. A test (`tests/test_qubo.py`) checks the QUBO's lowest bitstring against the brute-force route.

**4. Convert to a quantum problem and run QAOA.** The QUBO is converted to an Ising operator (substituting x = (1 - Z)/2), and I added a test that its diagonal matches the QUBO energies, to catch bit-order mistakes. QAOA runs with `qiskit-algorithms` on the Aer simulator, with COBYLA as the classical optimiser, at depth p=1 and p=2. A single K=4 solve takes roughly 3 to 8 seconds on my laptop.

**5. Read the answer.** QAOA does not return one answer. It returns a distribution over bitstrings. I decode every sampled bitstring, throw away the invalid ones, and keep the shortest valid route. I also record the share of shots that were valid routes and the probability on the optimal route.

**A control I added.** With 4096 samples, even random guessing can stumble on a good route when the problem is tiny. So the benchmark includes "random sampling": the same number of uniformly random bitstrings, decoded the same way. QAOA has to beat that to mean anything.

## Results

20 random lakes per size, from `results/benchmark.csv` and `results/summary.txt`. Ratio is route length divided by the optimal length (1.00 = optimal), averaged over lakes where the method found a valid route.

**K=4 (16 qubits)**

| Method | Mean ratio | Found the optimum | Found any valid route |
|---|---|---|---|
| Exact (brute force) | 1.00 | 100% | 100% |
| Greedy | 1.03 | 80% | 100% |
| Random sampling | 1.17 | 25% | 65% |
| QAOA p=1 | 1.13 | 45% | 75% |
| QAOA p=2 | 1.12 | 60% | 95% |

**K=3 (9 qubits)**: greedy 1.01 (optimal on 90%). Exact, random sampling, QAOA p=1 and QAOA p=2 all reached 1.00 on every lake.

![Route comparison on the demo lake](results/route_comparison.png)
![Benchmark](results/benchmark.png)

**Did we achieve it?** Partly.

- It works end to end: the QUBO is correct (checked against brute force), QAOA runs on the simulator and produces valid routes, and the whole pipeline is reproducible from one command.
- At K=4, QAOA does better than the random-sampling control, and p=2 does better than p=1. So the circuit is doing something.
- But greedy was better than QAOA on every measure, and costs almost nothing to run. That is a normal outcome at this size, and I am reporting it as it is.
- Only about 0.3% of QAOA's shots at K=4 were valid routes. At p=1 it produced no valid route at all on 5 of 20 lakes.
- The K=3 results say very little. Random sampling already finds the optimum every time, so K=3 cannot tell QAOA apart from luck.
- The demo lake (seed 16) was picked because the exact route is visibly shorter than the others. It is not a typical lake. On it, QAOA found the same route as greedy (length 16, optimal is 14), and its most probable bitstring was not a valid route.

## What went wrong and what I learned

- **A weak penalty gives invalid routes.** The brute-force scan showed it plainly: with a small weight, the lowest-energy bitstring was often not a route at all, so a perfect QAOA would still have returned an invalid answer.
- **The environment fought back.** On Python 3.14, Windows Application Control blocked a DLL inside scipy, which `qiskit-algorithms` needs. I switched to a Python 3.11 virtualenv instead of working around the policy.
- **Aer could not run QAOA directly.** The first QAOA call failed with "unknown instruction: QAOA". The circuit has to be transpiled into basic gates first.
- **Most shots are not routes.** I hoped QAOA would concentrate probability on valid routes. It only does so slightly. Random bitstrings are valid routes about 1.2% of the time at K=3 and 0.04% at K=4, so with 4096 shots a tiny problem can look solved by luck. That is why I added the random-sampling control, and why I treat K=3 as uninformative.
- **My first charts were misleading.** The route figure drew diagonal lines though the rover moves on grid lines, and the benchmark bars started at zero and hid the differences. I redrew both.
- **Penalty weight did not clearly help QAOA.** I tried weights 6, 8 and the default on a few lakes. The results were too noisy to pick a winner, so I kept the default and did not tune further.

## Limitations

- Simulator only. No real quantum hardware and no noise model.
- A tiny 5x5 grid and 3 to 4 debris spots.
- A single QAOA run per lake and a limited number of optimiser steps, so QAOA's numbers could probably improve with more tuning.
- No quantum speedup or advantage is claimed, and none was found.

## Next steps

- Run the same circuits on real IBM hardware through Qiskit.
- Add an Aer noise model to see how noise changes the valid-route rate.
- Add currents, obstacles and battery limits to the lake.
- Send the planned waypoints to the real rover.

## Run it

Tested with Python 3.11.

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   or   source .venv/bin/activate
pip install -r requirements.txt
python demo.py                   (live, about 10 seconds)
python demo.py --cached          (reuses the saved QAOA result, labelled as cached)
python run_benchmark.py          (20 lakes at K=3 and K=4, a few minutes)
python run_benchmark.py --replot (redraw the chart from the saved CSV)
python -m pytest                 (tests)
```

## How this was built

I used Claude Code for coding assistance while building this. [FILL: anything the hackathon's AI-tools policy requires. I will check the Devfolio page.]

## References

- Qiskit Optimization: https://qiskit-community.github.io/qiskit-optimization/
- Qiskit Algorithms: https://qiskit-community.github.io/qiskit-algorithms/
- Qiskit documentation: https://docs.quantum.ibm.com/
- Related reading I have not reproduced or extended:
  - https://arxiv.org/abs/2407.08767 (multi-robot coverage path planning with quantum computing)
  - https://arxiv.org/abs/2510.07413 (grid path planning with parallel QAOA circuits)
  - https://arxiv.org/abs/2304.09629 (quantum-assisted solution paths for the capacitated vehicle routing problem)

## Team

[FILL: team members, college, roles]
