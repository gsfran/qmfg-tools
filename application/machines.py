import os
import json

with open(os.environ['MACHINES_JSON'], 'r') as machines_json:
    machines = json.load(machines_json)
