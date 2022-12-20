from dataclasses import dataclass

import pandas as pd

from .poucher import Poucher


class iTrakLine: 
    """
    iTrak Production Line object.
    """
    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.data_folder = self.machine_info.get('data_folder')
        self.poucher = Poucher(self.machine_info)
        
        print(f'{self.machine_info.get("production_line")} created:')
        print(f'{self.machine_info}')

    IDEAL_RUN_RATE = 140
    STANDARD_RATE = (5000 / 60)