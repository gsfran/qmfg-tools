import os
import json

with open(os.environ['MACHINES_JSON'], 'r') as machines_json:
    machines: dict[str, dict[str, str]] = json.load(machines_json)
