import os
import json

with open(os.environ['PRODUCTS_JSON'], 'r') as json_file:
    products = json.load(json_file)
