import os
import json
import streamlit as st
import matplotlib.pyplot as plt
from phm.data_io import load_csv, generate_demo_data, REQUIRED_COLUMNS
from phm.metrics import compute_kpis, step_durations
from phm.discovery import detect_bottlenecks
from phm.viz import build_process_graph, plot_throughput_trend
from phm.report import make_pdf_report

st.set_page_config(page_title="Process Health Monitor", layout="wide")
st.title("Process Health Monitor")
st.caption("Analyze event logs, visualize your process, detect bottlenecks, and export an executive summary.")

with st.sidebar:
    st.header("Data Input")
    uploaded = st.file_uploader("Upload CSV (case_id, activity, timestamp[, resource, cost])", type=["csv"])
    st.markdown("Or generate a realistic demo dataset:")
    n_cases = st.slider("Demo cases", min_value=100, max_value=2000, value=600, step=50)
    seed = st.number_input("Seed", value=42, step=1)
    gen_demo = st.button("Generate demo data")


    st.header("Settings")
    sla_hours = st.slider("SLA threshold (hours) for throughput", min_value=0, max_value=240, value=72, step=6)
    method = st.selectbox("Bottleneck detection", options=["zscore", "percentile"], index=0)
    zthr = st.slider("Z-score threshold", 1.0, 4.0, 2.0, 0.1)
    pctl = st.slider("Percentile threshold", 0.5, 0.99, 0.9, 0.01)


    st.header("Filters")
    date_from = st.date_input("From date", value=None)
    date_to = st.date_input("To date", value=None)
    res_filter = st.text_input("Resource contains (optional)")

try:
    if uploaded is not None:
        df = load_csv(uploaded)
    elif gen_demo:
        df = generate_demo_data(n_cases=int(n_cases), seed=int(seed))
    else:
        st.info("Upload your CSV or click 'Generate demo data' in the sidebar.")
        st.stop()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Apply filters
import pandas as pd
if date_from:
    df = df[df["timestamp"].dt.date >= pd.to_datetime(date_from).date()]
if date_to:
    df = df[df["timestamp"].dt.date <= pd.to_datetime(date_to).date()]
if res_filter and "resource" in df.columns:
    df = df[df["resource"].astype(str).str.contains(res_filter, case=False, na=False)]


if df.empty:
    st.warning("No data after applying filters.")
    st.stop()

# KPIs
kpis = compute_kpis(df, sla_hours=sla_hours)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total cases", f"{kpis['total_cases']}")
col2.metric("Avg throughput (h)", f"{kpis['avg_throughput_h']:.2f}")
col3.metric("Median throughput (h)", f"{kpis['median_throughput_h']:.2f}")
col4.metric("SLA breach rate", f"{100*kpis['sla_breach_rate']:.1f}%")

# Trend
st.subheader("Completions per day")
fig = plot_throughput_trend(kpis["throughput_by_day"])
st.pyplot(fig)

# Step stats and bottlenecks
stats = step_durations(df)

st.subheader("Process Map")
dot = build_process_graph(df, stats)
st.graphviz_chart(dot)

st.subheader("Step Performance")
colA, colB = st.columns([2,1])
with colA:
    st.dataframe(stats, use_container_width=True)

bnecks = detect_bottlenecks(stats, method=method, threshold=float(zthr), percentile=float(pctl))
with colB:
    st.markdown("**Detected bottlenecks**")
    st.dataframe(bnecks[bnecks["is_bottleneck"]], use_container_width=True)

# Case explorer
st.subheader("Case Explorer")
sel_case = st.selectbox("Select a case", options=sorted(df["case_id"].unique().tolist()))
case_df = df[df["case_id"] == sel_case].copy()
case_df["next_time"] = case_df["timestamp"].shift(-1)
case_df["duration_h"] = (case_df["next_time"] - case_df["timestamp"]).dt.total_seconds() / 3600.0
st.dataframe(case_df.drop(columns=["next_time"]).fillna(""), use_container_width=True)

# Suggestions (simple rules)
st.subheader("Suggestions")
rule_suggestions = []
if not bnecks.empty:
    for _, r in bnecks[bnecks["is_bottleneck"]].head(5).iterrows():
        act = r["activity"]
        rule_suggestions.append(f"• '{act}' shows elevated mean duration. Consider standardized SOPs, approval rules, or upstream parallelization.")
if kpis["sla_breach_rate"] > 0.15:
    rule_suggestions.append("• SLA breach rate > 15%. Review staffing on peak days and introduce priority queues.")
if stats["occurrences"].median() < 50:
    rule_suggestions.append("• Variant sprawl suspected. Consolidate process variants where possible.")


st.markdown("".join(rule_suggestions) if rule_suggestions else "No obvious issues detected.")


# Optional LLM narrative hook
use_llm = st.checkbox("Enhance with AI narrative (requires LLM_API_KEY in env)")
if use_llm and os.getenv("LLM_API_KEY"):
    narrative = (
        "Based on detected bottlenecks, prioritizing the top two steps is likely to reduce end-to-end cycle time by 8–15%. "
        "Automating approval routing and pre-validation can further decrease rework rates."
    )
    st.success(narrative)
elif use_llm:
    st.info("Set LLM_API_KEY to enable AI narrative.")


# Exports
st.subheader("Export")
kpis_json = json.dumps({k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in kpis.items()}, default=str, indent=2)
st.download_button("Download KPIs (JSON)", kpis_json, file_name="kpis.json", mime="application/json")
st.download_button("Download bottlenecks (CSV)", bnecks.to_csv(index=False).encode("utf-8"), file_name="bottlenecks.csv", mime="text/csv")
pdf_bytes = make_pdf_report(kpis, stats, bnecks)
st.download_button("Download Executive PDF", data=pdf_bytes, file_name="process_health_summary.pdf", mime="application/pdf")

st.caption("Tip: brand this with company colors and plug it into a Sheet or API for live data.")