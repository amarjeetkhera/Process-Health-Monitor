import math
import matplotlib.pyplot as plt
from graphviz import Digraph
import pandas as pd



def plot_throughput_trend(throughput_by_day: pd.DataFrame):
    fig = plt.figure(figsize=(8,3))
    plt.plot(throughput_by_day["day"], throughput_by_day["completed_cases"], marker="o")
    plt.xlabel("Day")
    plt.ylabel("Completed cases")
    plt.tight_layout()
    return fig


def build_process_graph(df: pd.DataFrame, step_stats: pd.DataFrame, color_by: str = "mean_h") -> Digraph:
    temp = df.sort_values(["case_id", "timestamp"]).copy()
    temp["next_act"] = temp.groupby("case_id")["activity"].shift(-1)
    transitions = temp.dropna(subset=["next_act"]).groupby(["activity", "next_act"]).size().reset_index(name="count")
    m = step_stats.set_index("activity").to_dict(orient="index")


    means = step_stats["mean_h"].fillna(0)
    if len(means) == 0:
        min_mean, max_mean = 0.0, 1.0
    else:       
        min_mean, max_mean = float(means.min()), float(means.max())
        if math.isclose(min_mean, max_mean):
            max_mean = min_mean + 1.0


    def color_for_mean(x):
        t = (x - min_mean) / (max_mean - min_mean)
        r = int(255 * t)
        g = int(180 * (1 - t))
        b = 60
        return f"#{r:02x}{g:02x}{b:02x}"


    dot = Digraph(engine="dot")
    dot.attr(rankdir="LR", splines="spline", nodesep="0.4", ranksep="0.6")

    for a in sorted(df["activity"].unique().tolist()):
        info = m.get(a, {})
        mean_h = float(info.get("mean_h", 0.0))
        occ = int(info.get("occurrences", 0))
        color = color_for_mean(mean_h)
        label = f"{a}\nmean: {mean_h:.2f} h\nN: {occ}"
        dot.node(
            a, 
            label=label, 
            style="filled", 
            fillcolor=color, 
            shape="box", 
            color="#333333")
    
    for _, row in transitions.iterrows():
        a, b, c = row["activity"], row["next_act"], int(row["count"])
        dot.edge(a, b, label=str(c))
    return dot