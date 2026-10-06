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
