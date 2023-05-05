from __future__ import annotations

import os
import json

json_file = os.environ['PRODUCTS_JSON']
with open(json_file, 'r') as j:
    products: dict[str, dict[str, str]] = json.load(j)


class Product:

    def __init__(self: Product, product: str | None) -> None:
        if product is None:
            raise Exception('No product key given.')
        self.key_ = product
        try:
            (self.name, self.short_name, self.item_number,
             self.standard_rate, self.pouch_type) = products[product].values()
        except KeyError:
            raise Exception(f'No product {product} found in json {json_file}.')

    def __repr__(self: Product) -> str:
        return f'{self.item_number} {self.name}'
