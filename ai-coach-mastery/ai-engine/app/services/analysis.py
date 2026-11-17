"""Statistical analysis services (SciPy / statsmodels / NumPy).

Implements the before/after ROI evaluation used by coaching engagements:
Welch's t-test on pre/post metric samples plus a simple OLS trend fit.
"""

from __future__ import annotations

import numpy as np
import statsmodels.api as sm
from scipy import stats


def roi_significance(before: list[float], after: list[float]) -> dict:
    """Welch's t-test comparing pre vs. post intervention metric samples.

    Returns effect size (Cohen's d), p-value, means, and a plain-language verdict.
    Raises ValueError for samples too small to analyze (< 2 observations each).
    """
    if len(before) < 2 or len(after) < 2:
        raise ValueError("Each sample must contain at least 2 observations")

    before_arr = np.asarray(before, dtype=float)
    after_arr = np.asarray(after, dtype=float)

    t_stat, p_value = stats.ttest_ind(after_arr, before_arr, equal_var=False)

    # Cohen's d with pooled standard deviation; guard zero variance.
    pooled_std = np.sqrt((before_arr.var(ddof=1) + after_arr.var(ddof=1)) / 2.0)
    cohens_d = float((after_arr.mean() - before_arr.mean()) / pooled_std) if pooled_std > 0 else 0.0

    significant = bool(p_value < 0.05)
    return {
        "mean_before": float(before_arr.mean()),
        "mean_after": float(after_arr.mean()),
        "uplift_pct": float(
            (after_arr.mean() - before_arr.mean()) / abs(before_arr.mean()) * 100.0
        ) if before_arr.mean() != 0 else None,
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "cohens_d": cohens_d,
        "significant_at_0_05": significant,
        "verdict": (
            "Statistically significant improvement" if significant and cohens_d > 0
            else "Statistically significant decline" if significant
            else "No statistically significant change detected"
        ),
    }


def trend(values: list[float]) -> dict:
    """OLS linear trend over an ordered metric series (statsmodels).

    Returns slope, intercept and R² so dashboards can plot the fitted line.
    """
    if len(values) < 3:
        raise ValueError("Trend analysis requires at least 3 observations")

    y = np.asarray(values, dtype=float)
    x = sm.add_constant(np.arange(len(y), dtype=float))
    model = sm.OLS(y, x).fit()

    return {
        "slope": float(model.params[1]),
        "intercept": float(model.params[0]),
        "r_squared": float(model.rsquared),
        "direction": "up" if model.params[1] > 0 else "down" if model.params[1] < 0 else "flat",
    }
