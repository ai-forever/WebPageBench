from datetime import datetime

from .constants import LOG_FILE

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as fout:
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        fout.write(f"[{date}] {msg}\n")
