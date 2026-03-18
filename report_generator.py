"""
Report generation: interactive HTML dashboard and PDF report.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette (shared)
# ---------------------------------------------------------------------------
COLOR_PASS = "#00d4aa"
COLOR_WARN = "#f59e0b"
COLOR_FAIL = "#ef4444"
COLOR_BG = "#0a0a0a"
COLOR_CARD = "#141414"
COLOR_ACCENT = "#00d4ff"
COLOR_TEXT = "#e5e7eb"
COLOR_SUBTEXT = "#9ca3af"


# ---------------------------------------------------------------------------
# HTML Dashboard
# ---------------------------------------------------------------------------

def _status_color(status: str) -> str:
    return {"pass": COLOR_PASS, "warning": COLOR_WARN, "fail": COLOR_FAIL}.get(status, "#6b7280")


def _status_emoji(status: str) -> str:
    return {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(status, "•")


def _score_color(score: int) -> str:
    if score >= 70:
        return COLOR_PASS
    if score >= 40:
        return COLOR_WARN
    return COLOR_FAIL


def generate_html_dashboard(audit_data: Dict[str, Any], audit_id: int = 0) -> str:
    """
    Return a self-contained HTML string for the interactive SEO audit dashboard.
    Plotly charts are embedded as JSON and rendered via the Plotly CDN.
    """
    score = audit_data.get("score", 0)
    url = audit_data.get("url", "")
    timestamp = audit_data.get("timestamp", datetime.now(timezone.utc).isoformat())
    summary = audit_data.get("summary", {})
    categories = audit_data.get("categories", {})
    checks = audit_data.get("checks", [])
    page_info = audit_data.get("page_info", {})

    # ---- Plotly chart data (JSON) ----------------------------------------
    # Gauge chart
    gauge_data = json.dumps(
        {
            "data": [
                {
                    "type": "indicator",
                    "mode": "gauge+number",
                    "value": score,
                    "title": {"text": "SEO Score", "font": {"size": 20, "color": COLOR_TEXT}},
                    "number": {"font": {"size": 48, "color": _score_color(score)}, "suffix": "/100"},
                    "gauge": {
                        "axis": {"range": [0, 100], "tickcolor": COLOR_SUBTEXT, "tickfont": {"color": COLOR_SUBTEXT}},
                        "bar": {"color": _score_color(score)},
                        "bgcolor": COLOR_CARD,
                        "bordercolor": "#333",
                        "steps": [
                            {"range": [0, 40], "color": "#2d0a0a"},
                            {"range": [40, 70], "color": "#2d1f0a"},
                            {"range": [70, 100], "color": "#0a2d1f"},
                        ],
                        "threshold": {
                            "line": {"color": COLOR_ACCENT, "width": 3},
                            "thickness": 0.85,
                            "value": score,
                        },
                    },
                }
            ],
            "layout": {
                "paper_bgcolor": COLOR_CARD,
                "plot_bgcolor": COLOR_CARD,
                "font": {"color": COLOR_TEXT},
                "margin": {"t": 60, "b": 20, "l": 20, "r": 20},
                "height": 300,
            },
        }
    )

    # Pie chart – pass / warning / fail
    pie_data = json.dumps(
        {
            "data": [
                {
                    "type": "pie",
                    "labels": ["Passed", "Warnings", "Failed"],
                    "values": [
                        summary.get("passed", 0),
                        summary.get("warnings", 0),
                        summary.get("failed", 0),
                    ],
                    "marker": {"colors": [COLOR_PASS, COLOR_WARN, COLOR_FAIL]},
                    "hole": 0.45,
                    "textfont": {"color": "#fff"},
                    "hovertemplate": "%{label}: %{value} (%{percent})<extra></extra>",
                }
            ],
            "layout": {
                "paper_bgcolor": COLOR_CARD,
                "plot_bgcolor": COLOR_CARD,
                "font": {"color": COLOR_TEXT},
                "showlegend": True,
                "legend": {"font": {"color": COLOR_TEXT}},
                "margin": {"t": 40, "b": 20, "l": 20, "r": 20},
                "height": 300,
                "title": {"text": "Checks Distribution", "font": {"color": COLOR_TEXT}},
            },
        }
    )

    # Bar chart – category scores
    cat_names = list(categories.keys())
    cat_values = list(categories.values())
    cat_colors = [_score_color(v) for v in cat_values]
    bar_data = json.dumps(
        {
            "data": [
                {
                    "type": "bar",
                    "x": cat_names,
                    "y": cat_values,
                    "marker": {"color": cat_colors},
                    "hovertemplate": "%{x}: %{y}/100<extra></extra>",
                }
            ],
            "layout": {
                "paper_bgcolor": COLOR_CARD,
                "plot_bgcolor": COLOR_BG,
                "font": {"color": COLOR_TEXT},
                "yaxis": {"range": [0, 100], "gridcolor": "#222", "tickfont": {"color": COLOR_SUBTEXT}},
                "xaxis": {"tickfont": {"color": COLOR_TEXT}},
                "margin": {"t": 40, "b": 40, "l": 50, "r": 20},
                "height": 300,
                "title": {"text": "Category Scores", "font": {"color": COLOR_TEXT}},
            },
        }
    )

    # ---- Build checks table rows ----------------------------------------
    rows_html = ""
    for c in checks:
        color = _status_color(c["status"])
        emoji = _status_emoji(c["status"])
        rec = c.get("recommendation", "")
        rec_html = f'<div class="rec">💡 {rec}</div>' if rec else ""
        rows_html += f"""
        <tr>
          <td><span class="badge" style="background:{color}22;color:{color};border:1px solid {color}44">{emoji} {c['status'].upper()}</span></td>
          <td class="cat-label">{c.get('category','')}</td>
          <td class="check-name">{c.get('name','')}</td>
          <td>{c.get('detail','')} {rec_html}</td>
        </tr>"""

    # ---- Category score cards -------------------------------------------
    cat_cards_html = ""
    for cat, sc in categories.items():
        col = _score_color(sc)
        cat_cards_html += f"""
        <div class="cat-card">
          <div class="cat-score" style="color:{col}">{sc}</div>
          <div class="cat-name">{cat}</div>
          <div class="cat-bar"><div class="cat-bar-fill" style="width:{sc}%;background:{col}"></div></div>
        </div>"""

    # ---- Page info rows -------------------------------------------------
    pi = page_info or {}
    page_rows = f"""
      <tr><th>Title</th><td>{pi.get('title','—')}</td></tr>
      <tr><th>Description</th><td>{pi.get('description','—') or '—'}</td></tr>
      <tr><th>H1 Count</th><td>{pi.get('h1_count','—')}</td></tr>
      <tr><th>Page Size</th><td>{pi.get('page_size_kb','—')} KB</td></tr>
      <tr><th>Load Time (est.)</th><td>{pi.get('load_time_ms','—')} ms</td></tr>
      <tr><th>Total Links</th><td>{pi.get('link_count','—')}</td></tr>
      <tr><th>Internal Links</th><td>{pi.get('internal_links','—')}</td></tr>
      <tr><th>External Links</th><td>{pi.get('external_links','—')}</td></tr>
    """

    # ---- Assemble full HTML ---------------------------------------------
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SEO Audit Dashboard | ATI &amp; AI</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,sans-serif;background:{COLOR_BG};color:{COLOR_TEXT};line-height:1.6}}
  a{{color:{COLOR_ACCENT};text-decoration:none}}
  /* Header */
  .header{{background:linear-gradient(135deg,#0d1117 0%,#161b22 100%);border-bottom:1px solid #00d4ff33;padding:24px 40px;display:flex;align-items:center;gap:20px}}
  .logo{{font-size:1.8rem;font-weight:800;color:{COLOR_ACCENT};letter-spacing:-0.5px}}
  .logo span{{color:#fff}}
  .header-meta{{margin-left:auto;text-align:right;color:{COLOR_SUBTEXT};font-size:0.85rem}}
  /* Layout */
  .container{{max-width:1200px;margin:0 auto;padding:32px 20px}}
  .section{{margin-bottom:40px}}
  h2{{font-size:1.25rem;font-weight:700;color:{COLOR_ACCENT};margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #333}}
  /* Summary cards */
  .summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:24px}}
  .summary-card{{background:{COLOR_CARD};border-radius:12px;padding:20px;text-align:center;border:1px solid #222}}
  .summary-card .val{{font-size:2.2rem;font-weight:800;margin-bottom:4px}}
  .summary-card .lbl{{font-size:0.8rem;color:{COLOR_SUBTEXT};text-transform:uppercase;letter-spacing:0.5px}}
  /* Charts grid */
  .charts-grid{{display:grid;grid-template-columns:1fr 1fr 2fr;gap:20px}}
  @media(max-width:900px){{.charts-grid{{grid-template-columns:1fr}}}}
  .chart-card{{background:{COLOR_CARD};border-radius:12px;padding:16px;border:1px solid #222}}
  /* Category cards */
  .cats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}
  .cat-card{{background:{COLOR_CARD};border-radius:12px;padding:20px;border:1px solid #222}}
  .cat-score{{font-size:2rem;font-weight:800;margin-bottom:4px}}
  .cat-name{{font-size:0.85rem;color:{COLOR_SUBTEXT};margin-bottom:10px}}
  .cat-bar{{height:4px;background:#222;border-radius:2px}}
  .cat-bar-fill{{height:100%;border-radius:2px;transition:width .4s}}
  /* Findings table */
  .table-wrap{{overflow-x:auto;border-radius:12px;border:1px solid #222}}
  table{{width:100%;border-collapse:collapse;background:{COLOR_CARD}}}
  th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid #1a1a1a;font-size:0.875rem}}
  th{{background:#0d0d0d;color:{COLOR_SUBTEXT};font-weight:600;text-transform:uppercase;font-size:0.75rem;letter-spacing:0.5px}}
  tr:hover td{{background:#1a1a1a}}
  .badge{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;white-space:nowrap}}
  .cat-label{{color:{COLOR_SUBTEXT};font-size:0.8rem}}
  .check-name{{font-weight:600}}
  .rec{{margin-top:4px;font-size:0.8rem;color:{COLOR_WARN};font-style:italic}}
  /* Page info */
  .info-table th{{width:160px;color:{COLOR_SUBTEXT};font-size:0.8rem}}
  /* Footer */
  .footer{{text-align:center;color:{COLOR_SUBTEXT};font-size:0.8rem;padding:32px 20px;border-top:1px solid #1a1a1a;margin-top:40px}}
  /* Download btn */
  .btn{{display:inline-block;padding:8px 20px;background:{COLOR_ACCENT};color:#000;border-radius:8px;font-weight:600;font-size:0.875rem;margin-top:8px;cursor:pointer;border:none}}
  .btn:hover{{opacity:0.85}}
</style>
</head>
<body>
<div class="header">
  <div class="logo">ATI &amp; <span>AI</span></div>
  <div style="color:{COLOR_SUBTEXT};font-size:0.95rem;margin-left:12px">Professional SEO Audit Report</div>
  <div class="header-meta">
    <div><strong style="color:{COLOR_TEXT}">{url}</strong></div>
    <div>Generated: {timestamp}</div>
    {"<div>Audit ID: " + str(audit_id) + "</div>" if audit_id else ""}
  </div>
</div>

<div class="container">

  <!-- Summary cards -->
  <div class="section">
    <h2>Executive Summary</h2>
    <div class="summary-grid">
      <div class="summary-card">
        <div class="val" style="color:{_score_color(score)}">{score}</div>
        <div class="lbl">SEO Score</div>
      </div>
      <div class="summary-card">
        <div class="val" style="color:{COLOR_PASS}">{summary.get('passed',0)}</div>
        <div class="lbl">Passed</div>
      </div>
      <div class="summary-card">
        <div class="val" style="color:{COLOR_WARN}">{summary.get('warnings',0)}</div>
        <div class="lbl">Warnings</div>
      </div>
      <div class="summary-card">
        <div class="val" style="color:{COLOR_FAIL}">{summary.get('failed',0)}</div>
        <div class="lbl">Failed</div>
      </div>
      <div class="summary-card">
        <div class="val">{summary.get('total',0)}</div>
        <div class="lbl">Total Checks</div>
      </div>
    </div>
  </div>

  <!-- Charts -->
  <div class="section">
    <h2>Performance Overview</h2>
    <div class="charts-grid">
      <div class="chart-card"><div id="gauge"></div></div>
      <div class="chart-card"><div id="pie"></div></div>
      <div class="chart-card"><div id="bar"></div></div>
    </div>
  </div>

  <!-- Category scores -->
  <div class="section">
    <h2>Category Scores</h2>
    <div class="cats-grid">
      {cat_cards_html}
    </div>
  </div>

  <!-- Page info -->
  <div class="section">
    <h2>Page Information</h2>
    <div class="table-wrap">
      <table class="info-table">
        <tbody>
          {page_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Detailed findings -->
  <div class="section">
    <h2>Detailed Findings</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Category</th>
            <th>Check</th>
            <th>Details &amp; Recommendations</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

</div><!-- /container -->

<div class="footer">
  &copy; {datetime.now(timezone.utc).year} ATI &amp; AI — Automated Technical Insights &amp; AI. All rights reserved.
</div>

<script>
(function(){{
  var gaugeData = {gauge_data};
  Plotly.newPlot('gauge', gaugeData.data, gaugeData.layout, {{responsive:true, displayModeBar:false}});
  var pieData = {pie_data};
  Plotly.newPlot('pie', pieData.data, pieData.layout, {{responsive:true, displayModeBar:false}});
  var barData = {bar_data};
  Plotly.newPlot('bar', barData.data, barData.layout, {{responsive:true, displayModeBar:false}});
}})();
</script>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# PDF Report
# ---------------------------------------------------------------------------

def generate_pdf_report(
    audit_data: Dict[str, Any],
    customer_name: str = "",
    business_name: str = "",
) -> bytes:
    """
    Generate a professional PDF report using ReportLab.
    Returns the PDF as bytes.
    """
    try:
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # ---- Styles ---------------------------------------------------------
        base_styles = getSampleStyleSheet()

        def style(name, parent="Normal", **kw):
            return ParagraphStyle(name, parent=base_styles[parent], **kw)

        dark_bg = colors.HexColor("#0a0a0a")
        accent = colors.HexColor("#00d4ff")
        white = colors.white
        light_grey = colors.HexColor("#e5e7eb")
        subtext = colors.HexColor("#9ca3af")
        pass_col = colors.HexColor("#00d4aa")
        warn_col = colors.HexColor("#f59e0b")
        fail_col = colors.HexColor("#ef4444")

        title_style = style("Cover_Title", fontSize=32, textColor=accent, spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica-Bold")
        subtitle_style = style("Cover_Sub", fontSize=14, textColor=light_grey, spaceAfter=4, alignment=TA_CENTER)
        body_style = style("Body_Custom", fontSize=10, textColor=light_grey, spaceAfter=4, leading=16)
        h1_style = style("H1_Custom", fontSize=18, textColor=accent, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
        h2_style = style("H2_Custom", fontSize=13, textColor=white, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold")
        small_style = style("Small_Custom", fontSize=9, textColor=subtext, spaceAfter=2)

        # ---- Colours for status
        def status_color(st: str):
            return {"pass": pass_col, "warning": warn_col, "fail": fail_col}.get(st, subtext)

        def status_text(st: str):
            return {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}.get(st, st.upper())

        score = audit_data.get("score", 0)
        url = audit_data.get("url", "")
        timestamp = audit_data.get("timestamp", "")
        summary = audit_data.get("summary", {})
        categories = audit_data.get("categories", {})
        checks = audit_data.get("checks", [])
        page_info = audit_data.get("page_info", {})

        story = []

        # ---- Cover page -----------------------------------------------------
        story.append(Spacer(1, 40 * mm))
        story.append(Paragraph("ATI &amp; AI", title_style))
        story.append(Paragraph("Professional SEO Audit Report", subtitle_style))
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width="100%", thickness=1, color=accent, spaceAfter=8))
        story.append(Paragraph(f"<b>Website:</b> {url}", body_style))
        if customer_name:
            story.append(Paragraph(f"<b>Prepared for:</b> {customer_name}", body_style))
        if business_name:
            story.append(Paragraph(f"<b>Business:</b> {business_name}", body_style))
        story.append(Paragraph(f"<b>Date:</b> {timestamp[:10]}", body_style))
        story.append(Spacer(1, 10 * mm))

        # Big score display
        score_col = colors.HexColor("#00d4aa") if score >= 70 else (colors.HexColor("#f59e0b") if score >= 40 else colors.HexColor("#ef4444"))
        score_table = Table(
            [[Paragraph(f'<font color="#{score_col.hexval()[2:]}"><b>{score}</b></font>', style("Score_Big", fontSize=60, textColor=score_col, alignment=TA_CENTER, fontName="Helvetica-Bold")),
              Paragraph("/ 100<br/>Overall SEO Score", style("Score_Label", fontSize=18, textColor=light_grey, alignment=TA_CENTER))]],
            colWidths=["40%", "60%"],
        )
        score_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(score_table)
        story.append(PageBreak())

        # ---- Executive Summary ----------------------------------------------
        story.append(Paragraph("Executive Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=accent, spaceAfter=6))

        exec_data = [
            ["Metric", "Value"],
            ["Total Checks", str(summary.get("total", 0))],
            ["Passed", str(summary.get("passed", 0))],
            ["Warnings", str(summary.get("warnings", 0))],
            ["Failed", str(summary.get("failed", 0))],
            ["Overall Score", f"{score}/100"],
        ]
        exec_table = Table(exec_data, colWidths=["50%", "50%"])
        exec_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#141414")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), accent),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 1), (-1, -1), light_grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0d0d0d")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0d0d0d"), colors.HexColor("#141414")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(exec_table)
        story.append(Spacer(1, 8 * mm))

        # ---- Category breakdown ---------------------------------------------
        story.append(Paragraph("Category Breakdown", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=accent, spaceAfter=6))
        cat_data = [["Category", "Score"]]
        for cat, sc in categories.items():
            cat_data.append([cat, f"{sc}/100"])
        cat_table = Table(cat_data, colWidths=["70%", "30%"])
        cat_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#141414")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), accent),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 1), (-1, -1), light_grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0d0d0d"), colors.HexColor("#141414")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(cat_table)
        story.append(Spacer(1, 8 * mm))

        # ---- Key Findings ---------------------------------------------------
        story.append(Paragraph("Key Findings", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=accent, spaceAfter=6))

        failed_checks = [c for c in checks if c["status"] == "fail"]
        warning_checks = [c for c in checks if c["status"] == "warning"]

        if failed_checks:
            story.append(Paragraph("Critical Issues", h2_style))
            for c in failed_checks:
                story.append(Paragraph(f"• <b>{c['name']}</b>: {c['detail']}", body_style))
                if c.get("recommendation"):
                    story.append(Paragraph(f"  → {c['recommendation']}", small_style))

        if warning_checks:
            story.append(Paragraph("Warnings", h2_style))
            for c in warning_checks:
                story.append(Paragraph(f"• <b>{c['name']}</b>: {c['detail']}", body_style))
                if c.get("recommendation"):
                    story.append(Paragraph(f"  → {c['recommendation']}", small_style))

        story.append(PageBreak())

        # ---- Full findings table --------------------------------------------
        story.append(Paragraph("Detailed Check Results", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=accent, spaceAfter=6))

        checks_data = [["Status", "Category", "Check Name", "Detail"]]
        for c in checks:
            sc = status_color(c["status"])
            checks_data.append(
                [
                    Paragraph(f'<font color="#{sc.hexval()[2:]}">{status_text(c["status"])}</font>',
                               style(f"st_{c['status']}", fontSize=9, fontName="Helvetica-Bold")),
                    Paragraph(c.get("category", ""), small_style),
                    Paragraph(f"<b>{c.get('name','')}</b>", body_style),
                    Paragraph(c.get("detail", ""), small_style),
                ]
            )

        checks_table = Table(checks_data, colWidths=["12%", "15%", "28%", "45%"])
        checks_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#141414")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), accent),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0d0d0d"), colors.HexColor("#141414")]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#222")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(checks_table)

        # ---- Build PDF ------------------------------------------------------
        doc.build(story)
        return buf.getvalue()

    except Exception as exc:
        logger.error("PDF generation failed: %s", exc, exc_info=True)
        # Return a minimal fallback PDF
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.setFont("Helvetica", 14)
            c.drawString(72, 700, "ATI & AI - SEO Audit Report")
            c.setFont("Helvetica", 10)
            c.drawString(72, 680, f"URL: {audit_data.get('url', '')}")
            c.drawString(72, 660, f"Score: {audit_data.get('score', 0)}/100")
            c.drawString(72, 640, f"Error generating full report: {exc}")
            c.save()
            return buf.getvalue()
        except Exception:
            return b""
