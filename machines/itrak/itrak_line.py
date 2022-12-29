from dataclasses import dataclass
import json

import pandas as pd

from .poucher import Poucher


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
