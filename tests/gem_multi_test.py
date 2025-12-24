import os
import time
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

GEM_URL = "https://gem.gov.in/view_contracts"


def run_multi_pdf_test(category="test"):
    """
    MULTIPLE PDF TEST (FINAL WORKING)

    USER:
      - Search contracts
      - Open contract
      - Solve captcha
      - Click Download (repeat)

    AUTOMATION:
      - Capture PDF from ANY tab
      - Save automatically
    """

    base_dir = os.path.join(os.getcwd(), "downloads", category.lower())
    pdf_dir = os.path.join(base_dir, "pdfs")
    log_excel = os.path.join(base_dir, "multi_test_log.xlsx")

    os.makedirs(pdf_dir, exist_ok=True)

    if os.path.exists(log_excel):
        log_df = pd.read_excel(log_excel)
    else:
        log_df = pd.DataFrame(columns=["PDF", "Time"])

    print("\n" + "=" * 60)
    print("🚀 GEM MULTIPLE PDF TEST (CONTEXT LISTENER)")
    print("📂 Save Dir:", pdf_dir)
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        context = browser.new_context()

        # 🔥 CRITICAL FIX: LISTEN AT CONTEXT LEVEL
        def handle_response(response):
            try:
                ctype = response.headers.get("content-type", "").lower()
                if "application/pdf" in ctype:
                    pdf_bytes = response.body()

                    filename = f"GEM_{int(time.time())}.pdf"
                    save_path = os.path.join(pdf_dir, filename)

                    with open(save_path, "wb") as f:
                        f.write(pdf_bytes)

                    log_df.loc[len(log_df)] = [
                        filename,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    log_df.to_excel(log_excel, index=False)

                    print(f"✅ PDF SAVED: {filename}")
            except Exception as e:
                print("⚠️ Capture error:", e)

        context.on("response", handle_response)

        page = context.new_page()
        page.goto(GEM_URL, timeout=60000)

        print("MANUAL STEPS:")
        print("1. Category + Date + Captcha → SEARCH")
        print("2. Open Contract")
        print("3. Captcha → SUBMIT")
        print("4. CLICK DOWNLOAD")
        print("5. PDF auto-saved")
        print("6. Repeat for next contract\n")

        while True:
            time.sleep(1)


if __name__ == "__main__":
    run_multi_pdf_test("health_test")
