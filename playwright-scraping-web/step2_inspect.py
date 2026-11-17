from playwright.sync_api import sync_playwright

URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

def inspect_structure():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # 1. Check for tables
        tables = page.locator("table")
        print(f"Total tables found: {tables.count()}")
        for i in range(tables.count()):
            headers = tables.nth(i).locator("th").all_inner_texts()
            rows = tables.nth(i).locator("tbody tr").count()
            print(f"  Table {i}: Headers={headers} | Body Rows={rows}")
            if rows > 0:
                first_row_cells = tables.nth(i).locator("tbody tr").first.locator("td").all_inner_texts()
                print(f"  Sample Row 1: {first_row_cells}")

        # 2. Check for scheme-related links (e.g., scheme_details.php or similar)
        scheme_links = page.locator("a[href*='scheme']")
        print(f"\nLinks containing 'scheme': {scheme_links.count()}")
        for i in range(min(5, scheme_links.count())):
            text = scheme_links.nth(i).inner_text().strip()
            href = scheme_links.nth(i).get_attribute("href")
            print(f"  Link {i}: '{text}' -> {href}")

        # 3. Check if pagination or DataTables controls exist
        pagination = page.locator(".pagination, .dataTables_paginate, select[name*='length']")
        print(f"\nPagination/Filter elements found: {pagination.count()}")

        browser.close()

if __name__ == "__main__":
    inspect_structure()