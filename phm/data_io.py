import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["case_id", "activity", "timestamp"]
OPTIONAL_COLUMNS = ["resource", "cost"]

def load_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in REQUIRED_COLUMNS:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("Invalid timestamps detected. Use ISO formats or YYYY-MM-DD HH:MM:SS.")
    return df.sort_values(["case_id", "timestamp"]).reset_index(drop=True)

def generate_demo_data(n_cases: int = 500, seed: int= 42) -> pd.DataFrame:
    # sanity guards
    assert callable(int), "int was shadowed somewhere"
    assert hasattr(pd, "Timestamp"), "pandas was shadowed"
    rng = np.random.default_rng(seed)
    activities = [
        ("Receive Order", 0.2, 1.0)
        ("Validate", 0.5, 2.0),
        ("Approve", 0.8, 3.5),
        ("Fulfill", 1.0, 6.0),
        ("Invoice", 0.5, 2.0),
        ("Pay", 0.3, 1.5),
    ]
    base_date = pd.Timestamp.now() - pd.Timedelta(days=60)
    rows = []
    for i in range(n_cases):
        case = f"C{i:05d}"
        t = base_date + pd.Timedelta(days=int(rng.integers(0,45)))
        path = []
        for name, mu, sigma in activities:
            if name == "Approve" and rng.random() < 0.1:
                path.append(("Re-Validate", 0.8, 2.5))
            path.append((name, mu, sigma))
        for step_name, mu, sigma in path:
            dur_hours = max(0.05, float(rng.normal(mu, sigma)))
            wait_hours = max(0.05, float(rng.normal(mu * 0.5, sigma * 0.4)))
            t = t + pd.Timedelta(hours=wait_hours)
            rows.append({
                "case_id": case,
                "activity": step_name,
                "timestamp": t,
                "resource": rng.choice(["Clerk A", "Clerk B", "Boss", "Robot"], p=[0.35,0.35,0.2,0.1]),
                "cost": round(max(1.0, float(rng.normal(20, 5))), 2)
            })
            t = t + pd.Timedelta(hours=dur_hours)
    df = pd.DataFrame(rows)
    return df.sort_values(["case_id", "timestamp"]).reset_index(drop=True)