import os
import time
from playwright.sync_api import sync_playwright

GEM_URL = "https://gem.gov.in/view_contracts"


def run_gem_downloader(category="default"):
    """
    FINAL GEM MULTIPLE PDF DOWNLOADER (SIMPLE VERSION)
    -------------------------------------------------
    ✔ Manual captcha
    ✔ Multiple contract PDFs
    ✔ Popup safe
    ✔ Resume / skip duplicate PDFs
    """

    # ---------- PDF FOLDER ----------
    pdf_dir = os.path.join(
        os.getcwd(), "downloads", category.lower(), "pdfs"
    )
    os.makedirs(pdf_dir, exist_ok=True)

    downloaded = {
        f.lower() for f in os.listdir(pdf_dir)
        if f.lower().endswith(".pdf")
    }

    print("\n======================================")
    print("🚀 GEM PDF DOWNLOADER STARTED")
    print(f"📂 Category   : {category}")
    print(f"📂 Save path  : {pdf_dir}")
    print("======================================\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 1️⃣ Open GeM
        page.goto(GEM_URL)

        print("🛑 MANUAL STEPS (DO THIS NOW)")
        print("1. Select Category")
        print("2. Select Date / Quarter")
        print("3. Fill Captcha")
        print("4. Click SEARCH\n")

        # 2️⃣ Wait for contract table
        page.wait_for_selector("table tbody tr", timeout=0)
        print("✅ Contract list loaded\n")

        # 3️⃣ Loop contracts
        while True:
            rows = page.locator("table tbody tr")
            total = rows.count()

            if total == 0:
                print("🎉 All contracts processed")
                break

            print(f"➡️ Remaining contracts: {total}")

            row = rows.first
            link = row.locator("a").first

            if link.count() == 0:
                print("⚠️ No contract link found")
                break

            # -------- POPUP SAFE CLICK --------
            with page.expect_popup() as pop:
                link.click()

            popup = pop.value
            popup.wait_for_load_state()

            print("🛑 Popup opened → captcha bharo & submit")

            # Wait until Download appears
            popup.wait_for_selector("text=Download", timeout=0)

            # -------- DOWNLOAD --------
            with popup.expect_download(timeout=0) as d:
                popup.click("text=Download")

            download = d.value
            filename = download.suggested_filename.lower()
            save_path = os.path.join(pdf_dir, filename)

            if os.path.exists(save_path):
                print(f"⏭️ Already exists, skipped: {filename}")
            else:
                download.save_as(save_path)
                print(f"✅ Downloaded: {filename}")

            popup.close()
            time.sleep(1.5)

        browser.close()
        print("\n✅ GEM DOWNLOAD FINISHED")


# -------- DIRECT RUN --------
if __name__ == "__main__":
    run_gem_downloader("default")
