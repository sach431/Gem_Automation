# services/gem_automation.py
# =====================================================
# FINAL STABLE GEM PDF AUTOMATION
# - Direct browser download (GeM behaviour)
# - Manual captcha (mandatory)
# - Playwright expect_download (fixed)
# - Duplicate skip
# - Streamlit-safe (run via subprocess)
# =====================================================

import os
import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError

GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_automation(category: str):
    # -------------------------------------------------
    # BASE DIR (SAFE FOR STREAMLIT SUBPROCESS)
    # -------------------------------------------------
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(BASE_DIR, "downloads", category.lower(), "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    print("=" * 60)
    print("🚀 GEM AUTOMATION STARTED (DIRECT DOWNLOAD MODE)")
    print("Category :", category)
    print("Save Dir :", pdf_dir)
    print("=" * 60)

    print("\nMANUAL STEPS (ONLY ONCE):")
    print("1. Select category & date range")
    print("2. Fill captcha → SEARCH")
    print("3. Open first contract")
    print("4. Fill captcha → SUBMIT")
    print("⬇️ After this, automation will DOWNLOAD PDFs\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(GEM_URL, timeout=60000)

        input("👉 Contract page open ho jaye to ENTER dabao...")

        while True:
            try:
                # -----------------------------------------
                # READ CONTRACT NUMBER (SAFE)
                # -----------------------------------------
                body_text = page.inner_text("body")

                if "Contract No" not in body_text:
                    print("⚠️ Contract page properly open nahi hai.")
                    input("Contract open karo, phir ENTER dabao...")
                    continue

                contract_no = (
                    body_text.split("Contract No")[1]
                    .split("\n")[0]
                    .replace(":", "")
                    .strip()
                )

                if not contract_no:
                    print("⚠️ Contract number empty.")
                    input("ENTER dabao retry ke liye...")
                    continue

                pdf_name = f"{category}_{contract_no}.pdf"
                pdf_path = os.path.join(pdf_dir, pdf_name)

                if os.path.exists(pdf_path):
                    print(f"⏭️ Already downloaded: {pdf_name}")
                else:
                    print(f"⬇️ Downloading: {pdf_name}")

                    # -----------------------------------------
                    # STRONG DOWNLOAD BUTTON CLICK
                    # -----------------------------------------
                    download_btn = page.locator("button:has-text('Download')")

                    if download_btn.count() == 0:
                        print("❌ Download button not found.")
                        print("➡️ Captcha submit karo, phir try karo.")
                        input("ENTER dabao retry ke liye...")
                        continue

                    with page.expect_download(timeout=120000) as download_info:
                        download_btn.click(force=True)

                    download = download_info.value
                    download.save_as(pdf_path)

                    print(f"✅ PDF saved successfully: {pdf_name}")

                # -----------------------------------------
                # BACK TO LIST
                # -----------------------------------------
                page.go_back()
                time.sleep(2)

                print("\n👉 Next contract open karo (manual captcha)")
                user = input("ENTER dabao | q likho quit ke liye: ").lower()
                if user == "q":
                    break

            except TimeoutError:
                print("⏳ Download timeout.")
                input("Captcha / page check karo, phir ENTER dabao...")
            except KeyboardInterrupt:
                print("\n🛑 Automation stopped by user")
                break
            except Exception as e:
                print("⚠️ Error:", e)
                input("ENTER dabao retry ke liye...")

        browser.close()


# =====================================================
# RUN AS STANDALONE PROCESS (REQUIRED)
# =====================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m services.gem_automation <Category>")
        sys.exit(1)

    run_gem_automation(sys.argv[1])
