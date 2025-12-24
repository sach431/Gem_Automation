from playwright.sync_api import sync_playwright
import os

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 1️⃣ Open GEM View Contracts page
        page.goto("https://gem.gov.in/view_contracts", wait_until="domcontentloaded")

        print("➡️ Category select karo")
        print("➡️ Date range (Quarter) bharo")
        print("➡️ Captcha bharo aur SEARCH click karo")

        # 2️⃣ Wait till contract list loads
        page.wait_for_selector("table tbody tr", timeout=0)
        print("✅ Contract list aa gayi")

        rows = page.locator("table tbody tr")
        total_rows = rows.count()
        print(f"🔢 Total contracts found: {total_rows}")

        # 3️⃣ Click first visible contract (same page / modal)
        clicked = False

        for i in range(total_rows):
            row = rows.nth(i)
            link = row.locator("a").first

            if link.count() > 0 and link.is_visible():
                print(f"➡️ Clicking contract row {i + 1}")
                link.click()
                clicked = True
                break

        if not clicked:
            print("❌ Koi clickable contract nahi mila")
            browser.close()
            return

        print("➡️ Contract open ho gaya")
        print("➡️ Captcha manually bharo aur SUBMIT karo")

        # 4️⃣ Wait for Download button after captcha submit
        page.wait_for_selector("text=Download", timeout=0)
        print("✅ Download button visible")

        # 5️⃣ Download PDF
        with page.expect_download() as download_info:
            page.click("text=Download")

        download = download_info.value
        filename = download.suggested_filename

        # Save PDF in same project folder
        save_path = os.path.join(os.getcwd(), filename)
        download.save_as(save_path)

        # 6️⃣ STRONG CONFIRMATION
        if os.path.exists(save_path):
            print("🎉 PDF DOWNLOAD CONFIRMED")
            print(f"📄 File saved at: {save_path}")
        else:
            print("❌ PDF download failed")

        browser.close()

if __name__ == "__main__":
    main()
