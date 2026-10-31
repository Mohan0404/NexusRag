from playwright.sync_api import sync_playwright
import fitz

html = """<!DOCTYPE html>
<html>
<head>
<style>
@page {
  size: A4 portrait;
  margin: 16mm 14mm 16mm 14mm;
  @top-left {
    content: "NexusRAG — Genworx Knowledge Assistant";
    font-size: 8pt;
    font-family: sans-serif;
    color: #94A3B8;
  }
  @top-right {
    content: "Project Defense Handbook";
    font-size: 8pt;
    font-family: sans-serif;
    color: #94A3B8;
  }
  @bottom-left {
    content: "Confidential · Senior AI Engineering Interview Preparation";
    font-size: 7.5pt;
    font-family: sans-serif;
    color: #94A3B8;
  }
  @bottom-right {
    content: "Page " counter(page);
    font-size: 8pt;
    font-family: sans-serif;
    font-weight: 600;
    color: #64748B;
  }
}

@page :first {
  margin: 0;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

body { margin: 0; font-family: sans-serif; }
.cover { height: 100vh; padding: 20mm; background: #EEF2FF; box-sizing: border-box; page-break-after: always; }
.page2 { padding: 10mm; }
</style>
</head>
<body>
<div class="cover"><h1>Cover Page</h1></div>
<div class="page2"><h1>Page 2 Content</h1></div>
</body>
</html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(html)
    pg.emulate_media(media='print')
    pg.pdf(path='test_css_page2.pdf', format='A4', print_background=True, display_header_footer=False, prefer_css_page_size=True)
    b.close()

doc = fitz.open('test_css_page2.pdf')
print('Page count:', len(doc))
for i, page in enumerate(doc):
    print(f"--- Page {i+1} text ---")
    print(repr(page.get_text()))
doc.close()
