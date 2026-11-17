from playwright.sync_api import sync_playwright

URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

def test_connection():
    with sync_playwright() as p:
        # headless=False lets you visually watch what the browser is doing
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True  # Helpful for Indian govt portals with occasional SSL chain quirks
        )
        page = context.new_page()
        
        print("Navigating to page...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        
        print("Page Title:", page.title())
        
        # Keep browser open for 5 seconds so you can inspect the layout visually
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    test_connection()