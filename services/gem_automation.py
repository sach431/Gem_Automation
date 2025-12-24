# services/gem_automation.py

import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_automation(category: str):
    base_dir = os.getcwd()
    pdf_dir = os.path.join(base_dir, "downloads", category.lower(), "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    print("=" * 60)
    print("GEM AUTOMATION STARTED (NETWORK BASED)")
    print("Category :", category)
    print("Save Dir :", pdf_dir)
    print("=" * 60)

    print("\nMANUAL STEPS (ONLY ONCE):")
    print("1. Select category & date range")
    print("2. Fill captcha → SEARCH")
    print("3. Open first contract")
    print("4. Fill captcha → SUBMIT")
    print("⬇️ After this automation will download PDFs\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Open GeM
        page.goto(GEM_URL, timeout=60000)

        print("⏳ Waiting for user to reach CONTRACT PAGE...")
        input("👉 Contract page open ho jaye to ENTER dabao...")

        while True:
            try:
                # 🔹 Contract number (page se)
                contract_no = page.locator("text=Contract No").first.text_content()
                contract_no = contract_no.split(":")[-1].strip()

                pdf_name = f"{category}_{contract_no}.pdf"
                pdf_path = os.path.join(pdf_dir, pdf_name)

                if os.path.exists(pdf_path):
                    print(f"⏭️ Already downloaded: {pdf_name}")
                else:
                    print(f"⬇️ Downloading: {pdf_name}")

                    # 🔹 Browser cookies → requests session
                    cookies = context.cookies()
                    session = requests.Session()

                    for c in cookies:
                        session.cookies.set(c["name"], c["value"])

                    # 🔥 REAL DOWNLOAD REQUEST (GeM backend)
                    download_url = "https://gem.gov.in/view_contracts/download"

                    payload = {
                        "contract_no": contract_no
                    }

                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": page.url
                    }

                    response = session.post(
                        download_url,
                        headers=headers,
                        data=payload,
                        timeout=60
                    )

                    if response.status_code == 200 and response.content[:4] == b"%PDF":
                        with open(pdf_path, "wb") as f:
                            f.write(response.content)
                        print(f"✅ Saved: {pdf_name}")
                    else:
                        print("❌ PDF download failed (captcha/session issue)")
                        print("➡️ Re-submit captcha and try again")

                # 🔁 Go back to list
                page.go_back()
                time.sleep(2)

                print("\n👉 Next contract open karo (manual captcha)")
                input("ENTER dabao jab next contract ready ho...")

            except KeyboardInterrupt:
                print("\n🛑 Automation stopped by user")
                break
            except Exception as e:
                print("⚠️ Error:", e)
                break

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gem_automation.py <Category>")
        sys.exit(1)

    run_gem_automation(sys.argv[1])
