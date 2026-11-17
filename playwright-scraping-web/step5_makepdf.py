import html
import json
from playwright.sync_api import sync_playwright

INPUT_JSON = "schemes_data.json"
OUTPUT_PDF = "TN_Agriculture_Schemes.pdf"

def build_html(schemes: list) -> str:
    cards_html = []

    for scheme in schemes:
        idx = scheme.get("index", "")
        title = html.escape(scheme.get("title", "Untitled Scheme"))
        url = html.escape(scheme.get("url", ""))
        details = scheme.get("details", {})

        rows_html = []
        for key, value in details.items():
            # Skip empty or N/A fields if you only want populated details, 
            # or keep them if you want every row shown:
            if value and value != "N/A":
                safe_key = html.escape(key)
                safe_val = html.escape(value)
                rows_html.append(f"""
                    <tr>
                        <th>{safe_key}</th>
                        <td>{safe_val}</td>
                    </tr>
                """)

        table_body = "\n".join(rows_html) if rows_html else "<tr><td colspan='2'>No details available</td></tr>"

        cards_html.append(f"""
        <div class="scheme-card">
            <div class="scheme-header">
                <span class="badge">#{idx}</span>
                <h2>{title}</h2>
            </div>
            <table>
                <tbody>
                    {table_body}
                </tbody>
            </table>
            <div class="source-link">Source: <a href="{url}">{url}</a></div>
        </div>
        """)

    all_cards = "\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: A4;
        margin: 18mm 14mm 18mm 14mm;
    }}
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #1f2937;
        line-height: 1.45;
        font-size: 10.5pt;
    }}
    .doc-title {{
        text-align: center;
        border-bottom: 2px solid #0f5132;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }}
    .doc-title h1 {{
        margin: 0;
        color: #0f5132;
        font-size: 18pt;
    }}
    .doc-title p {{
        margin: 4px 0 0;
        color: #4b5563;
        font-size: 10pt;
    }}
    .scheme-card {{
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 18px;
        background-color: #ffffff;
        page-break-inside: avoid; /* Keeps each scheme together on one page when possible */
    }}
    .scheme-header {{
        display: flex;
        align-items: baseline;
        gap: 8px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }}
    .badge {{
        background-color: #0f5132;
        color: #ffffff;
        font-weight: bold;
        font-size: 9pt;
        padding: 2px 7px;
        border-radius: 4px;
    }}
    .scheme-header h2 {{
        margin: 0;
        font-size: 12pt;
        color: #111827;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    th, td {{
        text-align: left;
        vertical-align: top;
        padding: 5px 8px;
        border-bottom: 1px solid #f3f4f6;
        font-size: 9.5pt;
    }}
    th {{
        width: 28%;
        color: #374151;
        font-weight: 600;
        background-color: #f9fafb;
    }}
    td {{
        width: 72%;
        color: #1f2937;
    }}
    .source-link {{
        margin-top: 8px;
        font-size: 8pt;
        color: #6b7280;
    }}
    .source-link a {{
        color: #0f5132;
        text-decoration: none;
    }}
</style>
</head>
<body>
    <div class="doc-title">
        <h1>Government of Tamil Nadu — Department Schemes</h1>
        <p>Total Schemes Extracted: {len(schemes)}</p>
    </div>
    {all_cards}
</body>
</html>
"""

def generate_pdf():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    print(f"Loaded {len(schemes)} schemes from {INPUT_JSON}...")
    html_content = build_html(schemes)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="load")

        page.pdf(
            path=OUTPUT_PDF,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template="""
                <div style="font-size: 8pt; color: #6b7280; width: 100%; text-align: center; font-family: Arial, sans-serif;">
                    Page <span class="pageNumber"></span> of <span class="totalPages"></span>
                </div>
            """,
            margin={"top": "18mm", "bottom": "18mm", "left": "14mm", "right": "14mm"}
        )
        browser.close()

    print(f"Successfully generated {OUTPUT_PDF}!")

if __name__ == "__main__":
    generate_pdf()