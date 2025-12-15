import time
import os
import shutil

def watch_and_move_pdf(target_folder, timeout=120):
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    print("Watching folder:", downloads)

    existing = set(os.listdir(downloads))
    start = time.time()

    while time.time() - start < timeout:
        current = set(os.listdir(downloads))
        new_files = current - existing

        for file in new_files:
            if file.lower().endswith(".pdf") and not file.endswith(".crdownload"):
                src = os.path.join(downloads, file)
                dst = os.path.join(target_folder, file)

                time.sleep(2)  # download complete hone ka wait
                shutil.move(src, dst)

                print("PDF moved to:", dst)
                return dst

        time.sleep(1)

    print("No PDF detected")
    return None
