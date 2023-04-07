import os
import json

with open(os.environ['PRODUCTS_JSON'], 'r') as products_json:
    products: dict[str, dict[str, str]] = json.load(products_json)
