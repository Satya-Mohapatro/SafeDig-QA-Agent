"""
SafeDig AI - Enterprise Markdown to PDF Compiler
Uses ReportLab to convert rich Markdown documents into publication-grade,
beautifully styled, multi-page PDF specifications with running headers, footers,
tables, code syntax blocks, and alerts.
"""

import os
import re
import html
from typing import List, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# SafeDig Color Palette
NAVY_HEADER = colors.HexColor('#0f172a')
ACCENT_BLUE = colors.HexColor('#1d4ed8')
SLATE_DARK = colors.HexColor('#1e293b')
SLATE_BODY = colors.HexColor('#334155')
SLATE_MUTED = colors.HexColor('#64748b')
BORDER_COLOR = colors.HexColor('#e2e8f0')
BG_CODE = colors.HexColor('#f8fafc')
BG_ALERT = colors.HexColor('#f1f5f9')
BG_TABLE_HDR = colors.HexColor('#0f172a')
BG_TABLE_ALT = colors.HexColor('#f8fafc')
GREEN_EMERALD = colors.HexColor('#10b981')
AMBER_WARNING = colors.HexColor('#d97706')
RED_ALERT = colors.HexColor('#dc2626')

class SafeDigNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.doc_title = kwargs.get('doc_title', 'SafeDig AI Engineering Specification')
        self.doc_subtitle = kwargs.get('doc_subtitle', 'HSG47 / CDM 2015 Safety Assurance')

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        self.saveState()
        # Top Header Banner
        self.setFillColor(NAVY_HEADER)
        self.rect(0, 742, 612, 50, fill=True, stroke=False)
        
        # Title & Subtitle in Banner
        self.setFillColor(colors.white)
        self.setFont('Helvetica-Bold', 11)
        self.drawString(36, 764, getattr(self, 'doc_title', 'SafeDig AI Specification'))
        
        self.setFillColor(colors.HexColor('#93c5fd'))
        self.setFont('Helvetica', 8)
        self.drawString(36, 751, getattr(self, 'doc_subtitle', 'UK Underground Utility Dig-Safety Map QA Platform'))
        
        # Badge on Right
        self.setFillColor(colors.HexColor('#1e293b'))
        self.roundRect(470, 750, 106, 20, 3, fill=True, stroke=False)
        self.setFillColor(GREEN_EMERALD)
        self.setFont('Helvetica-Bold', 7.5)
        self.drawCentredString(523, 756, "HSG47 COMPLIANT")

        # Bottom Running Footer
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.8)
        self.line(36, 36, 576, 36)
        
        self.setFont('Helvetica', 8)
        self.setFillColor(SLATE_MUTED)
        self.drawString(36, 24, "SafeDig AI Platform — Safety-Critical Engineering Documentation")
        
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(576, 24, page_str)
        self.restoreState()


def get_safedig_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='SDTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=NAVY_HEADER,
        spaceBefore=14,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='SDHeading1',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=NAVY_HEADER,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SDHeading2',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SDHeading3',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=SLATE_DARK,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SDBody',
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=SLATE_BODY,
        spaceBefore=2,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='SDBullet',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=SLATE_BODY,
        leftIndent=14,
        firstLineIndent=-10,
        spaceBefore=1,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name='SDAlert',
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=SLATE_DARK,
        spaceBefore=4,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='SDCodeLine',
        fontName='Courier',
        fontSize=6.8,
        leading=9,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=0,
        spaceAfter=0
    ))

    styles.add(ParagraphStyle(
        name='SDTableCell',
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.5,
        textColor=SLATE_BODY
    ))

    styles.add(ParagraphStyle(
        name='SDTableHdr',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.white
    ))

    return styles


def format_inline_markdown(text: str) -> str:
    """Format markdown bold, code, and links into ReportLab HTML tags."""
    # First escape bare XML entities
    # Split by code spans first to avoid escaping inside code
    parts = re.split(r'(`[^`]+`)', text)
    formatted_parts = []
    
    for part in parts:
        if part.startswith('`') and part.endswith('`') and len(part) >= 2:
            code_content = part[1:-1]
            escaped_code = html.escape(code_content)
            formatted_parts.append(f'<font name="Courier" color="#1d4ed8"><b>{escaped_code}</b></font>')
        else:
            # Escape HTML
            s = html.escape(part)
            # Bold: **bold** or __bold__
            s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
            s = re.sub(r'__(.+?)__', r'<b>\1</b>', s)
            # Italic: *italic* or _italic_
            s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', s)
            # Links: [text](url) -> text
            s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<font color="#1d4ed8"><u>\1</u></font>', s)
            formatted_parts.append(s)
            
    return "".join(formatted_parts)


def parse_markdown_to_flowables(md_content: str, styles) -> List:
    lines = md_content.splitlines()
    flowables = []
    
    in_code_block = False
    code_block_lines = []
    
    in_table = False
    table_raw_rows = []
    
    in_quote = False
    quote_lines = []

    def flush_code_block():
        nonlocal in_code_block, code_block_lines
        if code_block_lines:
            # Chunk code lines into blocks of up to 24 lines so tables fit cleanly on a single page
            chunk_size = 24
            for c_idx in range(0, len(code_block_lines), chunk_size):
                chunk = code_block_lines[c_idx:c_idx + chunk_size]
                raw_code = "\n".join(chunk)
                escaped_code = html.escape(raw_code)
                p = Preformatted(escaped_code, styles['SDCodeLine'])
                t = Table([[p]], colWidths=[540])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), BG_CODE),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                flowables.append(Spacer(1, 2))
                flowables.append(t)
                flowables.append(Spacer(1, 3))
            code_block_lines = []
        in_code_block = False

    def flush_table():
        nonlocal in_table, table_raw_rows
        if table_raw_rows:
            # Parse rows
            parsed_rows = []
            for r in table_raw_rows:
                cells = [c.strip() for c in r.strip().strip('|').split('|')]
                parsed_rows.append(cells)
            
            # Determine num columns
            num_cols = max(len(r) for r in parsed_rows) if parsed_rows else 0
            if num_cols > 0:
                # Normalize row cell count
                norm_rows = []
                for r in parsed_rows:
                    if len(r) < num_cols:
                        r = r + [''] * (num_cols - len(r))
                    norm_rows.append(r[:num_cols])
                
                # Available width = 540pt
                col_width = 540.0 / num_cols
                col_widths = [col_width] * num_cols
                
                # If first column is short ID or Gate, distribute better
                if num_cols == 4:
                    col_widths = [110, 110, 160, 160]
                elif num_cols == 3:
                    col_widths = [140, 160, 240]
                elif num_cols == 2:
                    col_widths = [180, 360]
                elif num_cols == 5:
                    col_widths = [80, 100, 100, 130, 130]

                table_data = []
                # Header row
                header_cells = [Paragraph(format_inline_markdown(c), styles['SDTableHdr']) for c in norm_rows[0]]
                table_data.append(header_cells)
                
                for r in norm_rows[1:]:
                    row_cells = [Paragraph(format_inline_markdown(c), styles['SDTableCell']) for c in r]
                    table_data.append(row_cells)

                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), BG_TABLE_HDR),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]
                for row_idx in range(1, len(table_data)):
                    if row_idx % 2 == 0:
                        t_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), BG_TABLE_ALT))
                
                t.setStyle(TableStyle(t_style))
                flowables.append(Spacer(1, 4))
                flowables.append(t)
                flowables.append(Spacer(1, 5))
            table_raw_rows = []
        in_table = False

    def flush_quote():
        nonlocal in_quote, quote_lines
        if quote_lines:
            q_text = " ".join(quote_lines)
            # Detect alert type
            border_c = ACCENT_BLUE
            bg_c = BG_ALERT
            if '[!WARNING]' in q_text or '[!CAUTION]' in q_text:
                border_c = RED_ALERT
                bg_c = colors.HexColor('#fef2f2')
            elif '[!NOTE]' in q_text or '[!IMPORTANT]' in q_text:
                border_c = AMBER_WARNING
                bg_c = colors.HexColor('#fffbeb')
            
            clean_text = re.sub(r'\[!(NOTE|WARNING|IMPORTANT|CAUTION)\]', r'<b>[\1]</b>', q_text)
            p = Paragraph(format_inline_markdown(clean_text), styles['SDAlert'])
            t = Table([[p]], colWidths=[540])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_c),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('LINEBEFORE', (0, 0), (0, -1), 3.5, border_c),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            flowables.append(Spacer(1, 3))
            flowables.append(t)
            flowables.append(Spacer(1, 4))
            quote_lines = []
        in_quote = False

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        
        # 1. Code blocks
        if stripped.startswith('```'):
            if in_code_block:
                flush_code_block()
            else:
                if in_table: flush_table()
                if in_quote: flush_quote()
                in_code_block = True
                code_block_lines = []
            idx += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            idx += 1
            continue

        # 2. Blockquotes
        if stripped.startswith('>'):
            if in_table: flush_table()
            in_quote = True
            quote_content = stripped.lstrip('>').strip()
            quote_lines.append(quote_content)
            idx += 1
            continue
        elif in_quote:
            flush_quote()

        # 3. Tables
        if stripped.startswith('|') and '|' in stripped[1:]:
            # Check if separator row like | --- | --- |
            if re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', stripped):
                # skip separator row
                idx += 1
                continue
            in_table = True
            table_raw_rows.append(stripped)
            idx += 1
            continue
        elif in_table:
            flush_table()

        # 4. Empty lines
        if not stripped:
            idx += 1
            continue

        # 5. Horizontal rules
        if stripped in ['---', '***', '___']:
            flowables.append(HRFlowable(width="100%", thickness=0.8, color=BORDER_COLOR, spaceBefore=6, spaceAfter=6))
            idx += 1
            continue

        # 6. Headings
        if stripped.startswith('# '):
            flowables.append(Paragraph(format_inline_markdown(stripped[2:]), styles['SDTitle']))
            idx += 1
            continue
        elif stripped.startswith('## '):
            flowables.append(Paragraph(format_inline_markdown(stripped[3:]), styles['SDHeading1']))
            idx += 1
            continue
        elif stripped.startswith('### '):
            flowables.append(Paragraph(format_inline_markdown(stripped[4:]), styles['SDHeading2']))
            idx += 1
            continue
        elif stripped.startswith('#### '):
            flowables.append(Paragraph(format_inline_markdown(stripped[5:]), styles['SDHeading3']))
            idx += 1
            continue

        # 7. Bullet lists
        if re.match(r'^[\*\-]\s+', stripped):
            bullet_text = re.sub(r'^[\*\-]\s+', '', stripped)
            formatted_bullet = f"&bull; {format_inline_markdown(bullet_text)}"
            flowables.append(Paragraph(formatted_bullet, styles['SDBullet']))
            idx += 1
            continue

        # 8. Numbered lists
        if re.match(r'^\d+\.\s+', stripped):
            num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
            num_str = num_match.group(1)
            num_text = num_match.group(2)
            formatted_num = f"<b>{num_str}.</b> {format_inline_markdown(num_text)}"
            flowables.append(Paragraph(formatted_num, styles['SDBullet']))
            idx += 1
            continue

        # 9. Regular text paragraph
        flowables.append(Paragraph(format_inline_markdown(stripped), styles['SDBody']))
        idx += 1

    # Cleanup open states
    if in_code_block: flush_code_block()
    if in_table: flush_table()
    if in_quote: flush_quote()

    return flowables


def compile_markdown_to_pdf(md_path: str, pdf_path: str, title: str, subtitle: str):
    """Compiles a Markdown file to a styled multi-page PDF."""
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Custom Canvas with Title/Subtitle
    class CustomCanvas(SafeDigNumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, doc_title=title, doc_subtitle=subtitle, **kwargs)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=58,
        bottomMargin=46
    )

    styles = get_safedig_styles()
    story = parse_markdown_to_flowables(md_text, styles)
    
    doc.build(story, canvasmaker=CustomCanvas)
    print(f"[COMPILED PDF] {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
