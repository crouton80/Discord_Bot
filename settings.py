import json, os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json") 

DEFAULT = {"polls_enabled": True, "9gag_enabled": True}

def load():
    if not os.path.isfile(SETTINGS_FILE):
        return dict(DEFAULT)
    with open(SETTINGS_FILE) as f:
        return {**DEFAULT, **json.load(f)}

def save(data):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(data, file, indent=2)

def get(key):
    return load()[key]

def set(key, value):
    data = load()
    data[key] = value
    save(data)