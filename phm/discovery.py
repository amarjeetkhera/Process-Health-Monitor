import math
import pandas as pd

def detect_bottlenecks(step_stats: pd.DataFrame, method: str = "zscore", threshold: float = 2.0, percentile: float = 0.9) -> pd.DataFrame:
    s = step_stats.copy()
    if s.empty:
        s["is_bottleneck"] = False
        s["score"] = 0.0
        return s
    if method == "zscore":
        mu = s["mean_h"].mean()
        sd = s["mean_h"].std(ddof=0) or 1e-6
        s["score"] = (s["mean_h"] - mu) / sd
        s["is_bottleneck"] = s["score"] >= threshold
    else:
        cut = s["mean_h"].quantile(percentile)
        s["score"] = s["mean_h"]
        s["is_bottleneck"] = s["mean_h"] >= cut
    return s.sort_values(["is_bottleneck", "score"], ascending=[False, False])