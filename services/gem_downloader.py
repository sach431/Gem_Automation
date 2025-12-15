import time
import shutil
import os

def watch_and_move_pdf(download_dir, target_dir, timeout=60):
    print("👀 Waiting for PDF download...")

    start = time.time()
    seen = set(os.listdir(download_dir))

    while time.time() - start < timeout:
        current = set(os.listdir(download_dir))
        new_files = current - seen

        for f in new_files:
            if f.lower().endswith(".pdf"):
                src = os.path.join(download_dir, f)
                dst = os.path.join(target_dir, f)

                time.sleep(2)  # ensure download complete
                shutil.move(src, dst)

                print(f"✅ PDF moved to {target_dir}")
                return dst

        time.sleep(1)

    print("❌ No PDF detected within timeout")
    return None
