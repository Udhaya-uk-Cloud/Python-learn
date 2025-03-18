import json

def load_config(config_path="config.json"):
    with open(config_path) as config_file:
        return json.load(config_file)

config = load_config()