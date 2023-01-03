import json

from cameras.product_inspect import ProductInspectCamera


class iTrak: 
    """
    iTrak Production Line object.
    """
    MACHINES_JSON = './machines/itrak/machines.json'
    
    IDEAL_RUN_RATE = 140
    STANDARD_RATE = (5000 / 60)

    def __init__(self, line_number: int) -> None:
        self.name = f'Line {line_number}'

        with open(iTrak.MACHINES_JSON, 'r') as reader:
            machine_dict = json.load(reader)

        self.machine_info = machine_dict['itrak'].get(self.name)
        self.data_folder = self.machine_info.get('data_folder')

        self.product_inspect = ProductInspectCamera(self.machine_info)