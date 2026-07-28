import io
import datetime
import pandas as pd
from typing import Union, List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.units import inch

def _add_page_number(canvas, doc):
    """Add page number and footer to each page."""
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.gray)
    page_num = canvas.getPageNumber()
    footer_text = f"DataMind AI - Professional Report - Page {page_num}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    canvas.drawString(inch, 0.5 * inch, footer_text)
    canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Generated: {timestamp}")
    canvas.restoreState()

def parse_markdown_to_platypus(text: str, styles) -> List:
    """Very simple markdown parser to platypus elements."""
    elements = []
    lines = text.split('\n')
    normal_style = styles['Normal']
    header_style = styles['Heading2']
    header3_style = styles['Heading3']
    list_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=2,
    )
    
    current_paragraph = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_paragraph:
                elements.append(Paragraph(" ".join(current_paragraph), normal_style))
                current_paragraph = []
            elements.append(Spacer(1, 0.1 * inch))
            continue
            
        import re
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        line = re.sub(r'__(.*?)__', r'<b>\1</b>', line)
        line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
        line = re.sub(r'```(.*?)```', r'<font face="Courier">\1</font>', line)
        
        if stripped.startswith("### "):
            if current_paragraph:
                elements.append(Paragraph(" ".join(current_paragraph), normal_style))
                current_paragraph = []
            elements.append(Paragraph(line.replace("### ", "").strip(), header3_style))
        elif stripped.startswith("## ") or stripped.startswith("# "):
            if current_paragraph:
                elements.append(Paragraph(" ".join(current_paragraph), normal_style))
                current_paragraph = []
            elements.append(Paragraph(re.sub(r'^#+ ', '', line).strip(), header_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if current_paragraph:
                elements.append(Paragraph(" ".join(current_paragraph), normal_style))
                current_paragraph = []
            # Bullet point
            clean_line = re.sub(r'^[\-\*]\s+', '', line)
            elements.append(Paragraph(f"<bullet>&bull;</bullet>{clean_line}", list_style))
        elif re.match(r'^\d+\.\s+', stripped):
            if current_paragraph:
                elements.append(Paragraph(" ".join(current_paragraph), normal_style))
                current_paragraph = []
            # Numbered list
            elements.append(Paragraph(line, list_style))
        else:
            current_paragraph.append(line)
            
    if current_paragraph:
        elements.append(Paragraph(" ".join(current_paragraph), normal_style))
        
    return elements

def generate_pdf_report(title: str, content: Union[str, List[Dict[str, Any]]]) -> bytes:
    """
    Generates a professional PDF report from structured data blocks.
    content can be a simple markdown string, or a list of blocks:
    [
      {"type": "markdown", "text": "..."},
      {"type": "sql", "text": "SELECT * ..."},
      {"type": "table", "dataframe": pd.DataFrame()},
      {"type": "chart", "image_bytes": bytes}
    ]
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    
    elements = []
    
    # Title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    blocks = []
    if isinstance(content, str):
        blocks = [{"type": "markdown", "text": content}]
    else:
        blocks = content
        
    for block in blocks:
        btype = block.get("type", "markdown")
        
        if btype == "markdown":
            text = block.get("text", "")
            if text:
                elements.extend(parse_markdown_to_platypus(text, styles))
                
        elif btype == "sql":
            sql_text = block.get("text", "")
            if sql_text:
                elements.append(Paragraph("<b>SQL Query Executed:</b>", styles['Heading3']))
                sql_style = ParagraphStyle(
                    'SQL',
                    parent=styles['Code'],
                    fontName='Courier',
                    backColor=colors.whitesmoke,
                    borderColor=colors.lightgrey,
                    borderWidth=1,
                    borderPadding=10,
                    borderRadius=5
                )
                # Replace newlines with <br/> for Platypus Paragraph
                sql_html = sql_text.replace('\n', '<br/>')
                elements.append(Paragraph(sql_html, sql_style))
                elements.append(Spacer(1, 0.1 * inch))
                
        elif btype == "table":
            df = block.get("dataframe")
            if df is not None and not df.empty:
                elements.append(Paragraph("<b>Data Sample:</b>", styles['Heading3']))
                # Limit to 10 rows for PDF to prevent overflow
                display_df = df.head(10)
                data = [display_df.columns.to_list()] + display_df.values.tolist()
                
                # Convert all items to string to prevent ReportLab formatting errors
                data = [[str(cell)[:50] + ('...' if len(str(cell)) > 50 else '') for cell in row] for row in data]
                
                # Dynamic column widths based on page size
                # A letter page is 8.5 inches wide, margins are 1 inch each = 6.5 inches printable
                available_width = 6.5 * inch
                num_cols = len(data[0])
                col_width = available_width / num_cols if num_cols > 0 else available_width
                
                t = Table(data, colWidths=[col_width] * num_cols, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.2 * inch))
                
        elif btype == "chart":
            img_bytes = block.get("image_bytes")
            if img_bytes:
                try:
                    img_buffer = io.BytesIO(img_bytes)
                    img = RLImage(img_buffer)
                    
                    # Scale image to fit page width (6.5 inches)
                    max_width = 6.5 * inch
                    if img.drawWidth > max_width:
                        scale = max_width / img.drawWidth
                        img.drawWidth = max_width
                        img.drawHeight = img.drawHeight * scale
                        
                    elements.append(img)
                    elements.append(Spacer(1, 0.2 * inch))
                except Exception as e:
                    elements.append(Paragraph(f"<i>[Chart could not be rendered: {str(e)}]</i>", styles['Normal']))
                    
        else:
            # Fallback
            elements.append(Paragraph(f"<i>[Unsupported block type: {btype}]</i>", styles['Normal']))
            
        elements.append(Spacer(1, 0.1 * inch))
        
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    
    return buffer.getvalue()
