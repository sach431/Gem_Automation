# services/pdf_export.py
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

os.makedirs("downloads", exist_ok=True)

def export_to_pdf(df, prefix="report"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{prefix}_{ts}.pdf"
    pdf_path = os.path.join("downloads", file_name)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Report", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if df is None or df.empty:
        elements.append(Paragraph("No data to display", styles['Normal']))
    else:
        data = [list(df.columns)] + df.fillna("").values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2D6CDF')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(table)

    doc.build(elements)
    return pdf_path, file_name
