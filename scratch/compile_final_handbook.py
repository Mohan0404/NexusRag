"""
Master Orchestration Script to Compile NexusRAG Interview Preparation Handbook.
Renders HTML, generates PDF via Playwright, and performs Visual QA with PyMuPDF.
"""
import os
import sys
import shutil
import time

# Ensure scratch directory is in python path
sys.path.insert(0, r"D:\Academic-Projects\RAG\scratch")

import build_full_handbook as base_builder
import sections_part1 as p1
import sections_part2 as p2
import sections_part3 as p3
import sections_part4 as p4
import sections_part5 as p5
import sections_part6 as p6
import sections_part7 as p7
import sections_part8 as p8

DOCS_DIR = r"D:\Academic-Projects\RAG\docs\interview"
NEXUS_DIR = r"D:\Academic-Projects\RAG\NexusRag\docs\interview"
MD_SOURCE = os.path.join(NEXUS_DIR, "GENWORX_RAG_INTERVIEW_PREPARATION.md")
CSS_PATH = os.path.join(DOCS_DIR, "assets", "css", "handbook.css")

def compile_master_html():
    print("=== Step 1: Loading Source Files ===")
    md_text = base_builder.load_file(MD_SOURCE)
    css_text = base_builder.load_file(CSS_PATH)

    print("=== Step 2: Generating Handbook Parts ===")
    cover_html = base_builder.build_cover_page()
    toc_html = base_builder.build_toc()
    part1_html = p1.generate_part_1(base_builder)
    part2_html = p2.generate_part_2(base_builder)
    part3_html = p3.generate_part_3(base_builder)
    part4_html = p4.generate_part_4(base_builder)
    part5_html = p5.generate_part_5(base_builder)
    part6_html = p6.generate_part_6(base_builder)
    part7_html = p7.generate_part_7(base_builder)
    part8_html = p8.generate_part_8(base_builder, md_text)

    master_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NexusRAG — Genworx Knowledge Assistant Interview Preparation Handbook</title>
  <meta name="description" content="AI-Powered RAG Knowledge Assistant Technical Architecture & Senior Interview Preparation Defense Handbook">
  <meta name="author" content="Mohan / Genworx AI Engineering">
  <style>
    {css_text}
  </style>
</head>
<body>
  <div class="handbook-container">
    {cover_html}
    {toc_html}
    {part1_html}
    {part2_html}
    {part3_html}
    {part4_html}
    {part5_html}
    {part6_html}
    {part7_html}
    {part8_html}
  </div>
</body>
</html>
"""

    out_html_1 = os.path.join(DOCS_DIR, "NexusRAG_Interview_Preparation_Handbook.html")
    out_html_2 = os.path.join(NEXUS_DIR, "NexusRAG_Interview_Preparation_Handbook.html")

    with open(out_html_1, "w", encoding="utf-8") as f:
        f.write(master_html)
    with open(out_html_2, "w", encoding="utf-8") as f:
        f.write(master_html)

    print(f"Master HTML generated: {len(master_html):,} characters.")
    print(f"Saved to: {out_html_1}")
    print(f"Saved to: {out_html_2}")
    return out_html_1

def render_pdf_with_playwright(html_path):
    print("\n=== Step 3: Rendering PDF via Playwright Chromium ===")
    from playwright.sync_api import sync_playwright

    out_pdf_1 = os.path.join(DOCS_DIR, "NexusRAG_Interview_Preparation_Handbook.pdf")
    out_pdf_2 = os.path.join(NEXUS_DIR, "NexusRAG_Interview_Preparation_Handbook.pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-gpu", "--no-sandbox"])
        page = browser.new_page()

        # Convert local path to file URL
        file_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
        print(f"Loading {file_url}...")
        page.goto(file_url, wait_until="networkidle", timeout=90000)

        # Emulate print media
        page.emulate_media(media="print")
        time.sleep(2)  # Allow SVG and styles to settle

        print("Generating PDF via Chromium CSS Paged Media engine...")
        page.pdf(
            path=out_pdf_1,
            format="A4",
            print_background=True,
            display_header_footer=False,
            prefer_css_page_size=True
        )
        browser.close()

    shutil.copyfile(out_pdf_1, out_pdf_2)
    pdf_size = os.path.getsize(out_pdf_1)
    print(f"PDF successfully rendered: {pdf_size:,} bytes.")
    print(f"Saved to: {out_pdf_1}")
    print(f"Saved to: {out_pdf_2}")
    return out_pdf_1

def visual_qa_inspection(pdf_path):
    print("\n=== Step 4: Visual QA Inspection with PyMuPDF ===")
    import fitz

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total Pages in PDF: {total_pages}")

    qa_dir = r"D:\Academic-Projects\RAG\scratch\visual_qa_pages"
    os.makedirs(qa_dir, exist_ok=True)

    # Sample pages to inspect: Cover, TOC, early diagram, mid section, question bank, end cheat sheet
    sample_indices = [
        0,                                # Cover (Page 1)
        1,                                # Table of Contents (Page 2)
        min(4, total_pages - 1),          # Part I / Flows
        min(10, total_pages - 1),         # Master Architecture (Figure A)
        min(18, total_pages - 1),         # Ingestion Pipeline (Figure B)
        min(28, total_pages - 1),         # Query RAG Flow (Figure C)
        min(45, total_pages - 1),         # Safe Replacement (Figure G)
        min(58, total_pages - 1),         # Failure Matrix
        min(75, total_pages - 1),         # Interview Q&A
        min(total_pages - 2, total_pages - 1), # Rapid-Fire Cheat Sheet
        total_pages - 1                   # Final Readiness Checklist
    ]
    sample_indices = sorted(list(set(sample_indices)))

    rendered_images = []
    for idx in sample_indices:
        page = doc[idx]
        pix = page.get_pixmap(dpi=150)
        img_path = os.path.join(qa_dir, f"page_{idx+1}.png")
        pix.save(img_path)
        rendered_images.append(img_path)
        print(f"Rendered Page {idx+1}/{total_pages} -> {img_path} ({pix.width}x{pix.height})")

    doc.close()
    return total_pages, rendered_images

if __name__ == "__main__":
    html_path = compile_master_html()
    pdf_path = render_pdf_with_playwright(html_path)
    total_pages, qa_images = visual_qa_inspection(pdf_path)
    print("\n==========================================")
    print("HANDBOOK GENERATION & VISUAL QA COMPLETE")
    print(f"Total Pages: {total_pages}")
    print(f"PDF Output: {pdf_path}")
    print(f"QA Images: {len(qa_images)} pages rendered")
    print("==========================================")
