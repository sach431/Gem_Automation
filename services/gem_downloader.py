# services/gem_downloader.py
# =====================================================
# FINAL GEM DOWNLOADER (NO __init__.py REQUIRED)
#
# ✔ Manual CAPTCHA
# ✔ Browser handles download
# ✔ System Downloads watcher
# ✔ Rename + move after detect
# =====================================================

import os
import sys
import time
from playwright.sync_api import sync_playwright

# =====================================================
# PATH FIX (REQUIRED WHEN NO __init__.py)
# =====================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =====================================================
# RELATIVE IMPORTS (FINAL FIX)
# =====================================================
from .download_watcher import wait_for_pdf_download
from .file_store import move_and_rename_pdf

# =====================================================
GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_downloader(category="default"):
    print("=" * 60)
    print("🚀 GEM DOWNLOADER STARTED (FINAL)")
    print("Category:", category)
    print("=" * 60)

    print("\n🛑 MANUAL STEPS (MANDATORY)")
    print("1. Select category")
    print("2. Select date / quarter")
    print("3. Solve CAPTCHA → SEARCH")
    print("4. Open contract → Solve CAPTCHA → SUBMIT")
    print("⬇️ Download auto-detect hoga\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(GEM_URL, timeout=60000)
        input("👉 Contract page open ho jaye to ENTER dabao...")

        while True:
            try:
                body_text = page.inner_text("body")

                if "Contract No" not in body_text:
                    input("⚠️ Contract open nahi hai. ENTER dabao...")
                    continue

                contract_no = (
                    body_text.split("Contract No")[1]
                    .split("\n")[0]
                    .replace(":", "")
                    .strip()
                )

                print(f"\n📄 Contract: {contract_no}")

                download_btn = page.locator("button:has-text('Download')")
                if download_btn.count() == 0:
                    input("❌ Download button nahi mila. CAPTCHA submit karke ENTER dabao...")
                    continue

                # CLICK ONLY
                download_btn.first.click(force=True)
                print("⬇️ Download clicked")

                # WATCH SYSTEM DOWNLOADS
                downloaded_pdf = wait_for_pdf_download()

                if downloaded_pdf:
                    final_path = move_and_rename_pdf(
                        src_pdf_path=downloaded_pdf,
                        category=category,
                        contract_no=contract_no
                    )
                    print(f"✅ Saved → {final_path}")
                else:
                    print("❌ Download detect nahi hua")

                page.go_back()
                time.sleep(2)

                user = input("ENTER = next | q = quit : ").lower()
                if user == "q":
                    break

            except KeyboardInterrupt:
                print("\n🛑 User stopped")
                break
            except Exception as e:
                print("⚠️ Error:", e)
                input("ENTER dabao retry ke liye...")

        browser.close()
        print("\n✅ GEM DOWNLOADER COMPLETED")


# =====================================================
# DIRECT RUN (OPTIONAL)
# =====================================================
if __name__ == "__main__":
    cat = sys.argv[1] if len(sys.argv) > 1 else "default"
    run_gem_downloader(cat)
