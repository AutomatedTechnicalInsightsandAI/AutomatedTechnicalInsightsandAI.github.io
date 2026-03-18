"""
Report generation: interactive HTML dashboard and PDF report.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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


# ---------------------------------------------------------------------------
# Influencer Reports
# ---------------------------------------------------------------------------

def generate_influencer_html_report(
    influencer_data: Dict[str, Any],
    scorecard: Optional[Dict[str, Any]] = None,
    audience_quality: Optional[Dict[str, Any]] = None,
    content_performance: Optional[Dict[str, Any]] = None,
    growth_trend: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Return a self-contained HTML report for an influencer profile.

    Parameters mirror the dicts produced by influencer_metrics.py helpers.
    Plotly charts are embedded as JSON and rendered via the Plotly CDN.
    """
    scorecard = scorecard or {}
    audience_quality = audience_quality or {}
    content_performance = content_performance or {}
    growth_trend = growth_trend or {}

    username = influencer_data.get("username", "Unknown")
    platform = influencer_data.get("platform", "").capitalize()
    follower_count = influencer_data.get("follower_count", 0)
    tier_label = influencer_data.get("tier_label", "")
    engagement_rate = content_performance.get(
        "engagement_rate", influencer_data.get("engagement_rate", 0.0)
    )
    overall_score = scorecard.get("overall_score", 0)
    score_color = _score_color(int(overall_score))

    # ── Scorecard gauge ──────────────────────────────────────────────────────
    gauge_data = json.dumps({
        "data": [{
            "type": "indicator",
            "mode": "gauge+number",
            "value": overall_score,
            "title": {"text": "Influencer Score", "font": {"size": 18, "color": COLOR_TEXT}},
            "number": {"font": {"size": 44, "color": score_color}, "suffix": "/100"},
            "gauge": {
                "axis": {"range": [0, 100], "tickcolor": COLOR_SUBTEXT},
                "bar": {"color": score_color},
                "bgcolor": COLOR_CARD,
                "bordercolor": "#333",
                "steps": [
                    {"range": [0, 35], "color": "#2d0a0a"},
                    {"range": [35, 65], "color": "#2d1f0a"},
                    {"range": [65, 100], "color": "#0a2d1f"},
                ],
            },
        }],
        "layout": {
            "paper_bgcolor": COLOR_BG,
            "plot_bgcolor": COLOR_BG,
            "margin": {"t": 60, "b": 20, "l": 20, "r": 20},
            "height": 250,
        },
    })

    # ── Audience quality pie ─────────────────────────────────────────────────
    real_pct = audience_quality.get("real_follower_pct", 80.0)
    suspicious_pct = audience_quality.get("suspicious_follower_pct", 5.0)
    other_pct = max(0.0, 100.0 - real_pct - suspicious_pct)
    audience_pie_data = json.dumps({
        "data": [{
            "type": "pie",
            "labels": ["Real Followers", "Suspicious", "Unknown"],
            "values": [real_pct, suspicious_pct, other_pct],
            "marker": {"colors": [COLOR_PASS, COLOR_FAIL, COLOR_WARN]},
            "textinfo": "label+percent",
            "textfont": {"color": COLOR_TEXT},
            "hole": 0.4,
        }],
        "layout": {
            "paper_bgcolor": COLOR_BG,
            "plot_bgcolor": COLOR_BG,
            "font": {"color": COLOR_TEXT},
            "showlegend": False,
            "margin": {"t": 30, "b": 20, "l": 20, "r": 20},
            "height": 250,
        },
    })

    # ── Growth trend line ────────────────────────────────────────────────────
    snapshots = growth_trend.get("snapshots", [])
    dates = [s.get("date", "") for s in snapshots]
    followers_series = [s.get("followers", 0) for s in snapshots]
    growth_chart_data = json.dumps({
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": dates,
            "y": followers_series,
            "line": {"color": COLOR_ACCENT, "width": 2},
            "marker": {"color": COLOR_ACCENT, "size": 6},
            "name": "Followers",
        }],
        "layout": {
            "paper_bgcolor": COLOR_BG,
            "plot_bgcolor": COLOR_BG,
            "font": {"color": COLOR_TEXT},
            "xaxis": {"gridcolor": "#222", "title": "Date"},
            "yaxis": {"gridcolor": "#222", "title": "Followers"},
            "margin": {"t": 30, "b": 60, "l": 60, "r": 20},
            "height": 250,
        },
    })

    # ── Scorecard component bars ─────────────────────────────────────────────
    components = scorecard.get("components", {})
    comp_labels = ["Authenticity", "Engagement", "Audience Size", "Growth"]
    comp_keys = ["authenticity", "engagement", "audience_size", "growth"]
    comp_values = [components.get(k, 0) for k in comp_keys]
    comp_colors = [
        COLOR_PASS if v >= 20 else COLOR_WARN if v >= 10 else COLOR_FAIL
        for v in comp_values
    ]
    bar_data = json.dumps({
        "data": [{
            "type": "bar",
            "x": comp_labels,
            "y": comp_values,
            "marker": {"color": comp_colors},
            "text": [f"{v:.1f}" for v in comp_values],
            "textposition": "outside",
            "textfont": {"color": COLOR_TEXT},
        }],
        "layout": {
            "paper_bgcolor": COLOR_BG,
            "plot_bgcolor": COLOR_BG,
            "font": {"color": COLOR_TEXT},
            "yaxis": {"range": [0, 35], "gridcolor": "#222"},
            "xaxis": {"gridcolor": "#222"},
            "margin": {"t": 30, "b": 60, "l": 50, "r": 20},
            "height": 250,
        },
    })

    top_interests = audience_quality.get("top_interests", [])
    top_countries = audience_quality.get("top_countries", [])
    gender_split = audience_quality.get("gender_split", {})
    age_dist = audience_quality.get("age_distribution", {})

    def _kv_row(label: str, value: Any) -> str:
        return (
            f"<tr><td style='color:{COLOR_SUBTEXT};padding:6px 12px 6px 0'>{label}</td>"
            f"<td style='color:{COLOR_TEXT};font-weight:600'>{value}</td></tr>"
        )

    profile_rows = "".join([
        _kv_row("Platform", platform),
        _kv_row("Followers", f"{follower_count:,}"),
        _kv_row("Tier", tier_label),
        _kv_row("Engagement Rate", f"{engagement_rate:.2f}%"),
        _kv_row("Authenticity Score", f"{audience_quality.get('authenticity_score', 0):.1f}/100"),
        _kv_row("Overall Score", f"{overall_score:.1f}/100"),
        _kv_row("Score Rating", scorecard.get("rating", "").replace("_", " ").title()),
    ])

    interests_html = (
        " ".join(
            f"<span style='background:{COLOR_CARD};border:1px solid #333;"
            f"border-radius:12px;padding:2px 10px;font-size:0.8rem'>{i}</span>"
            for i in top_interests
        )
        if top_interests
        else "<em style='color:#555'>No data</em>"
    )

    countries_html = ""
    for c in top_countries[:5]:
        country = c.get("country", "")
        pct = c.get("pct", 0)
        countries_html += (
            f"<div style='display:flex;justify-content:space-between;"
            f"margin-bottom:4px'>"
            f"<span style='color:{COLOR_TEXT}'>{country}</span>"
            f"<span style='color:{COLOR_ACCENT}'>{pct:.1f}%</span></div>"
        )
    if not countries_html:
        countries_html = "<em style='color:#555'>No data</em>"

    gender_html = " | ".join(
        f"<b style='color:{COLOR_TEXT}'>{g.title()}</b> {p:.1f}%"
        for g, p in gender_split.items()
    ) or "<em style='color:#555'>No data</em>"

    age_html = " | ".join(
        f"<b style='color:{COLOR_TEXT}'>{bracket}</b> {pct:.1f}%"
        for bracket, pct in sorted(age_dist.items())
    ) or "<em style='color:#555'>No data</em>"

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Influencer Report — {username}</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:{COLOR_BG};color:{COLOR_TEXT};font-family:'Segoe UI',system-ui,sans-serif;padding:24px}}
    h2{{color:{COLOR_ACCENT};margin-bottom:8px}}
    h3{{color:{COLOR_SUBTEXT};font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin:24px 0 8px}}
    .card{{background:{COLOR_CARD};border-radius:12px;padding:20px;margin-bottom:20px}}
    .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
    .grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
    .metric{{background:{COLOR_BG};border:1px solid #222;border-radius:10px;padding:16px;text-align:center}}
    .metric-val{{font-size:1.6rem;font-weight:800;color:{COLOR_ACCENT}}}
    .metric-lbl{{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:{COLOR_SUBTEXT};margin-top:4px}}
    .hero{{background:linear-gradient(135deg,#0d2137,#1e3a5f);border-radius:16px;padding:32px;margin-bottom:24px}}
    .hero h1{{font-size:2rem;font-weight:800;color:white}}
    .hero .sub{{color:rgba(255,255,255,0.7);margin-top:8px}}
    table{{width:100%;border-collapse:collapse}}
    @media(max-width:700px){{.grid2,.grid4{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
  <div class="hero">
    <h1>@{username}</h1>
    <div class="sub">{platform} · {tier_label} · Generated {now_str}</div>
  </div>

  <div class="grid4">
    <div class="metric"><div class="metric-val">{follower_count:,}</div><div class="metric-lbl">Followers</div></div>
    <div class="metric"><div class="metric-val">{engagement_rate:.2f}%</div><div class="metric-lbl">Engagement Rate</div></div>
    <div class="metric"><div class="metric-val">{audience_quality.get('authenticity_score', 0):.0f}</div><div class="metric-lbl">Authenticity Score</div></div>
    <div class="metric"><div class="metric-val" style="color:{score_color}">{overall_score:.0f}</div><div class="metric-lbl">Overall Score</div></div>
  </div>

  <div class="grid2" style="margin-top:20px">
    <div class="card">
      <h3>Influencer Score</h3>
      <div id="gauge_chart"></div>
    </div>
    <div class="card">
      <h3>Score Components</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h3>Audience Authenticity</h3>
      <div id="audience_pie"></div>
    </div>
    <div class="card">
      <h3>Follower Growth Trend</h3>
      <div id="growth_chart"></div>
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h3>Profile Summary</h3>
      <table>{profile_rows}</table>
    </div>
    <div class="card">
      <h3>Audience Demographics</h3>
      <p style="font-size:0.8rem;color:{COLOR_SUBTEXT};margin-bottom:6px">Gender</p>
      <p style="margin-bottom:12px">{gender_html}</p>
      <p style="font-size:0.8rem;color:{COLOR_SUBTEXT};margin-bottom:6px">Age Groups</p>
      <p style="margin-bottom:12px">{age_html}</p>
      <p style="font-size:0.8rem;color:{COLOR_SUBTEXT};margin-bottom:6px">Top Countries</p>
      {countries_html}
    </div>
  </div>

  <div class="card">
    <h3>Top Interests</h3>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">{interests_html}</div>
  </div>

  <script>
    Plotly.newPlot('gauge_chart', {gauge_data}.data, {gauge_data}.layout, {{responsive:true}});
    Plotly.newPlot('bar_chart', {bar_data}.data, {bar_data}.layout, {{responsive:true}});
    Plotly.newPlot('audience_pie', {audience_pie_data}.data, {audience_pie_data}.layout, {{responsive:true}});
    Plotly.newPlot('growth_chart', {growth_chart_data}.data, {growth_chart_data}.layout, {{responsive:true}});
  </script>
</body>
</html>"""


def generate_campaign_roi_report(
    campaign: Dict[str, Any],
    influencers: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Return a self-contained HTML campaign ROI report.

    Parameters
    ----------
    campaign:   Campaign dict (same schema as database.get_campaign).
    influencers: List of campaign influencer dicts (from get_campaign_influencers).
    """
    influencers = influencers or []
    name = campaign.get("campaign_name", "Campaign")
    budget = campaign.get("budget", 0.0)
    actual_reach = campaign.get("actual_reach", 0)
    impressions = campaign.get("impressions", 0)
    clicks = campaign.get("clicks", 0)
    conversions = campaign.get("conversions", 0)
    revenue = campaign.get("revenue", 0.0)
    roi = campaign.get("roi", 0.0)
    status = campaign.get("status", "").title()

    ctr = round(clicks / max(impressions, 1) * 100, 4)
    cpm = round(budget / max(impressions, 1) * 1000, 2)
    cpc = round(budget / max(clicks, 1), 2)
    cvr = round(conversions / max(clicks, 1) * 100, 4)

    roi_color = COLOR_PASS if roi >= 0 else COLOR_FAIL
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Funnel chart
    funnel_data = json.dumps({
        "data": [{
            "type": "funnel",
            "y": ["Reach", "Impressions", "Clicks", "Conversions"],
            "x": [actual_reach, impressions, clicks, conversions],
            "marker": {"color": [COLOR_ACCENT, COLOR_PASS, COLOR_WARN, COLOR_FAIL]},
            "textinfo": "value+percent initial",
        }],
        "layout": {
            "paper_bgcolor": COLOR_BG,
            "plot_bgcolor": COLOR_BG,
            "font": {"color": COLOR_TEXT},
            "margin": {"t": 30, "b": 30, "l": 120, "r": 20},
            "height": 280,
        },
    })

    # Influencer table rows
    inf_rows = ""
    for inf in influencers:
        inf_rows += (
            f"<tr>"
            f"<td>@{inf.get('username', '')}</td>"
            f"<td>{inf.get('platform', '').title()}</td>"
            f"<td>{inf.get('follower_count', 0):,}</td>"
            f"<td>${inf.get('fee', 0):.0f}</td>"
            f"<td>{inf.get('expected_impressions', 0):,}</td>"
            f"<td>{inf.get('actual_impressions', 0):,}</td>"
            f"<td>{inf.get('status', '').title()}</td>"
            f"</tr>"
        )
    if not inf_rows:
        inf_rows = "<tr><td colspan='7' style='color:#555;text-align:center'>No influencers linked</td></tr>"

    def _metric_card(label: str, value: str, color: str = COLOR_ACCENT) -> str:
        return (
            f"<div class='metric'>"
            f"<div class='metric-val' style='color:{color}'>{value}</div>"
            f"<div class='metric-lbl'>{label}</div>"
            f"</div>"
        )

    metrics_html = "".join([
        _metric_card("Budget", f"${budget:,.2f}"),
        _metric_card("Revenue", f"${revenue:,.2f}", COLOR_PASS),
        _metric_card("ROI", f"{roi:.1f}%", roi_color),
        _metric_card("Reach", f"{actual_reach:,}"),
        _metric_card("Impressions", f"{impressions:,}"),
        _metric_card("Clicks", f"{clicks:,}"),
        _metric_card("Conversions", f"{conversions:,}"),
        _metric_card("CTR", f"{ctr:.2f}%"),
        _metric_card("CPM", f"${cpm:.2f}"),
        _metric_card("CPC", f"${cpc:.2f}"),
        _metric_card("CVR", f"{cvr:.2f}%"),
        _metric_card("Status", status),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Campaign Report — {name}</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:{COLOR_BG};color:{COLOR_TEXT};font-family:'Segoe UI',system-ui,sans-serif;padding:24px}}
    h3{{color:{COLOR_SUBTEXT};font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin:24px 0 8px}}
    .card{{background:{COLOR_CARD};border-radius:12px;padding:20px;margin-bottom:20px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-bottom:20px}}
    .metric{{background:{COLOR_BG};border:1px solid #222;border-radius:10px;padding:14px;text-align:center}}
    .metric-val{{font-size:1.4rem;font-weight:800;color:{COLOR_ACCENT}}}
    .metric-lbl{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.5px;color:{COLOR_SUBTEXT};margin-top:4px}}
    .hero{{background:linear-gradient(135deg,#0d2137,#1e3a5f);border-radius:16px;padding:28px;margin-bottom:24px}}
    .hero h1{{font-size:1.8rem;font-weight:800;color:white}}
    .hero .sub{{color:rgba(255,255,255,0.7);margin-top:6px}}
    table{{width:100%;border-collapse:collapse;font-size:0.88rem}}
    th{{color:{COLOR_SUBTEXT};text-align:left;padding:8px;border-bottom:1px solid #222;font-weight:600}}
    td{{color:{COLOR_TEXT};padding:8px;border-bottom:1px solid #1a1a1a}}
    tr:hover td{{background:#1c1c1c}}
  </style>
</head>
<body>
  <div class="hero">
    <h1>{name}</h1>
    <div class="sub">Status: {status} · Generated {now_str}</div>
  </div>

  <div class="grid">{metrics_html}</div>

  <div class="card">
    <h3>Conversion Funnel</h3>
    <div id="funnel_chart"></div>
  </div>

  <div class="card">
    <h3>Influencers in Campaign</h3>
    <table>
      <thead>
        <tr><th>Handle</th><th>Platform</th><th>Followers</th><th>Fee</th>
            <th>Expected Impr.</th><th>Actual Impr.</th><th>Status</th></tr>
      </thead>
      <tbody>{inf_rows}</tbody>
    </table>
  </div>

  <script>
    Plotly.newPlot('funnel_chart', {funnel_data}.data, {funnel_data}.layout, {{responsive:true}});
  </script>
</body>
</html>"""


def generate_influencer_comparison_html(
    influencers: List[Dict[str, Any]],
) -> str:
    """
    Return an HTML comparison matrix for a list of influencer dicts.

    Each influencer dict should include profile metrics and optionally
    'scorecard', 'audience_quality', and 'content_performance' sub-dicts.
    """
    if not influencers:
        return "<p>No influencers to compare.</p>"

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    headers = [
        "Handle", "Platform", "Tier", "Followers", "Engagement Rate",
        "Authenticity", "Overall Score", "Rating",
    ]

    rows_html = ""
    for inf in influencers:
        aq = inf.get("audience_quality", {})
        sc = inf.get("scorecard", {})
        cp = inf.get("content_performance", {})
        er = cp.get("engagement_rate", inf.get("engagement_rate", 0.0))
        overall = sc.get("overall_score", 0)
        score_col = COLOR_PASS if overall >= 65 else COLOR_WARN if overall >= 35 else COLOR_FAIL
        rows_html += (
            f"<tr>"
            f"<td><a href='{inf.get('profile_url', '#')}' style='color:{COLOR_ACCENT}'>"
            f"@{inf.get('username', '')}</a></td>"
            f"<td>{inf.get('platform', '').title()}</td>"
            f"<td>{inf.get('tier_label', '')}</td>"
            f"<td>{inf.get('follower_count', 0):,}</td>"
            f"<td>{er:.2f}%</td>"
            f"<td>{aq.get('authenticity_score', 0):.1f}</td>"
            f"<td style='color:{score_col};font-weight:700'>{overall:.1f}</td>"
            f"<td>{sc.get('rating', '').replace('_', ' ').title()}</td>"
            f"</tr>"
        )

    header_html = "".join(f"<th>{h}</th>" for h in headers)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Influencer Comparison — ATI &amp; AI</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:{COLOR_BG};color:{COLOR_TEXT};font-family:'Segoe UI',system-ui,sans-serif;padding:24px}}
    h1{{color:{COLOR_ACCENT};margin-bottom:8px;font-size:1.6rem}}
    .sub{{color:{COLOR_SUBTEXT};font-size:0.85rem;margin-bottom:20px}}
    .card{{background:{COLOR_CARD};border-radius:12px;padding:20px}}
    table{{width:100%;border-collapse:collapse;font-size:0.88rem}}
    th{{color:{COLOR_SUBTEXT};text-align:left;padding:10px 8px;border-bottom:2px solid #222;font-weight:600;white-space:nowrap}}
    td{{color:{COLOR_TEXT};padding:10px 8px;border-bottom:1px solid #1a1a1a}}
    tr:hover td{{background:#1c1c1c}}
  </style>
</head>
<body>
  <h1>Influencer Comparison Matrix</h1>
  <div class="sub">Generated {now_str} · {len(influencers)} influencer(s)</div>
  <div class="card">
    <table>
      <thead><tr>{header_html}</tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</body>
</html>"""
