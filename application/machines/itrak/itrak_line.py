from application.cameras.product_inspect import ProductInspectCamera


class iTrak: 
    """
    iTrak Production Line object.
    """
    ITRAK_DICT = {
    'Line 5': {
        # 'production_line': 'Line 5',
        'data_folder': 'Line5'
        },
    'Line 6': {
        # 'production_line': 'Line 6',
        'data_folder': 'Line6'
        },
    'Line 7': {
        # 'production_line': 'Line 7',
        'data_folder': 'Line7'
        },
    'Line 8': {
        # 'production_line': 'Line 8',
        'data_folder': 'Line8'
        },
    'Line 9': {
        # 'production_line': 'Line 9',
        'data_folder': 'Line9'
        }
    }
    
    IDEAL_RUN_RATE = 140
    STANDARD_RATE = (5000 / 60)

    def __init__(self, line_number: int) -> None:
        self.name = f'Line {line_number}'

        self.machine_info = iTrak.ITRAK_DICT.get(self.name)
        self.data_folder = self.machine_info.get('data_folder')

        self.product_inspect = ProductInspectCamera(self.machine_info)