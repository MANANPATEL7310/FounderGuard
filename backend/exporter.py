"""Report Exporter: generates PDF, HTML, and JSON representations of the evaluation report."""
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ReportLab imports for PDF export
from reportlab.lib import colors  # type: ignore # pyrefly: ignore[missing-source-for-stubs]
from reportlab.lib.pagesizes import letter  # type: ignore # pyrefly: ignore[missing-source-for-stubs]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore # pyrefly: ignore[missing-source-for-stubs]
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore # pyrefly: ignore[missing-source-for-stubs]


class ReportExporter:
    @staticmethod
    def export_json(report: Any, recommendations: Any = None) -> str:
        """Returns structured JSON serialization of the full evaluation report."""
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "report": report.model_dump() if hasattr(report, "model_dump") else report,
            "recommendations": recommendations.model_dump() if hasattr(recommendations, "model_dump") else recommendations,
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def export_html(report: Any, recommendations: Any = None) -> str:
        """Generates a self-contained, beautifully formatted HTML report with clean CSS."""
        rep = report.model_dump() if hasattr(report, "model_dump") else report
        recs = recommendations.model_dump() if hasattr(recommendations, "model_dump") else (recommendations or {})

        eval_id = rep.get("evaluation_id", "N/A")
        interp = rep.get("interpretation", {})
        interp_cat = interp.get("category", "Evaluation Complete")
        interp_summary = interp.get("summary", "")

        sections_html = ""
        for s in rep.get("sections", []):
            sections_html += f"""
            <div class="card">
                <h3>{s.get('section_number', '')}. {s.get('title', '')}</h3>
                <p>{s.get('summary', '')}</p>
            </div>
            """

        recs_list = recs.get("recommendations", [])
        recs_html = ""
        if recs_list:
            recs_html += "<h2>Prioritized Advisory Recommendations</h2>"
            for r in recs_list:
                prio = r.get("priority", "Medium").upper()
                prio_class = "prio-high" if prio == "HIGH" else ("prio-med" if prio == "MEDIUM" else "prio-low")
                steps_li = "".join([f"<li>{step}</li>" for step in r.get("implementation_steps", [])])
                recs_html += f"""
                <div class="rec-card">
                    <span class="badge {prio_class}">[{prio}] {r.get('identified_problem_or_risk')}</span>
                    <h4>Specific Action: {r.get('specific_action')}</h4>
                    <p><strong>Why It Matters:</strong> {r.get('why_it_matters_for_this_startup')}</p>
                    <p><strong>Implementation Steps:</strong></p>
                    <ol>{steps_li}</ol>
                    <p><strong>Expected Benefit:</strong> {r.get('expected_benefit')}</p>
                    <p><strong>Validation Method:</strong> {r.get('validation_method')}</p>
                    <small>Based on: {', '.join(r.get('evidence_refs', []))}</small>
                </div>
                """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Evaluation Report - {eval_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            padding: 40px;
        }}
        .header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0 0 8px 0; color: #0f172a; font-size: 28px; }}
        .header p {{ margin: 0; color: #64748b; font-size: 14px; }}
        .banner {{
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 16px 20px;
            border-radius: 4px;
            margin-bottom: 30px;
        }}
        .banner h2 {{ margin: 0 0 6px 0; font-size: 18px; color: #1e40af; }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .card h3 {{ margin-top: 0; color: #1e293b; font-size: 18px; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px; }}
        .rec-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        }}
        .badge {{
            display: inline-block;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 9999px;
            margin-bottom: 10px;
        }}
        .prio-high {{ background: #fee2e2; color: #b91c1c; }}
        .prio-med {{ background: #fef3c7; color: #b45309; }}
        .prio-low {{ background: #dbeafe; color: #1d4ed8; }}
        .disclaimer {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            padding-top: 20px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Startup Failure Risk & Advisory Report</h1>
            <p>Evaluation ID: <code>{eval_id}</code> | Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}</p>
        </div>

        <div class="banner">
            <h2>{interp_cat}</h2>
            <p>{interp_summary}</p>
        </div>

        <h2>Analytical Assessment (Models A to D)</h2>
        {sections_html}

        {recs_html}

        <div class="disclaimer">
            <p>This report is generated by a multi-model evaluation pipeline and is intended for informational and advisory guidance only. Predictions represent historical statistical distributions and do not guarantee commercial success or failure.</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content

    @staticmethod
    def export_pdf(report: Any, recommendations: Any = None) -> bytes:
        """Generates a professional, multi-page PDF document using ReportLab."""
        rep = report.model_dump() if hasattr(report, "model_dump") else report
        recs = recommendations.model_dump() if hasattr(recommendations, "model_dump") else (recommendations or {})

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=8,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15,
        )
        h2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=8,
        )
        h3_style = ParagraphStyle(
            "Heading3",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6,
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            leftIndent=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        )
        banner_style = ParagraphStyle(
            "Banner",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e40af"),
            backColor=colors.HexColor("#eff6ff"),
            borderColor=colors.HexColor("#93c5fd"),
            borderWidth=1,
            borderPadding=10,
            spaceAfter=15,
        )

        story = []

        # 1. Header
        story.append(Paragraph("Startup Risk Evaluation & Advisory Report", title_style))
        eval_id = rep.get("evaluation_id", "N/A")
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")
        story.append(Paragraph(f"Evaluation ID: {eval_id} &nbsp;|&nbsp; Generated: {date_str}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

        # 2. Overall Interpretation Banner
        interp = rep.get("interpretation", {})
        interp_text = f"<b>{interp.get('category', 'Evaluation Complete')}</b>: {interp.get('summary', '')}"
        story.append(Paragraph(interp_text, banner_style))

        # 3. Model Sections (1 to 8)
        story.append(Paragraph("Core Multi-Model Assessment", h2_style))
        for s in rep.get("sections", [])[:6]:  # sections 1 to 6
            sec_title = f"{s.get('section_number')}. {s.get('title')}"
            story.append(Paragraph(sec_title, h3_style))
            summary_txt = s.get("summary", "")
            story.append(Paragraph(summary_txt, body_style))
            story.append(Spacer(1, 4))

        # 4. Recommendations
        recs_list = recs.get("recommendations", [])
        if recs_list:
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
            story.append(Paragraph("Prioritized Advisory Recommendations", h2_style))

            for idx, r in enumerate(recs_list[:4]):
                prio = r.get("priority", "Medium").upper()
                rec_heading = f"<b>[{prio}] {r.get('identified_problem_or_risk')}</b>"
                story.append(Paragraph(rec_heading, h3_style))
                story.append(Paragraph(f"<b>Specific Action:</b> {r.get('specific_action')}", body_style))
                story.append(Paragraph(f"<b>Why It Matters:</b> {r.get('why_it_matters_for_this_startup')}", body_style))

                steps = r.get("implementation_steps", [])
                if steps:
                    story.append(Paragraph("<b>Implementation Steps:</b>", body_style))
                    for step in steps[:4]:
                        story.append(Paragraph(f"• {step}", bullet_style))

                story.append(Paragraph(f"<b>Validation Target:</b> {r.get('validation_method')}", body_style))
                story.append(Spacer(1, 8))

        # 5. Standing Disclaimer Footer
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))
        disclaimer_text = (
            "<i>Notice: This report provides statistical insights derived from historical datasets. "
            "It does not constitute financial, legal, or investment advice, nor does it guarantee success or prevent failure.</i>"
        )
        story.append(Paragraph(disclaimer_text, ParagraphStyle("Disc", parent=body_style, fontSize=7.5, leading=10, textColor=colors.HexColor("#94a3b8"))))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

