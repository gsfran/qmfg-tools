import json

from cameras.product_inspect import ProductInspectCamera


class iTrakLine: 
    """
    iTrak Production Line object.
    """
    MACHINE_DICT = './machines/machines.json'
    IDEAL_RUN_RATE = 140
    STANDARD_RATE = (5000 / 60)

    def __init__(self, line_number: int) -> None:
        self.name = f'Line {line_number}'

        with open(iTrakLine.MACHINE_DICT, 'r') as reader:
            machine_dict = json.load(reader)

        self.machine_info = machine_dict['itrak'].get(self.name)
        self.data_folder = self.machine_info.get('data_folder')
        self.poucher = Poucher(self.machine_info)


class Poucher:
    """
    iTrak Poucher object, contains two Camera objects.
    """
    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.product_inspect = ProductInspectCamera(self.machine_info)