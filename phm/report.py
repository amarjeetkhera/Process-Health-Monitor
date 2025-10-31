from fpdf import FPDF
from datetime import datetime
import pandas as pd




def make_pdf_report(kpis: dict, step_stats: pd.DataFrame, bottlenecks: pd.DataFrame) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Process Health Monitor Executive Summary", ln=1)
    pdf.set_font("Arial", size=12)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 8, f"Generated: {now}", ln=1)


    pdf.ln(4)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Key KPIs", ln=1)
    pdf.set_font("Arial", size=12)
    lines = [
        f"Total cases: {kpis.get('total_cases', 0)}",
        f"Avg throughput: {kpis.get('avg_throughput_h', 0.0):.2f} h",
        f"Median throughput: {kpis.get('median_throughput_h', 0.0):.2f} h",
        f"SLA breach rate: {100*kpis.get('sla_breach_rate', 0.0):.1f}%",
    ]
    for ln in lines:
        pdf.cell(0, 8, ln, ln=1)


    pdf.ln(4)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Top Bottlenecks", ln=1)
    pdf.set_font("Arial", size=11)
    hdr = ["Activity", "Mean h", "Median h", "N", "Bottleneck"]
    colw = [65, 25, 25, 20, 30]
    for w, h in zip(colw, hdr):
        pdf.cell(w, 8, h, border=1)
    pdf.ln(8)
    for _, r in bottlenecks.head(12).iterrows():
        cells = [
            str(r.get("activity", ""))[:36],
            f"{float(r.get('mean_h', 0.0)):.2f}",
            f"{float(r.get('median_h', 0.0)):.2f}",
            f"{int(r.get('occurrences', 0))}",
            "Yes" if bool(r.get("is_bottleneck", False)) else "No",
        ]
        for w, c in zip(colw, cells):
            pdf.cell(w, 8, c, border=1)
        pdf.ln(8)


    return pdf.output(dest='S').encode('latin-1')