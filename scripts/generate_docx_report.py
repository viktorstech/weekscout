"""
generate_docx_report.py
Generates a clean, professional, academic Microsoft Word document (.docx)
from REPORT_4IT529.md for course 4IT529 Competitive Intelligence at VŠE Prague.
"""

import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell (in twips, 20 twips = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top="CCCCCC", bottom="CCCCCC", left=None, right=None, sz="4"):
    """Set custom borders on table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="{"single" if top else "none"}" w:sz="{sz}" w:space="0" w:color="{top or "auto"}"/>'
        f'<w:bottom w:val="{"single" if bottom else "none"}" w:sz="{sz}" w:space="0" w:color="{bottom or "auto"}"/>'
        f'<w:left w:val="{"single" if left else "none"}" w:sz="{sz}" w:space="0" w:color="{left or "auto"}"/>'
        f'<w:right w:val="{"single" if right else "none"}" w:sz="{sz}" w:space="0" w:color="{right or "auto"}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def add_header_footer(doc):
    """Add subtle academic header and page number footer."""
    section = doc.sections[0]
    
    # Header
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "4IT529 Competitive Intelligence | Projekt WeekScout (Tým 17)"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.style.font.name = "Calibri"
    hp.style.font.size = Pt(8.5)
    hp.style.font.color.rgb = RGBColor(128, 128, 128)
    
    # Footer
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = "Vysoká škola ekonomická v Praze • Fakulta informatiky a statistiky"
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fp.style.font.name = "Calibri"
    fp.style.font.size = Pt(8.5)
    fp.style.font.color.rgb = RGBColor(128, 128, 128)

def format_run_text(paragraph, text, base_font="Calibri", base_size=Pt(11), base_color=RGBColor(30, 30, 30), bold_prefix=False):
    """
    Parse inline bolding (**text**), italics (*text*), and code (`text`).
    """
    # Regex to split on bold (**...**) and italics (*...*)
    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run()
        run.font.name = base_font
        run.font.size = base_size
        run.font.color.rgb = base_color
        
        if part.startswith('**') and part.endswith('**'):
            run.text = part[2:-2]
            run.bold = True
        elif part.startswith('*') and part.endswith('*'):
            run.text = part[1:-1]
            run.italic = True
        elif part.startswith('`') and part.endswith('`'):
            run.text = part[1:-1]
            run.font.name = "Consolas"
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(180, 40, 40)
        else:
            run.text = part

def build_docx(md_path, output_path):
    doc = Document()
    
    # Page setup: Standard A4, 2.5 cm margins (approx 0.984 inches)
    section = doc.sections[0]
    section.page_width = Inches(8.27)   # A4 width
    section.page_height = Inches(11.69) # A4 height
    section.top_margin = Inches(0.98)
    section.bottom_margin = Inches(0.98)
    section.left_margin = Inches(0.98)
    section.right_margin = Inches(0.98)
    
    add_header_footer(doc)
    
    # Read markdown content
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    table_lines = []
    
    i = 0
    total_lines = len(lines)
    
    # Color palette - Classic Academic Navy
    NAVY_DARK = RGBColor(15, 45, 95)
    NAVY_MID = RGBColor(30, 70, 130)
    TEXT_COLOR = RGBColor(40, 40, 40)
    MUTED_COLOR = RGBColor(90, 90, 90)
    
    while i < total_lines:
        line = lines[i].strip()
        
        # Check if table block
        if line.startswith("|") and line.endswith("|"):
            table_lines.append(line)
            i += 1
            # collect all table lines
            while i < total_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            
            # Process table
            render_table(doc, table_lines, NAVY_DARK, TEXT_COLOR)
            table_lines = []
            continue
            
        # Empty line
        if not line:
            i += 1
            continue
            
        # Title (Line 1)
        if line.startswith("# "):
            title_text = line[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(title_text)
            run.font.name = "Calibri"
            run.font.size = Pt(22)
            run.bold = True
            run.font.color.rgb = NAVY_DARK
            i += 1
            continue
            
        # Subtitle / Header metadata block (Předmět, Instituce, Autoři, etc.)
        if line.startswith("**Předmět:**") or line.startswith("**Instituce:**") or line.startswith("**Autoři:**") or line.startswith("**Datum odevzdání:**") or line.startswith("**Odkazy na živý prototyp:**"):
            # Gather metadata block
            meta_lines = [line]
            i += 1
            while i < total_lines and (lines[i].strip().startswith("* ") or lines[i].strip().startswith("**") or lines[i].strip() == ""):
                if lines[i].strip() == "---":
                    break
                if lines[i].strip():
                    meta_lines.append(lines[i].strip())
                i += 1
            
            render_metadata_box(doc, meta_lines)
            continue
            
        if line == "---":
            # Horizontal divider - represented by spacing
            i += 1
            continue
            
        # Heading 1 (##)
        if line.startswith("## "):
            h1_text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h1_text)
            run.font.name = "Calibri"
            run.font.size = Pt(15)
            run.bold = True
            run.font.color.rgb = NAVY_DARK
            i += 1
            continue
            
        # Heading 2 (###)
        if line.startswith("### "):
            h2_text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h2_text)
            run.font.name = "Calibri"
            run.font.size = Pt(12.5)
            run.bold = True
            run.font.color.rgb = NAVY_MID
            i += 1
            continue
            
        # Bullet list item (* ...)
        if line.startswith("* "):
            bullet_text = line[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            format_run_text(p, bullet_text, base_size=Pt(10.5), base_color=TEXT_COLOR)
            i += 1
            continue
            
        # Numbered list item (1. ..., 2. ...)
        m_num = re.match(r'^(\d+)\.\s+(.*)$', line)
        if m_num:
            num = m_num.group(1)
            item_text = m_num.group(2).strip()
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            format_run_text(p, item_text, base_size=Pt(10.5), base_color=TEXT_COLOR)
            i += 1
            continue
            
        # Regular paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        format_run_text(p, line, base_size=Pt(11), base_color=TEXT_COLOR)
        i += 1
        
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

def render_metadata_box(doc, meta_lines):
    """Render a structured, clean header box with metadata."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F6F9")
    set_cell_margins(cell, top=160, bottom=160, left=240, right=240)
    set_cell_borders(cell, top="CBD5E1", bottom="CBD5E1", left="1E4682", right="CBD5E1", sz="12")
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    
    for idx, l in enumerate(meta_lines):
        if idx > 0:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.2
            
        format_run_text(p, l, base_size=Pt(10), base_color=RGBColor(50, 50, 50))
        
    # Spacer paragraph after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(8)

def render_table(doc, table_lines, navy_dark, text_color):
    """Render markdown table into a beautifully formatted Word table."""
    # Filter out separator row (e.g. | :--- | :--- |)
    rows_data = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip('|').split('|')]
        # check if separator
        if all(re.match(r'^:?-+:?$', c) for c in cells):
            continue
        rows_data.append(cells)
        
    if not rows_data:
        return
        
    num_rows = len(rows_data)
    num_cols = len(rows_data[0])
    
    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Calculate widths based on columns count
    col_widths = []
    if num_cols == 5:
        # Srovnávací matice
        col_widths = [Inches(1.5), Inches(1.8), Inches(0.9), Inches(1.1), Inches(1.7)]
    elif num_cols == 3:
        # CI cyklus
        col_widths = [Inches(1.4), Inches(1.6), Inches(3.8)]
    else:
        # evenly split
        total_w = Inches(6.8)
        w_each = total_w / num_cols
        col_widths = [w_each] * num_cols

    for r_idx, row_cells in enumerate(rows_data):
        row = table.rows[r_idx]
        is_header = (r_idx == 0)
        
        # Prevent row split across pages
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if is_header:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            
        for c_idx, cell_value in enumerate(row_cells):
            if c_idx >= num_cols:
                continue
            cell = row.cells[c_idx]
            if c_idx < len(col_widths):
                cell.width = col_widths[c_idx]
                
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
            
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.1
            
            if is_header:
                set_cell_background(cell, "1E3A8A") # Dark Navy Header
                set_cell_borders(cell, top="1E3A8A", bottom="1E3A8A", left="2E4A9A", right="2E4A9A", sz="4")
                format_run_text(p, cell_value, base_size=Pt(9.5), base_color=RGBColor(255, 255, 255))
                # ensure bold
                for run in p.runs:
                    run.bold = True
            else:
                bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
                set_cell_background(cell, bg_color)
                set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz="4")
                format_run_text(p, cell_value, base_size=Pt(9.5), base_color=text_color)
                
    # Spacing after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_file = os.path.join(base_dir, "REPORT_4IT529.md")
    output_docx = os.path.join(base_dir, "WeekScout_report_4IT529.docx")
    build_docx(md_file, output_docx)
