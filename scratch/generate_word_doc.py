import re
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets inner padding for a table cell in twentieths of a point (dxa)."""
    tc_pr = cell._element.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)

def set_table_borders(table, color="CBD5E1", sz="4"):
    """Applies clean subtle borders to a table."""
    tbl_pr = table._element.xpath('w:tblPr')
    if tbl_pr:
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:insideV w:val="none"/>'
            f'<w:left w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'</w:tblBorders>'
        )
        tbl_pr[0].append(borders)

def add_header_footer(doc):
    """Configures running header and page numbering footer."""
    section = doc.sections[0]
    
    # Running Header
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run("NexusRAG — Technical Interview Preparation & System Design Guide")
    hrun.font.name = "Calibri"
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = RGBColor(148, 163, 184) # #94A3B8
    
    # Running Footer
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    frun = fp.add_run("Genworx Knowledge Assistant   |   Page ")
    frun.font.name = "Calibri"
    frun.font.size = Pt(9)
    frun.font.color.rgb = RGBColor(148, 163, 184)
    
    # Add page number field
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    fp._p.append(fldSimple)

def parse_inline_formatting(paragraph, text, default_color=None, base_font_size=11, is_code=False):
    """Parses markdown inline bold, italic, code, and LaTeX math into Word runs."""
    if not text:
        return

    # Clean simple math notations for Word readability: $L_2^2$ -> L2^2, $\le$ -> <=, etc.
    text = text.replace(r"$\le", "<=").replace(r"\le", "<=").replace(r"$\approx", "~").replace(r"\approx", "~")
    text = text.replace(r"$\mathbb{R}^D$", "R^D").replace(r"$L_2^2$", "L2^2").replace(r"$\mathbf{u}", "u").replace(r"\mathbf{v}", "v")
    text = text.replace(r"\text{ MB}", " MB").replace(r"\text{ms}", "ms").replace(r"\text{s}", "s")
    text = re.sub(r"\$([^\$]+)\$", r"\1", text) # Remove remaining single dollar math markers

    # Tokenize by: inline code `...`, bold **...**, italic *...*
    token_pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)")
    parts = token_pattern.split(text)

    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            code_text = part[1:-1]
            run = paragraph.add_run(code_text)
            run.font.name = "Consolas"
            run.font.size = Pt(base_font_size - 1)
            run.font.color.rgb = RGBColor(79, 70, 229) # Indigo #4F46E5
            # Shaded background for inline code
            rPr = run._r.get_or_add_rPr()
            rPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>'))
        elif part.startswith("**") and part.endswith("**") and len(part) >= 4:
            bold_text = part[2:-2]
            run = paragraph.add_run(bold_text)
            run.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(base_font_size)
            if default_color:
                run.font.color.rgb = default_color
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            italic_text = part[1:-1]
            run = paragraph.add_run(italic_text)
            run.italic = True
            run.font.name = "Calibri"
            run.font.size = Pt(base_font_size)
            if default_color:
                run.font.color.rgb = default_color
        else:
            run = paragraph.add_run(part)
            run.font.name = "Consolas" if is_code else "Calibri"
            run.font.size = Pt(base_font_size)
            if default_color:
                run.font.color.rgb = default_color

def build_docx_from_markdown(md_path: Path, output_path: Path):
    doc = Document()
    
    # Page setup - 1 inch margins
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        
    add_header_footer(doc)
    
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_lang = ""
    code_lines = []
    
    in_table = False
    table_rows = []
    
    in_blockquote = False
    blockquote_lines = []
    
    def flush_blockquote():
        nonlocal in_blockquote, blockquote_lines
        if not blockquote_lines:
            return
        full_text = " ".join([l.strip() for l in blockquote_lines])
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.right_indent = Inches(0.4)
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(10)
        
        # Add a left border via XML
        pPr = p._element.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'<w:left w:val="single" w:sz="24" w:space="15" w:color="4F46E5"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="EEF2FF"/>')
        pPr.append(shd)
        
        parse_inline_formatting(p, full_text, default_color=RGBColor(49, 46, 129), base_font_size=10.5)
        blockquote_lines = []
        in_blockquote = False

    def flush_code_block():
        nonlocal in_code_block, code_lines, code_lang
        if not code_lines:
            in_code_block = False
            return
        code_text = "".join(code_lines).rstrip()
        
        # We render code block inside a 1x1 table with gray background and light border
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        
        # Border
        tc_pr = cell._element.get_or_add_tcPr()
        tc_bdr = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
            f'<w:left w:val="single" w:sz="18" w:space="0" w:color="6366F1"/>'
            f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
            f'<w:right w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
            f'</w:tcBorders>'
        )
        tc_pr.append(tc_bdr)
        
        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(2)
        cp.paragraph_format.space_after = Pt(2)
        cp.paragraph_format.line_spacing = 1.05
        
        run = cp.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(9.0)
        run.font.color.rgb = RGBColor(15, 23, 42)
        
        # Add spacing after table
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)
        
        code_lines = []
        code_lang = ""
        in_code_block = False

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
            
        # Parse table cells
        parsed_rows = []
        for r in table_rows:
            cells = [c.strip() for c in r.strip().strip('|').split('|')]
            # Check if separator row (e.g. |---|---|)
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            parsed_rows.append(cells)
            
        if not parsed_rows:
            in_table = False
            table_rows = []
            return
            
        num_cols = max(len(r) for r in parsed_rows)
        table = doc.add_table(rows=len(parsed_rows), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        set_table_borders(table, color="CBD5E1", sz="4")
        
        for row_idx, row_data in enumerate(parsed_rows):
            is_header = (row_idx == 0)
            row = table.rows[row_idx]
            
            # CantSplit and tblHeader for header
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            if is_header:
                trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                
            for col_idx in range(num_cols):
                cell = row.cells[col_idx]
                cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                
                # Cell padding
                set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
                
                # Shading
                if is_header:
                    set_cell_background(cell, "4F46E5") # Indigo
                else:
                    if row_idx % 2 == 0:
                        set_cell_background(cell, "F8FAFC") # Soft zebra
                    else:
                        set_cell_background(cell, "FFFFFF")
                        
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.05
                
                if is_header:
                    run = p.add_run(cell_text)
                    run.bold = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(9.5)
                    run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    parse_inline_formatting(p, cell_text, default_color=RGBColor(30, 41, 59), base_font_size=9.5)
                    
        # Spacing after table
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)
        
        table_rows = []
        in_table = False

    i = 0
    total_lines = len(lines)
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # 1. Code Block Delimiter
        if stripped.startswith("```"):
            if in_code_block:
                flush_code_block()
            else:
                if in_blockquote:
                    flush_blockquote()
                if in_table:
                    flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            i += 1
            continue
            
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
            
        # 2. Blockquote
        if stripped.startswith(">"):
            if in_table:
                flush_table()
            in_blockquote = True
            bq_content = stripped.lstrip(">").strip()
            blockquote_lines.append(bq_content)
            i += 1
            continue
        elif in_blockquote and stripped:
            blockquote_lines.append(stripped)
            i += 1
            continue
        elif in_blockquote and not stripped:
            flush_blockquote()
            i += 1
            continue
            
        # 3. Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            flush_table()
            
        # 4. Horizontal Rule
        if stripped in ("---", "***", "___"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            pPr = p._element.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'<w:bottom w:val="single" w:sz="6" w:space="1" w:color="E2E8F0"/>'
                f'</w:pBdr>'
            )
            pPr.append(pBdr)
            i += 1
            continue
            
        # 5. Headings
        if stripped.startswith("#"):
            match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                
                if level == 1:
                    # Document Title
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(12)
                    h.paragraph_format.space_after = Pt(4)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(heading_text)
                    run.bold = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(22)
                    run.font.color.rgb = RGBColor(79, 70, 229) # Indigo #4F46E5
                elif level == 2:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(16)
                    h.paragraph_format.space_after = Pt(4)
                    h.paragraph_format.keep_with_next = True
                    
                    # Top border accent for H2
                    pPr = h._element.get_or_add_pPr()
                    pBdr = parse_xml(
                        f'<w:pBdr {nsdecls("w")}>'
                        f'<w:bottom w:val="single" w:sz="8" w:space="4" w:color="E2E8F0"/>'
                        f'</w:pBdr>'
                    )
                    pPr.append(pBdr)
                    
                    run = h.add_run(heading_text)
                    run.bold = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(15)
                    run.font.color.rgb = RGBColor(30, 41, 59) # Slate #1E293B
                elif level == 3:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(12)
                    h.paragraph_format.space_after = Pt(3)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(heading_text)
                    run.bold = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(12.5)
                    run.font.color.rgb = RGBColor(51, 65, 85) # Slate #334155
                else:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(8)
                    h.paragraph_format.space_after = Pt(2)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(heading_text)
                    run.bold = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
                    run.font.color.rgb = RGBColor(71, 85, 105)
                    
                i += 1
                continue
                
        # 6. List items (bullets or numbers)
        bullet_match = re.match(r"^(\s*)[-*+]\s+(.*)$", stripped)
        num_match = re.match(r"^(\s*)\d+\.\s+(.*)$", stripped)
        
        if bullet_match:
            content = bullet_match.group(2)
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, content, default_color=RGBColor(30, 41, 59), base_font_size=10.5)
            i += 1
            continue
            
        if num_match:
            content = num_match.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, content, default_color=RGBColor(30, 41, 59), base_font_size=10.5)
            i += 1
            continue
            
        # 7. Standard Paragraph
        if stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, stripped, default_color=RGBColor(30, 41, 59), base_font_size=10.5)
            
        i += 1

    # Cleanup trailing elements
    if in_code_block:
        flush_code_block()
    if in_blockquote:
        flush_blockquote()
    if in_table:
        flush_table()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Successfully created: {output_path}")

if __name__ == "__main__":
    src_md = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"d:\Academic-Projects\RAG\NexusRag\docs\interview\GENWORX_RAG_INTERVIEW_PREPARATION.md")
    dest_docx = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(r"d:\Academic-Projects\RAG\NexusRag\docs\interview\GENWORX_RAG_INTERVIEW_PREPARATION.docx")
    build_docx_from_markdown(src_md, dest_docx)
