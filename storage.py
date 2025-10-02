import os
import json

STORAGE_FILE = "recent_files.json"


class RecentStorage:
    def __init__(self):
        if not os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, "w") as f:
                json.dump([], f)

    def save_recent(self, file):
        with open(STORAGE_FILE, "r+") as f:
            data = json.load(f)
            if file not in data:
                data.append(file)
            f.seek(0)
            json.dump(data[-10:], f, indent=2)
            f.truncate()

    def get_recent(self):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
