"""High-DPI chart factory (matplotlib, headless Agg backend).

Each function returns PNG bytes at 200 DPI in the corporate theme. The stage
chart dispatcher degrades gracefully: when the stage_result lacks expected
fields, a themed placeholder chart is produced instead of failing — a missing
chart must never block a deliverable.
"""

from __future__ import annotations

import io
import math

import matplotlib

matplotlib.use("Agg")  # headless — must precede pyplot import

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from app.doc_factory import theme  # noqa: E402


def _fig(width: float = 8.0, height: float = 4.5) -> tuple:
    fig, ax = plt.subplots(figsize=(width, height), facecolor=theme.CHART_FACE)
    ax.set_facecolor(theme.CHART_FACE)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(theme.SLATE)
    ax.tick_params(colors=theme.SLATE)
    ax.grid(True, color=theme.CHART_GRID, linewidth=0.6, alpha=0.8)
    return fig, ax


def _render(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=theme.CHART_DPI,
                bbox_inches="tight", facecolor=theme.CHART_FACE)
    plt.close(fig)
    return buffer.getvalue()


def placeholder_chart(title: str) -> bytes:
    """Themed placeholder when stage data is insufficient for a real chart."""
    fig, ax = _fig()
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.55, title, ha="center", va="center",
            fontsize=16, color=theme.DEEP_NAVY, weight="bold")
    ax.text(0.5, 0.4, "Data will populate after stage execution",
            ha="center", va="center", fontsize=10, color=theme.SLATE)
    return _render(fig)


def copilot_vs_agent_trajectory(stage_result: dict) -> bytes:
    """Stage 1: cumulative 12-month net value — copilots vs agentic."""
    copilot = stage_result.get("traditionalCopilots", {}).get("annualNetValue", {})
    agentic = stage_result.get("agenticWorkflows", {}).get("annualNetValue", {})
    if "mid" not in copilot or "mid" not in agentic:
        return placeholder_chart("Copilot vs Agent Trajectory")

    months = np.arange(1, 13)
    copilot_curve = copilot["mid"] * months / 12
    # Agentic ramps with an S-curve (adoption takes ~a quarter to bite).
    ramp = 1 / (1 + np.exp(-(months - 4) / 1.6))
    agentic_curve = agentic["mid"] * (ramp / ramp[-1]) * months / 12

    fig, ax = _fig()
    ax.plot(months, copilot_curve, color=theme.SLATE, linewidth=2.5,
            marker="o", markersize=4, label="Traditional Copilots")
    ax.plot(months, agentic_curve, color=theme.ELECTRIC_SKY, linewidth=2.5,
            marker="o", markersize=4, label="Agentic Workflows")
    ax.fill_between(months, copilot_curve, agentic_curve,
                    where=agentic_curve >= copilot_curve,
                    color=theme.EMERALD, alpha=0.15, label="Agentic advantage")
    ax.set_title("12-Month Cumulative Net Value (mid case)",
                 color=theme.DEEP_NAVY, fontsize=13, weight="bold")
    ax.set_xlabel("Month", color=theme.SLATE)
    ax.set_ylabel("Cumulative net value (USD)", color=theme.SLATE)
    ax.legend(frameon=False, labelcolor=theme.SLATE)
    return _render(fig)


def maturity_radar(stage_result: dict) -> bytes:
    """Stage 2: 5-pillar maturity radar."""
    scores = stage_result.get("pillarScores", {})
    if len(scores) < 3:
        return placeholder_chart("Maturity Radar")

    labels = [k.replace("_", " ").title() for k in scores]
    values = list(scores.values())
    angles = np.linspace(0, 2 * math.pi, len(labels), endpoint=False).tolist()
    values_closed = values + values[:1]
    angles_closed = angles + angles[:1]

    fig = plt.figure(figsize=(6.5, 6.5), facecolor=theme.CHART_FACE)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(theme.CHART_FACE)
    ax.plot(angles_closed, values_closed, color=theme.ELECTRIC_SKY, linewidth=2.5)
    ax.fill(angles_closed, values_closed, color=theme.ELECTRIC_SKY, alpha=0.20)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color=theme.SLATE, fontsize=8)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], color=theme.SLATE, fontsize=8)
    ax.set_title("5-Pillar Maturity Radar", color=theme.DEEP_NAVY,
                 fontsize=13, weight="bold", pad=24)
    return _render(fig)


def architecture_footprint(stage_result: dict) -> bytes:
    """Stage 3: agents & integrations per blueprint component."""
    components = stage_result.get("components", [])
    if not components:
        return placeholder_chart("Architecture Footprint")

    names = [c["name"] if len(c["name"]) <= 28 else c["name"][:25] + "…"
             for c in components]
    agent_counts = [len(c.get("agents", [])) for c in components]
    integration_counts = [len(c.get("integrations", [])) for c in components]
    x = np.arange(len(names))

    fig, ax = _fig(9.0, 4.5)
    ax.bar(x - 0.2, agent_counts, width=0.4, color=theme.ELECTRIC_SKY, label="Agents")
    ax.bar(x + 0.2, integration_counts, width=0.4, color=theme.EMERALD,
           label="Integrations")
    ax.set_xticks(x)
    ax.set_xticklabels(names, color=theme.SLATE, fontsize=8)
    ax.set_title("Execution Architecture Footprint", color=theme.DEEP_NAVY,
                 fontsize=13, weight="bold")
    ax.legend(frameon=False, labelcolor=theme.SLATE)
    return _render(fig)


def evaluator_confidence(stage_result: dict) -> bytes:
    """Stage 4: evaluator scores against governance thresholds."""
    trace = stage_result.get("trace", [])
    evaluator = next((s for s in trace if s.get("step") == 4), None)
    if not evaluator:
        return placeholder_chart("Evaluator Scores")

    fig, ax = _fig(7.0, 4.2)
    metrics = ["Confidence", "Shadow Diff"]
    values = [evaluator.get("confidence", 0), evaluator.get("shadowDiffScore", 0)]
    thresholds = [evaluator.get("thresholds", {}).get("minConfidence", 0.85),
                  evaluator.get("thresholds", {}).get("maxShadowDiff", 0.08)]
    bars = ax.bar(metrics, values, width=0.45,
                  color=[theme.ELECTRIC_SKY, theme.EMERALD])
    for i, threshold in enumerate(thresholds):
        ax.hlines(threshold, i - 0.3, i + 0.3, colors=theme.ROSE,
                  linestyles="dashed", linewidth=2)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.3f}",
                ha="center", color=theme.DEEP_NAVY, weight="bold", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_title("Evaluator Scores vs Governance Thresholds (dashed)",
                 color=theme.DEEP_NAVY, fontsize=13, weight="bold")
    return _render(fig)


def ab_confidence_distribution(stage_result: dict) -> bytes:
    """Stage 5: A/B mean difference with 95% CI band, else NEV bar fallback."""
    ab = stage_result.get("abTest")
    if ab and "ci95" in ab:
        fig, ax = _fig(7.5, 4.2)
        diff = ab["meanDifference"]
        low, high = ab["ci95"]["low"], ab["ci95"]["high"]
        ax.axvspan(low, high, color=theme.ELECTRIC_SKY, alpha=0.18,
                   label="95% CI of mean difference")
        ax.axvline(diff, color=theme.ELECTRIC_SKY, linewidth=2.5, label="Observed lift")
        ax.axvline(0, color=theme.ROSE, linewidth=2, linestyle="dashed",
                   label="No effect")
        ax.set_yticks([])
        ax.set_title(
            f"A/B Lift: {diff:.2f}  (p={ab['welchT']['pValue']:.4f}, "
            f"{'significant' if ab['significantAt005'] else 'not significant'})",
            color=theme.DEEP_NAVY, fontsize=12, weight="bold")
        ax.legend(frameon=False, labelcolor=theme.SLATE, loc="upper left")
        return _render(fig)

    econ = stage_result.get("economics")
    if econ:
        fig, ax = _fig(7.0, 4.2)
        labels = ["Gross savings", "Overhead", "Net value"]
        values = [econ.get("annualGrossSavings", 0), -econ.get("annualOverhead", 0),
                  econ.get("netEconomicValue", 0)]
        colors = [theme.EMERALD, theme.ROSE, theme.ELECTRIC_SKY]
        ax.bar(labels, values, color=colors, width=0.5)
        ax.axhline(0, color=theme.SLATE, linewidth=1)
        ax.set_title("CFO Net Economic Value (annual)", color=theme.DEEP_NAVY,
                     fontsize=13, weight="bold")
        return _render(fig)

    return placeholder_chart("Statistical Evidence")


def roadmap_gantt(stage_result: dict) -> bytes:
    """Stage 6: 30-60-90 Gantt."""
    plan = stage_result.get("plan", [])
    if len(plan) != 3:
        return placeholder_chart("30-60-90 Roadmap")

    fig, ax = _fig(8.5, 3.6)
    colors = [theme.SLATE, theme.ELECTRIC_SKY, theme.EMERALD]
    for i, (phase, color) in enumerate(zip(plan, colors)):
        ax.broken_barh([(i * 30, 30)], (2 - i - 0.35, 0.7), facecolors=color)
        ax.text(i * 30 + 15, 2 - i, phase["theme"], ha="center", va="center",
                color=theme.WHITE, weight="bold", fontsize=10)
    ax.set_xlim(0, 90)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xticks([0, 30, 60, 90])
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels([p["window"] for p in plan], color=theme.SLATE, fontsize=9)
    ax.set_xlabel("Day", color=theme.SLATE)
    ax.set_title("30-60-90 Execution Plan", color=theme.DEEP_NAVY,
                 fontsize=13, weight="bold")
    return _render(fig)


def stage_chart(stage_num: int, stage_result: dict) -> bytes:
    """Dispatch to the stage's signature chart; placeholder on any gap."""
    dispatch = {
        1: copilot_vs_agent_trajectory,
        2: maturity_radar,
        3: architecture_footprint,
        4: evaluator_confidence,
        5: ab_confidence_distribution,
        6: roadmap_gantt,
    }
    renderer = dispatch.get(stage_num)
    if renderer is None:
        return placeholder_chart(f"Stage {stage_num}")
    try:
        return renderer(stage_result or {})
    except Exception:  # noqa: BLE001 — a chart must never sink the deliverable
        return placeholder_chart(f"Stage {stage_num} Chart")
