from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

def inspect_detail_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)

        # Target specifically links pointing to scheme_details.php
        links = page.locator("a[href*='scheme_details.php']")
        count = links.count()
        print(f"Found {count} scheme detail links.\n")

        schemes = []
        for i in range(count):
            title = links.nth(i).inner_text().strip()
            href = links.nth(i).get_attribute("href")
            full_url = urljoin(BASE_URL, href)
            if title:
                schemes.append({"title": title, "url": full_url})

        # Visit the FIRST scheme detail page to see its HTML structure
        first_scheme = schemes[0]
        print(f"Inspecting: {first_scheme['title']}")
        print(f"URL: {first_scheme['url']}\n")

        page.goto(first_scheme["url"], wait_until="networkidle", timeout=60000)

        # Check if details are inside a table, definition list, or specific container
        tables = page.locator("table")
        print(f"Tables on detail page: {tables.count()}")
        for i in range(tables.count()):
            print(f"\n--- Table {i} Text ---")
            print(tables.nth(i).inner_text()[:1000])

        # Also check main content containers just in case it uses divs/cards instead of tables
        if tables.count() == 0:
            main_text = page.locator("main, .container, #content, body").first.inner_text()
            print("\n--- Page Text Sample ---")
            print(main_text[:1500])

        browser.close()

if __name__ == "__main__":
    inspect_detail_page()