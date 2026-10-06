"""Fixed-start TSP as a QUBO, plus QAOA solve and decoding.

Variable x[i][t] = 1 means "debris spot i is visited at step t".
The dock is the fixed start and end, so it needs no variables: K spots and
K steps give K*K binary variables (16 qubits for K=4).
"""
import numpy as np

from lake import manhattan


def var(i, t, k):
    return i * k + t


def default_penalty(dock, debris):
    # Why this value: breaking a constraint should never pay off, but a huge
    # weight flattens the distance term and makes QAOA's job harder. I scanned
    # weights 1..16 with a brute-force check over all 2^16 bitstrings on 15
    # seeds (K=4): 1 and 2 gave no optimal routes, 4 worked on 6/15, and 6 or
    # more worked on 15/15. Starting point is 2x the longest leg, which is
    # safely above that threshold; may be lowered after testing with QAOA.
    pts = [dock] + list(debris)
    longest = max(manhattan(a, b) for a in pts for b in pts)
    return 2.0 * longest


def build_qubo(dock, debris, penalty=None):
    """Return (Q, const). Energy of bit vector x is x @ Q @ x + const, Q upper triangular."""
    k = len(debris)
    A = default_penalty(dock, debris) if penalty is None else penalty
    n = k * k
    Q = np.zeros((n, n))
    const = 0.0

    def add(a, b, w):
        # Binary variables: x*x = x, so a diagonal term is just linear.
        a, b = min(a, b), max(a, b)
        Q[a, b] += w

    # Distance terms: dock -> first spot, consecutive spots, last spot -> dock.
    for i in range(k):
        add(var(i, 0, k), var(i, 0, k), manhattan(dock, debris[i]))
        add(var(i, k - 1, k), var(i, k - 1, k), manhattan(debris[i], dock))
    for t in range(k - 1):
        for i in range(k):
            for j in range(k):
                if i != j:
                    add(var(i, t, k), var(j, t + 1, k), manhattan(debris[i], debris[j]))

    # Constraint penalties A * (sum of group - 1)^2, expanded for binary x:
    # -sum x + 2 * sum over pairs x_a x_b + 1.
    groups = [[var(i, t, k) for t in range(k)] for i in range(k)]  # spot i once
    groups += [[var(i, t, k) for i in range(k)] for t in range(k)]  # step t holds one spot
    for g in groups:
        const += A
        for a in g:
            add(a, a, -A)
        for x in range(len(g)):
            for y in range(x + 1, len(g)):
                add(g[x], g[y], 2 * A)
    return Q, const


def energy(bits, Q, const):
    x = np.asarray(bits, dtype=float)
    return float(x @ Q @ x + const)


def decode(bits, k):
    """Bit vector -> visiting order, or None if it is not a valid route."""
    m = np.asarray(bits, dtype=int).reshape(k, k)  # m[i][t]
    if not (np.all(m.sum(axis=0) == 1) and np.all(m.sum(axis=1) == 1)):
        return None
    return [int(np.argmax(m[:, t])) for t in range(k)]


def all_energies(Q, const):
    """Energy of every bitstring, indexed by the integer whose bit v is variable v."""
    n = Q.shape[0]
    idx = np.arange(2 ** n)
    X = ((idx[:, None] >> np.arange(n)) & 1).astype(float)
    return np.einsum("ab,bc,ac->a", X, Q, X) + const


# ---------------------------------------------------------------- QAOA part
import time

from qiskit.quantum_info import SparsePauliOp


def qubo_to_ising(Q, const):
    """Substitute x = (1 - Z)/2 so the QUBO energy becomes a sum of Pauli-Z terms.

    Qubit v is variable v (Qiskit's little-endian order), the same convention
    all_energies() uses, so bitstring integers line up between the two.
    """
    n = Q.shape[0]
    terms = {}  # tuple of qubit indices -> coefficient

    def add(qubits, w):
        terms[qubits] = terms.get(qubits, 0.0) + w

    offset = const
    for a in range(n):
        for b in range(a, n):
            w = Q[a, b]
            if w == 0:
                continue
            if a == b:  # w * (1 - Za)/2
                offset += w / 2
                add((a,), -w / 2)
            else:  # w * (1 - Za)(1 - Zb)/4
                offset += w / 4
                add((a,), -w / 4)
                add((b,), -w / 4)
                add((a, b), w / 4)
    paulis = []
    for qs, w in terms.items():
        label = ["I"] * n
        for q in qs:
            label[n - 1 - q] = "Z"  # rightmost character is qubit 0
        paulis.append(("".join(label), w))
    paulis.append(("I" * n, offset))
    return SparsePauliOp.from_list(paulis).simplify()


def solve_qaoa(dock, debris, reps=1, penalty=None, shots=4096, maxiter=100, seed=0):
    """Run QAOA on the simulator and return the metrics from PRD section 4.3.1."""
    from qiskit_aer.primitives import SamplerV2
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from lake import route_length
    from classical import exact

    k = len(debris)
    Q, const = build_qubo(dock, debris, penalty)
    op = qubo_to_ising(Q, const)

    # Aer cannot run the high-level QAOA block directly, so decompose it into
    # basic gates with a preset pass manager before sampling.
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    pm = generate_preset_pass_manager(optimization_level=1, backend=AerSimulator())
    sampler = SamplerV2(default_shots=shots, seed=seed)
    qaoa = QAOA(sampler, COBYLA(maxiter=maxiter), reps=reps,
                initial_point=np.full(2 * reps, 0.1), transpiler=pm)
    t0 = time.time()
    res = qaoa.compute_minimum_eigenvalue(op)
    elapsed = time.time() - t0

    # eigenstate maps bitstring -> probability. The leftmost character is the
    # highest qubit, so variable v is the character at position n-1-v.
    _, opt_len = exact(dock, debris)
    n = k * k
    valid_mass, opt_mass, best = 0.0, 0.0, None
    top_bits = max(res.eigenstate, key=res.eigenstate.get)
    top_order = decode([int(top_bits[n - 1 - v]) for v in range(n)], k)
    for bits, p in res.eigenstate.items():
        order = decode([int(bits[n - 1 - v]) for v in range(n)], k)
        if order is None:
            continue
        length = route_length(dock, debris, order)
        valid_mass += p
        if length == opt_len:
            opt_mass += p
        if best is None or length < best[1]:
            best = (order, length)
    return {
        "best_order": best[0] if best else None,
        "best_length": best[1] if best else None,
        "optimal_length": opt_len,
        "top_is_valid": top_order is not None,
        "valid_fraction": valid_mass,
        "optimal_mass": opt_mass,
        "seconds": elapsed,
        "evals": res.cost_function_evals,
        "reps": reps,
    }
