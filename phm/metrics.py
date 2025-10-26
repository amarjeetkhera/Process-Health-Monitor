import pandas as pd


def compute_kpis(df: pd.DataFrame, sla_hours: float) -> dict:
    first = df.groupby("case_id")["timestamp"].min()
    last = df.groupby("case_id")["timestamp"].max()
    throughput_hours = (last - first).dt.total_seconds() / 3600.0


    kpis = {
        "total_cases": len(throughput_hours),
        "avg_throughput_h": float(throughput_hours.mean()) if len(throughput_hours) else 0.0,
        "median_throughput_h": float(throughput_hours.median()) if len(throughput_hours) else 0.0,
        "sla_breach_rate": float((throughput_hours > sla_hours).mean()) if sla_hours else 0.0,
    }


    completed = df.groupby("case_id")["timestamp"].max().reset_index()
    completed["day"] = completed["timestamp"].dt.date
    throughput_by_day = completed.groupby("day")["timestamp"].count().rename("completed_cases").reset_index()
    kpis["throughput_by_day"] = throughput_by_day
    kpis["throughput_hours_by_case"] = throughput_hours
    return kpis




def step_durations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["case_id", "timestamp"]).copy()
    df["next_time"] = df.groupby("case_id")["timestamp"].shift(-1)
    df["duration_h"] = (df["next_time"] - df["timestamp"]).dt.total_seconds() / 3600.0
    stats = (
        df.dropna(subset=["duration_h"]).groupby("activity")["duration_h"]
        .agg(["count", "mean", "median", "std"]).reset_index()
        .rename(columns={"count": "occurrences", "mean": "mean_h", "median": "median_h", "std": "std_h"})
    )
    return stats