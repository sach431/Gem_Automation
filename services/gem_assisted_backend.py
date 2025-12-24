import os
import time
from playwright.sync_api import sync_playwright

GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_assisted(category: str, pdf_dir: str, stop_file: str):

    pdf_dir = os.path.abspath(pdf_dir)
    stop_file = os.path.abspath(stop_file)

    os.makedirs(pdf_dir, exist_ok=True)

    print("=" * 60)
    print("🚀 GeM Assisted Automation Started")
    print("📂 Category :", category)
    print("📂 PDF Dir  :", pdf_dir)
    print("🛑 Stop File:", stop_file)
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        context = browser.new_context(accept_downloads=True)

        page = context.new_page()
        page.goto(GEM_URL, timeout=60000)

        print("🌐 Browser opened → waiting for user actions")

        page.evaluate(
            "alert('Captcha bharo → Contract open karo → Submit / Download karo')"
        )

        # ✅ FIX: LISTEN AT CONTEXT LEVEL (ALL TABS / POPUPS)
        def handle_download(download):
            try:
                filename = download.suggested_filename
                save_path = os.path.join(pdf_dir, filename)
                download.save_as(save_path)
                print("⬇️ PDF Downloaded:", filename)
            except Exception as e:
                print("❌ Download error:", e)

        context.on("download", handle_download)

        # 🔁 STOP LOOP
        try:
            while True:
                if os.path.exists(stop_file):
                    print("🛑 Stop signal detected")
                    break
                time.sleep(1)
        finally:
            context.close()
            browser.close()
            print("✅ Browser closed safely")
