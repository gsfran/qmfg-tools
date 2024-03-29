from __future__ import annotations

from application.vision.product_inspect import ProductInspectCamera


class iTrak:
    """
    iTrak Production Line object.
    """
    ITRAK_DICT = {
        'Line 5': {
            'data_folder': 'Line5'
        },
        'Line 6': {
            'data_folder': 'Line6'
        },
        'Line 7': {
            'data_folder': 'Line7'
        },
        'Line 8': {
            'data_folder': 'Line8'
        },
        'Line 9': {
            'data_folder': 'Line9'
        },
        'Line 10': {
            'data_folder': 'Line10'
        },
        'Line 11': {
            'data_folder': 'Line11'
        },
        'Line 12': {
            'data_folder': 'Line12'
        }
    }

    IDEAL_RUN_RATE_HZ = 140 / 60
    STANDARD_RATE_HZ = 5000 / 3600

    def __init__(self: iTrak, line_number: int) -> None:
        self.number = line_number
        self.name = f'Line {self.number}'

        self.machine_info = iTrak.ITRAK_DICT[self.name]
        self.data_folder = self.machine_info['data_folder']
        self.product_inspect = ProductInspectCamera(self.machine_info)
