"""
reports.py
Compliance Report Generator for ComplyBot.
Generates publication-quality downloadable PDF & printable HTML compliance assessment reports
for businesses, MSMEs, consultants, and importers.
"""

import os
import io
from datetime import datetime
from typing import Dict, Any, Optional

import json

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_product_report_data(query_or_product: str) -> Dict[str, Any]:
    """
    Resolves product data from either compliance_checklists.json or standards_catalog.json.
    Falls back to a structured template if not found.
    """
    q_lower = (query_or_product or "").lower()

    # 1. Check compliance_checklists.json
    checklist_path = os.path.join(DATA_DIR, "compliance_checklists.json")
    if os.path.exists(checklist_path):
        try:
            with open(checklist_path, encoding="utf-8") as f:
                checklists = json.load(f).get("checklists", [])
                for item in checklists:
                    if any(kw.lower() in q_lower for kw in item.get("keywords", [])) or item["product_category"].lower() in q_lower:
                        return item
        except Exception:
            pass

    # 2. Check standards_catalog.json
    catalog_path = os.path.join(DATA_DIR, "standards_catalog.json")
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, encoding="utf-8") as f:
                catalog = json.load(f).get("catalog", [])
                for item in catalog:
                    if any(kw.lower() in q_lower for kw in item.get("keywords", [])) or item["category"].lower() in q_lower:
                        return {
                            "product_category": item["category"],
                            "certification_route": item["scheme"],
                            "risk_level": "Mandatory QCO (High Regulatory Priority)" if item.get("mandatory_qco") else "Voluntary / Standard Scheme",
                            "timeline_estimate": "30-60 calendar days",
                            "estimated_cost_range": "₹35,000 - ₹95,000 (Testing + Application Fee)",
                            "applicable_standards": item.get("is_numbers", []),
                            "marking_requirements": [
                                f"Standard Conformity Mark under {item['scheme']}",
                                "Standard IS number and license/registration number permanently marked on product",
                                "Legible packaging label containing manufacturer address and batch code",
                            ],
                            "testing_required": [
                                f"Safety and performance testing per {item['standard_title']}",
                                f"Key Clauses: {item.get('key_clauses', 'Standard specification testing')}",
                                f"Scope: {item.get('scope', 'Conformity assessment testing')}",
                            ],
                            "documents_needed": [
                                "Manufacturing license and business registration (GST / MSME / CIN)",
                                "Detailed manufacturing process flowchart and machinery list",
                                "In-house test equipment calibration certificates",
                                "Authorized Indian Representative (AIR) appointment letter (for foreign manufacturers)",
                                "NABL / BIS recognized laboratory test report within validity",
                            ],
                            "renewal_period": "2 years (Subject to surveillance audits)",
                            "source_url": item.get("portal_url", "https://manakonline.in"),
                        }
        except Exception:
            pass

    # 3. Default fallback
    category_name = query_or_product.title() if query_or_product else "Industrial & Consumer Product"
    return {
        "product_category": category_name,
        "certification_route": "Scheme I (ISI Mark) / Scheme II (CRS)",
        "risk_level": "Mandatory Quality Control Order (QCO)",
        "timeline_estimate": "4-8 weeks",
        "estimated_cost_range": "₹40,000 - ₹1,20,000 depending on laboratory test parameters",
        "applicable_standards": ["Relevant Indian Standard per BIS Gazette Notification"],
        "marking_requirements": [
            "Conformity Mark affixed prominently on product and outer packaging",
            "Traceable CM/L or R-Number marking with official website link",
        ],
        "testing_required": [
            "Mandatory sample testing at BIS recognized / NABL accredited laboratory",
            "Electrical, mechanical, chemical, or safety performance verification",
        ],
        "documents_needed": [
            "Factory registration and business entity proof",
            "Process flow diagram & list of manufacturing equipment",
            "Quality control manual and test facility records",
            "Raw material test certificates",
        ],
        "renewal_period": "1-2 Years with annual maintenance audit",
    }


def generate_compliance_pdf(product_data: Dict[str, Any], user_name: str = "Industry Applicant") -> io.BytesIO:
    """
    Generates a formal BIS Compliance Assessment Report in PDF format.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#166534"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#374151"),
    )
    badge_style = ParagraphStyle(
        "ReportBadge",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#065f46"),
        backColor=colors.HexColor("#d1fae5"),
        borderPadding=4,
    )

    story = []

    # Title & Header
    story.append(Paragraph("<b>COMPLYBOT</b> — BIS Statutory Compliance Report", title_style))
    story.append(Paragraph(f"Generated for: <b>{user_name}</b> | Date: {datetime.now().strftime('%d %B %Y')} | Assessment Reference: CB-{int(datetime.now().timestamp())}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#22c55e"), spaceAfter=14))

    # Product Overview Table
    prod_name = product_data.get("product_category", "Product Evaluation")
    route = product_data.get("certification_route", "BIS Mandatory Scheme")
    risk = product_data.get("risk_level", "Mandatory QCO")
    timeline = product_data.get("timeline_estimate", "4-8 weeks")
    cost = product_data.get("estimated_cost_range", "Variable")

    meta_table_data = [
        [Paragraph("<b>Product Category:</b>", body_style), Paragraph(prod_name, body_style)],
        [Paragraph("<b>Certification Route:</b>", body_style), Paragraph(route, badge_style)],
        [Paragraph("<b>Statutory Risk Classification:</b>", body_style), Paragraph(risk, body_style)],
        [Paragraph("<b>Estimated Turnaround:</b>", body_style), Paragraph(timeline, body_style)],
        [Paragraph("<b>Estimated Commercial Range:</b>", body_style), Paragraph(cost, body_style)],
    ]
    t = Table(meta_table_data, colWidths=[160, 380])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Section 1: Applicable Standards
    story.append(Paragraph("1. Applicable Indian Standards (IS Specifications)", h2_style))
    stds = product_data.get("applicable_standards", ["Standard per BIS Gazette Order"])
    for s in stds:
        story.append(Paragraph(f"• <b>{s}</b>", body_style))
    story.append(Spacer(1, 10))

    # Section 2: Required Markings
    story.append(Paragraph("2. Statutory Marking & Packaging Requirements", h2_style))
    markings = product_data.get("marking_requirements", ["Conformity mark required on product body and packaging"])
    for m in markings:
        story.append(Paragraph(f"• {m}", body_style))
    story.append(Spacer(1, 10))

    # Section 3: Laboratory Testing Scope
    story.append(Paragraph("3. Prescribed Laboratory Testing Protocols", h2_style))
    tests = product_data.get("testing_required", ["Safety and performance testing at a BIS recognized laboratory"])
    for test in tests:
        story.append(Paragraph(f"• {test}", body_style))
    story.append(Spacer(1, 10))

    # Section 4: Document Checklist
    story.append(Paragraph("4. Pre-Application Document Checklist", h2_style))
    docs = product_data.get("documents_needed", ["Test report, business license, factory details"])
    for i, d in enumerate(docs):
        story.append(Paragraph(f"<b>{i+1}.</b> {d}", body_style))
    story.append(Spacer(1, 14))

    # Footer Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d1d5db"), spaceAfter=8))
    story.append(Paragraph("<i>Disclaimer: This document is an advisory regulatory assessment generated by ComplyBot AI. Official standards, gazette Quality Control Orders (QCOs), and test fees should be verified with the Bureau of Indian Standards (manakonline.in) prior to commercial manufacture or import.</i>", ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7, leading=9, textColor=colors.HexColor("#9ca3af"))))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_compliance_html(product_data: Dict[str, Any], user_name: str = "Industry Applicant") -> str:
    """
    Generates a responsive, printable HTML report with print CSS styling.
    """
    prod_name = product_data.get("product_category", "Product Evaluation")
    route = product_data.get("certification_route", "BIS Mandatory Scheme")
    risk = product_data.get("risk_level", "Mandatory QCO")
    timeline = product_data.get("timeline_estimate", "4-8 weeks")
    cost = product_data.get("estimated_cost_range", "Variable")
    renewal = product_data.get("renewal_period", "Periodic")

    stds_html = "".join(f"<li><strong>{s}</strong></li>" for s in product_data.get("applicable_standards", []))
    marks_html = "".join(f"<li>{m}</li>" for m in product_data.get("marking_requirements", []))
    tests_html = "".join(f"<li>{t}</li>" for t in product_data.get("testing_required", []))
    docs_html = "".join(f"<li>{d}</li>" for d in product_data.get("documents_needed", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ComplyBot Assessment Report — {prod_name}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1f2937; margin: 40px auto; max-width: 800px; line-height: 1.5; }}
  .header {{ border-bottom: 3px solid #22c55e; padding-bottom: 12px; margin-bottom: 24px; }}
  .brand {{ font-size: 24px; font-weight: 800; color: #166534; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px; }}
  .meta-item {{ font-size: 14px; }}
  .badge {{ background: #d1fae5; color: #065f46; padding: 3px 8px; border-radius: 999px; font-weight: 600; font-size: 12px; display: inline-block; }}
  h2 {{ color: #111827; font-size: 16px; margin-top: 20px; border-bottom: 1px solid #f3f4f6; padding-bottom: 4px; }}
  ul, ol {{ padding-left: 20px; font-size: 14px; color: #374151; }}
  li {{ margin-bottom: 6px; }}
  .disclaimer {{ font-size: 11px; color: #9ca3af; margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 12px; }}
  @media print {{ body {{ margin: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
  <div class="header">
    <div class="brand">COMPLYBOT</div>
    <div>BIS Conformity & Regulatory Assessment Report</div>
    <div style="font-size:12px; color:#6b7280; margin-top:4px;">Applicant: {user_name} | Generated: {datetime.now().strftime('%d %B %Y')}</div>
  </div>

  <div class="meta-grid">
    <div class="meta-item"><strong>Product Category:</strong> {prod_name}</div>
    <div class="meta-item"><strong>Certification Route:</strong> <span class="badge">{route}</span></div>
    <div class="meta-item"><strong>Statutory Risk:</strong> {risk}</div>
    <div class="meta-item"><strong>Turnaround Timeline:</strong> {timeline}</div>
    <div class="meta-item"><strong>Estimated Cost:</strong> {cost}</div>
    <div class="meta-item"><strong>Renewal Period:</strong> {renewal}</div>
  </div>

  <h2>1. Mandatory Applicable Standards</h2>
  <ul>{stds_html}</ul>

  <h2>2. Statutory Marking & Labeling Rules</h2>
  <ul>{marks_html}</ul>

  <h2>3. Laboratory Testing Protocols</h2>
  <ul>{tests_html}</ul>

  <h2>4. Pre-Application Document Checklist</h2>
  <ol>{docs_html}</ol>

  <div class="disclaimer">
    Disclaimer: Advisory regulatory report synthesized by ComplyBot AI for Indian Standards conformity. Official notifications should be verified with the Bureau of Indian Standards (manakonline.in).
  </div>
</body>
</html>
"""
