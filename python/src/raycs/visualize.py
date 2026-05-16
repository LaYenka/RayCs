"""
Matplotlib visualization helpers for RCS results.

All functions accept either an RCSResult object or a tuple of
(theta_deg, phi_deg, rcs_db) arrays.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def _unwrap_result(result):
    """Convert various input formats to (theta, phi, rcs) arrays."""
    if hasattr(result, "theta_deg"):
        return result.theta_deg, result.phi_deg, result.rcs_total_db
    if isinstance(result, tuple) and len(result) == 3:
        return result
    try:
        return result["theta_deg"], result["phi_deg"], result["rcs_total_db"]
    except (TypeError, KeyError):
        pass
    raise TypeError("Expected RCSResult, tuple (theta, phi, rcs), or numpy structured array")


def _add_incident_arrow(ax, kind="2d", rcs_range=None):
    """Add incident wave direction arrow to plot."""
    import matplotlib.patches as mpatches

    if kind == "polar":
        if rcs_range is not None:
            r_max = rcs_range[1]
        else:
            r_max = ax.get_rmax()
        ax.annotate("", xy=(0, r_max * 0.9), xytext=(0, r_max * 1.15),
                    arrowprops=dict(arrowstyle="->", color="red", lw=2))
        ax.text(0, r_max * 1.25, "Incident (+Z)", ha="center", fontsize=10, color="red")
    elif kind == "3d":
        ax.quiver(0, 0, 2, 0, 0, -1.5, color="red",
                  arrow_length_ratio=0.3, linewidth=3)
        ax.text(0, 0, 2.3, "+Z (Incident)", fontsize=12, color="red", ha="center")
    elif kind == "2d":
        if rcs_range is not None:
            y_mid = (rcs_range[0] + rcs_range[1]) / 2
            ax.annotate("", xy=(5, y_mid), xytext=(0, y_mid - 10),
                        arrowprops=dict(arrowstyle="->", color="red", lw=2))
            ax.text(2, y_mid - 15, "Incident\nWave (+Z)", ha="center", fontsize=10, color="red")


def plot_2d(result, phi_cut=0, ax=None, show_incident=True, title="", label=None):
    """2D RCS cut at constant phi.

    Args:
        result: RCSResult or (theta, phi, rcs) tuple.
        phi_cut: Phi angle for the cut in degrees (default 0).
        ax: Matplotlib axis (optional).
        show_incident: Show incident wave arrow (default True).
        title: Plot title.
        label: Legend label.

    Returns:
        Matplotlib figure.
    """
    theta, phi, rcs = _unwrap_result(result)
    mask = np.abs(phi - phi_cut) < 1.0
    if not np.any(mask):
        mask = np.abs(phi - phi_cut) < 10.0
    valid = mask & (rcs > -300)

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    ax.plot(theta[valid], rcs[valid], "b-", linewidth=2, label=label or "RCS")

    if show_incident and np.any(valid):
        _add_incident_arrow(ax, "2d",
                            (np.min(rcs[valid]), np.max(rcs[valid])))

    ax.set_xlabel("Theta (degrees)")
    ax.set_ylabel("RCS (dBsm)")
    ax.set_title(title or f"RCS 2D Cut (phi={phi_cut}°)")
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 180])

    return fig


def plot_3d(result, ax=None, show_incident=False, title="", cmap="viridis"):
    """3D radiation pattern.

    Args:
        result: RCSResult or (theta, phi, rcs) tuple.
        ax: Matplotlib 3D axis (optional).
        show_incident: Show incident wave arrow (default False).
        title: Plot title.
        cmap: Colormap name.

    Returns:
        Matplotlib 3D axis.
    """
    theta, phi, rcs = _unwrap_result(result)
    theta_rad = np.radians(theta)
    phi_rad = np.radians(phi)
    valid = rcs > -300
    if not np.any(valid):
        print("  Warning: No valid RCS data for 3D plot")
        return ax

    r = np.maximum(rcs + 100, 0) / 30
    x = r * np.sin(theta_rad) * np.cos(phi_rad)
    y = r * np.sin(theta_rad) * np.sin(phi_rad)
    z = r * np.cos(theta_rad)

    if ax is None:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection="3d")
    else:
        fig = ax.figure

    scatter = ax.scatter(x[valid], y[valid], z[valid],
                         c=rcs[valid], cmap=cmap, s=15, alpha=0.8)

    if show_incident:
        _add_incident_arrow(ax, "3d")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(title or "3D Radiation Pattern")

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.5)
    cbar.set_label("RCS (dBsm)")

    return fig


def plot_polar(result, ax=None, show_incident=True, title="", label=None):
    """Polar radiation pattern.

    Args:
        result: RCSResult or (theta, phi, rcs) tuple.
        ax: Matplotlib polar axis (optional).
        show_incident: Show incident wave arrow (default True).
        title: Plot title.
        label: Legend label.

    Returns:
        Matplotlib polar axis.
    """
    theta, phi, rcs = _unwrap_result(result)
    theta_rad = np.radians(theta)
    valid = rcs > -300

    if ax is None:
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(10, 8))
    else:
        fig = ax.figure

    ax.plot(theta_rad[valid], rcs[valid], "b-", linewidth=2, label=label or "RCS")

    if show_incident:
        _add_incident_arrow(ax, "polar")

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(title or "Polar Pattern", pad=20)
    ax.grid(True)

    return fig


def plot_radiation_pattern(result, title=""):
    """Combined 2x2 figure: 2D cut, polar, 3D, info panel.

    Args:
        result: RCSResult or (theta, phi, rcs) tuple.
        title: Additional title info.

    Returns:
        Matplotlib figure.
    """
    theta, phi, rcs = _unwrap_result(result)

    fig = plt.figure(figsize=(16, 12))

    # 2D cut (phi=0)
    ax1 = fig.add_subplot(2, 2, 1)
    mask = np.abs(phi) < 1
    valid = mask & (rcs > -300)
    if np.any(valid):
        ax1.plot(theta[valid], rcs[valid], "b-", linewidth=2)
        _add_incident_arrow(ax1, "2d", (np.min(rcs[valid]), np.max(rcs[valid])))
    ax1.set_xlabel("Theta (degrees)")
    ax1.set_ylabel("RCS (dBsm)")
    ax1.set_title("2D Cut (phi=0°)")
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 180])

    # Polar
    ax2 = fig.add_subplot(2, 2, 2, projection="polar")
    theta_rad = np.radians(theta)
    valid = rcs > -300
    ax2.plot(theta_rad[valid], rcs[valid], "b-", linewidth=2)
    _add_incident_arrow(ax2, "polar")
    ax2.set_title("Polar Pattern")
    ax2.grid(True)

    # 3D
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    valid_3d = rcs > -300
    if np.any(valid_3d):
        theta_3d = np.radians(theta[valid_3d])
        phi_3d = np.radians(phi[valid_3d])
        r_3d = np.maximum(rcs[valid_3d] + 100, 0) / 30
        x = r_3d * np.sin(theta_3d) * np.cos(phi_3d)
        y = r_3d * np.sin(theta_3d) * np.sin(phi_3d)
        z = r_3d * np.cos(theta_3d)
        scatter = ax3.scatter(x, y, z, c=rcs[valid_3d], cmap="viridis", s=10, alpha=0.8)
        ax3.set_xlabel("X")
        ax3.set_ylabel("Y")
        ax3.set_zlabel("Z")
        ax3.set_title("3D Pattern")

    # Info
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis("off")
    info = f"RCS Simulation\n{'='*25}\n\n"
    info += f"Valid points: {np.sum(rcs > -300)}/{len(rcs)}\n"
    info += f"Theta range: [{theta.min():.0f}, {theta.max():.0f}]°\n"
    info += f"Phi range: [{phi.min():.0f}, {phi.max():.0f}]°\n\n"
    if len(rcs) > 0 and np.any(rcs > -300):
        valid_data = rcs[rcs > -300]
        info += f"RCS: {valid_data.min():.1f} to {valid_data.max():.1f} dBsm\n"
    ax4.text(0.1, 0.9, info, transform=ax4.transAxes, fontsize=11,
             verticalalignment="top", fontfamily="monospace")

    fig.suptitle(title or "Radiation Pattern", fontsize=14, fontweight="bold")
    plt.tight_layout()

    return fig


def plot_rotation_comparison(results, labels=None, title="", theta_cut=False):
    """Compare RCS from multiple configurations (e.g., different rotations).

    Args:
        results: Dict of {label: RCSResult} or list of RCSResult.
        labels: List of labels (optional if results is a dict).
        title: Plot title.
        theta_cut: If True, show 2D cut. Default shows polar comparison.

    Returns:
        Matplotlib figure.
    """
    if isinstance(results, dict):
        items = list(results.items())
    else:
        if labels is None:
            labels = [f"Run {i}" for i in range(len(results))]
        items = list(zip(labels, results))

    colors = ["b", "r", "g", "orange", "purple", "brown", "pink", "gray", "olive", "cyan"]

    if theta_cut:
        fig, ax = plt.subplots(figsize=(12, 6))
        for i, (label, result) in enumerate(items):
            theta, phi, rcs = _unwrap_result(result)
            mask = np.abs(phi) < 1
            valid = mask & (rcs > -300)
            if np.any(valid):
                ax.plot(theta[valid], rcs[valid], "-", linewidth=2,
                        color=colors[i % len(colors)], label=str(label))
        ax.set_xlabel("Theta (degrees)")
        ax.set_ylabel("RCS (dBsm)")
        ax.set_title(title or "Rotation Comparison (phi=0°)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 180])
    else:
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(10, 8))
        for i, (label, result) in enumerate(items):
            theta, phi, rcs = _unwrap_result(result)
            theta_rad = np.radians(theta)
            valid = rcs > -300
            if np.any(valid):
                ax.plot(theta_rad[valid], rcs[valid], "-", linewidth=2,
                        color=colors[i % len(colors)], label=str(label))
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title(title or "Rotation Comparison", pad=20)
        ax.legend(loc="upper right")
        ax.grid(True)

    return fig
