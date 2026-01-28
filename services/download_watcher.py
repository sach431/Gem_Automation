# services/download_watcher.py
# =====================================================
# FINAL DOWNLOAD WATCHER – RENAME + CATEGORY MOVE
# =====================================================

import os
import time
import shutil

# Project download base folder
PROJECT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")


def wait_for_pdf_download(category, timeout=180):
    """
    Watches project downloads folder.
    Detects new PDF.
    Renames it.
    Moves it to category/pdfs folder.
    """

    print("👀 Watching project downloads folder...")
    print(f"📂 Category: {category}")

    start_time = time.time()
    before = set(os.listdir(PROJECT_DOWNLOAD_DIR))

    while time.time() - start_time < timeout:
        after = set(os.listdir(PROJECT_DOWNLOAD_DIR))
        new_files = after - before

        for filename in new_files:
            name = filename.lower()

            # Ignore temp / non-pdf files
            if name.endswith(".crdownload") or not name.endswith(".pdf"):
                continue

            src_path = os.path.join(PROJECT_DOWNLOAD_DIR, filename)

            # Wait until file write is complete
            if not _is_file_ready(src_path):
                continue

            print(f"✅ Download detected: {filename}")

            # Extract contract no from filename if possible
            contract_no = extract_contract_no(filename)
            today = time.strftime("%Y-%m-%d")

            new_filename = f"{category}_{contract_no}_{today}.pdf"

            target_dir = os.path.join(
                PROJECT_DOWNLOAD_DIR, category, "pdfs"
            )
            os.makedirs(target_dir, exist_ok=True)

            target_path = os.path.join(target_dir, new_filename)

            # Avoid duplicate
            if os.path.exists(target_path):
                print("⚠️ PDF already exists. Skipping.")
                return target_path

            shutil.move(src_path, target_path)
            print(f"📁 Saved as: {target_path}")

            return target_path

        time.sleep(1)

    print("❌ No PDF detected within timeout")
    return None


def _is_file_ready(path, wait=1.5):
    """Check file write completion"""
    try:
        size1 = os.path.getsize(path)
        time.sleep(wait)
        size2 = os.path.getsize(path)
        return size1 == size2
    except OSError:
        return False


def extract_contract_no(filename):
    """
    Try to extract GEM contract number.
    Fallback = UNKNOWN
    """
    import re

    match = re.search(r"GEMC[-_]\d+", filename.upper())
    if match:
        return match.group().replace("_", "-")

    return "UNKNOWN"
