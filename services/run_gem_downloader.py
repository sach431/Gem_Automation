import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def auto_download_pdf(pdf_dir):
    chrome_options = Options()
    chrome_options.add_experimental_option(
        "debuggerAddress", "127.0.0.1:9222"
    )

    prefs = {
        "download.default_directory": pdf_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    wait = WebDriverWait(driver, 60)

    print("🔗 Attached to existing Chrome session")

    # Switch to last tab (popup / PDF tab)
    driver.switch_to.window(driver.window_handles[-1])
    print("🪟 Switched to active popup tab")

    time.sleep(2)

    # Try all iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"🧩 Iframes found: {len(iframes)}")

    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)
            print(f"➡ Switched to iframe {i+1}")
            break
        except:
            pass

    # Wait and force-click download
    print("⏳ Waiting for Download button...")
    download_btn = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(text(),'Download') or contains(@class,'download')]"
        ))
    )

    driver.execute_script("""
        arguments[0].scrollIntoView(true);
        arguments[0].click();
    """, download_btn)

    print("⬇️ FORCE CLICK executed on Download button")

    time.sleep(15)
    print("✅ Download trigger finished")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("❌ PDF directory missing")
        sys.exit(1)

    pdf_dir = os.path.abspath(sys.argv[1])
    os.makedirs(pdf_dir, exist_ok=True)

    print("\n🚀 GeM PDF AUTO DOWNLOAD – FINAL FORCE CLICK TEST")
    print("✔ Remote Chrome open")
    print("✔ Captcha solved")
    print("✔ Popup open, Download NOT clicked manually\n")

    auto_download_pdf(pdf_dir)

    input("\nPress ENTER to exit...")
