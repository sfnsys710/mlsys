"""Visualization utilities for consistent plotting style."""

import matplotlib.pyplot as plt


def setup_plot_style() -> None:
    """
    Configure matplotlib plotting style for consistent, publication-quality visualizations.

    Sets:
    - Figure style: seaborn-v0_8-darkgrid or default if not available
    - Figure size: 10x6 inches
    - Font size: 12pt
    - DPI: 100
    """
    try:
        plt.style.use("seaborn-v0_8-darkgrid")
    except OSError:
        # Fallback if seaborn style not available
        plt.style.use("default")

    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "font.size": 12,
            "figure.dpi": 100,
            "axes.labelsize": 12,
            "axes.titlesize": 14,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
        }
    )
