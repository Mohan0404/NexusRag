from playwright.sync_api import sync_playwright
import fitz

html = """<!DOCTYPE html>
<html>
<head>
<style>
@page {
  size: A4 portrait;
  margin: 16mm 14mm 16mm 14mm;
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 8pt;
    font-family: sans-serif;
  }
}
body { margin: 0; }
.p1 { height: 100vh; page-break-after: always; }
.p2 { height: 100vh; }
</style>
</head>
<body>
<div class="p1"><h1>Page 1</h1></div>
<div class="p2"><h1>Page 2</h1></div>
</body>
</html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(html)
    pg.emulate_media(media='print')
    pg.pdf(path='test_pages.pdf', format='A4', print_background=True, display_header_footer=False, prefer_css_page_size=True)
    b.close()

doc = fitz.open('test_pages.pdf')
for i, page in enumerate(doc):
    print(f"--- Page {i+1} text ---")
    print(repr(page.get_text()))
doc.close()
