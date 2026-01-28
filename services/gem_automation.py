# services/gem_automation.py
# =====================================================
# FINAL GEM AUTOMATION (DOWNLOAD ONLY)
#
# ✔ Manual CAPTCHA (mandatory)
# ✔ Browser triggers PDF download
# ✔ NO rename / NO move (handled by download_watcher.py)
# ✔ Playwright compatible (NO downloads_path)
# =====================================================

import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_automation(category: str):
    print("=" * 65)
    print("GEM AUTOMATION STARTED")
    print(f"Category: {category}")
    print("Download path: project /downloads folder")
    print("=" * 65)

    print("\nMANUAL STEPS REQUIRED:")
    print("1. Select category and date range")
    print("2. Solve CAPTCHA and click SEARCH")
    print("3. Open contract, solve CAPTCHA, submit")
    print("4. Click DOWNLOAD\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=200
        )

        # ✅ CORRECT CONTEXT (NO downloads_path)
        context = browser.new_context(
            accept_downloads=True
        )

        page = context.new_page()
        page.goto(GEM_URL, timeout=60000)

        input("Press ENTER once the contract list is visible...")

        while True:
            try:
                body_text = page.inner_text("body")

                if "Contract No" not in body_text:
                    print("Contract page not detected.")
                    input("Open a contract and press ENTER to continue...")
                    continue

                download_btn = page.locator("button:has-text('Download')")

                if download_btn.count() == 0:
                    print("Download button not found. Ensure CAPTCHA is submitted.")
                    input("Press ENTER to retry...")
                    continue

                print("Triggering PDF download...")

                with page.expect_download(timeout=120000):
                    download_btn.first.click(force=True)

                print("Download triggered successfully.")

                page.go_back()
                time.sleep(2)

                user_input = input(
                    "Open next contract | ENTER = continue | q = quit: "
                ).strip().lower()

                if user_input == "q":
                    break

            except PlaywrightTimeoutError:
                print("Download timed out.")
                input("Check page and CAPTCHA, then press ENTER...")
            except KeyboardInterrupt:
                print("\nAutomation stopped by user.")
                break
            except Exception as e:
                print("Unexpected error:", e)
                input("Press ENTER to retry...")

        context.close()
        browser.close()
        print("GEM automation completed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python services/gem_automation.py <Category>")
        sys.exit(1)

    run_gem_automation(sys.argv[1])
 