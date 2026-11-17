import json
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="
OUTPUT_JSON = "schemes_data.json"

def clean_text(text: str) -> str:
    """Normalize whitespace and non-breaking spaces."""
    return " ".join(text.replace("\xa0", " ").split()).strip()

def scrape_all_schemes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        print("Fetching scheme list...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("a[href*='scheme_details.php']")

        links = page.locator("a[href*='scheme_details.php']")
        scheme_urls = []
        for i in range(links.count()):
            title = clean_text(links.nth(i).inner_text())
            href = links.nth(i).get_attribute("href")
            if title and href:
                scheme_urls.append({
                    "list_title": title,
                    "url": urljoin(BASE_URL, href)
                })

        print(f"Total schemes queued: {len(scheme_urls)}\n")
        all_schemes_data = []

        for idx, item in enumerate(scheme_urls, start=1):
            print(f"[{idx}/{len(scheme_urls)}] Scraping: {item['list_title']}")
            try:
                page.goto(item["url"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_selector("table tr", timeout=15000)

                rows = page.locator("table tr")
                details = {}

                for r in range(rows.count()):
                    cells = rows.nth(r).locator("td, th")
                    cell_count = cells.count()

                    if cell_count >= 2:
                        key = clean_text(cells.nth(0).inner_text()).rstrip(":")
                        val = clean_text(cells.nth(1).inner_text())
                        if key:
                            details[key] = val if val else "N/A"

                all_schemes_data.append({
                    "index": idx,
                    "title": item["list_title"],
                    "url": item["url"],
                    "details": details
                })

                # Polite tiny delay so we don't hammer the government server
                time.sleep(0.3)

            except Exception as e:
                print(f"   [!] Error scraping {item['url']}: {e}")

        browser.close()

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_schemes_data, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved {len(all_schemes_data)} schemes to {OUTPUT_JSON}")

if __name__ == "__main__":
    scrape_all_schemes()