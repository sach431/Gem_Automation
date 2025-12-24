import re

def clean_text(text):
    text = re.sub(r"\(cid:\d+\)", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
