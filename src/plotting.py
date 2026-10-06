"""Matplotlib figures. Big fonts and strong contrast so they read on a phone."""
import matplotlib.pyplot as plt

# method -> (colour, linestyle, small offset on the grid so overlapping routes stay visible)
STYLES = {
    "exact": ("#1b7837", "-", -0.12),
    "greedy": ("#d95f02", "--", 0.0),
    "qaoa": ("#7570b3", ":", 0.12),
}
LABELS = {"exact": "Exact (optimal)", "greedy": "Greedy", "qaoa": "QAOA"}


def plot_routes(dock, debris, routes, size=5, path="results/route_comparison.png", show=False):
    """routes: {'exact': (order, length), 'greedy': ..., 'qaoa': ...}; order may be None."""
    fig, ax = plt.subplots(figsize=(9, 9))
    for m, (order, length) in routes.items():
        colour, ls, off = STYLES[m]
        if order is None:
            ax.plot([], [], color=colour, ls=ls, lw=4, label=f"{LABELS[m]}: no valid route")
            continue
        pts = [dock] + [debris[i] for i in order] + [dock]
        # The rover moves along grid lines, so draw each leg as an L (x first, then y).
        xs, ys = [pts[0][0] + off], [pts[0][1] + off]
        for (_, y0), (x1, y1) in zip(pts, pts[1:]):
            xs += [x1 + off, x1 + off]
            ys += [y0 + off, y1 + off]
        ax.plot(xs, ys, color=colour, ls=ls, lw=4, label=f"{LABELS[m]}: length {length}")
    ax.scatter(*zip(*debris), s=500, c="#e7298a", edgecolor="black", zorder=5, label="Debris")
    for i, (x, y) in enumerate(debris):
        ax.text(x, y, str(i), ha="center", va="center", color="white", fontsize=16,
                fontweight="bold", zorder=6)
    ax.scatter([dock[0]], [dock[1]], s=700, marker="s", c="black", zorder=5, label="Dock")
    ax.set_xticks(range(size))
    ax.set_yticks(range(size))
    ax.set_xlim(-0.6, size - 0.4)
    ax.set_ylim(-0.6, size - 0.4)
    ax.grid(True, color="#bbbbbb")
    ax.tick_params(labelsize=16)
    ax.set_title("Debris sweep routes on the simulated lake", fontsize=20)
    ax.legend(fontsize=15, loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_benchmark(summary, path="results/benchmark.png"):
    """summary: {k: {method: {'mean_ratio', 'optimal_rate', 'route_found_rate'}}}."""
    methods = ["exact", "greedy", "random_sampling", "qaoa_p1", "qaoa_p2"]
    colours = ["#1b7837", "#d95f02", "#999999", "#7570b3", "#c2a5cf"]
    ks = sorted(summary)
    width = 0.8 / len(methods)
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    panels = [("mean_ratio", "Mean length / optimal (1.00 = optimal)", 1.0),
              ("optimal_rate", "Fraction of seeds where optimum was found", 0.0)]
    for ax, (key, ylabel, base) in zip(axes, panels):
        for j, m in enumerate(methods):
            vals = [summary[k][m][key] or 0 for k in ks]
            xs = [i + j * width for i in range(len(ks))]
            bars = ax.bar(xs, [v - base if base else v for v in vals], width, bottom=base,
                          label=m, color=colours[j], edgecolor="black")
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, max(v, base) + 0.01, f"{v:.2f}",
                        ha="center", fontsize=11)
        ax.set_xticks([i + 0.4 - width / 2 for i in range(len(ks))])
        ax.set_xticklabels([f"K = {k}" for k in ks], fontsize=16)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.tick_params(axis="y", labelsize=13)
    axes[0].set_ylim(0.95, 1.22)
    axes[1].set_ylim(0, 1.12)
    axes[0].legend(fontsize=12, loc="upper left")
    found = "; ".join(f"{m} {summary[max(ks)][m]['route_found_rate']:.0%}" for m in methods[2:])
    fig.suptitle("Route quality by method", fontsize=20)
    fig.text(0.5, 0.01, f"Ratio is averaged over seeds where a valid route was found. "
             f"Seeds with a route at K={max(ks)}: {found}.", ha="center", fontsize=12)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(path, dpi=150)
    plt.close(fig)
