from dataclasses import dataclass

import pandas as pd

from .poucher import Poucher


@dataclass
class iTrakLine: 
    """
    iTrak Production Line object.
    """
    machine_info: dict

    def __post_init__(self):
        self.data_folder = self.machine_info.get('data_folder')
        self.poucher = Poucher(self.machine_info)
        
        print(f'{self.machine_info.get("production_line")} created:')
        print(f'{self.machine_info}')

    IDEAL_RUN_RATE = 140
    STANDARD_RATE = (5000 / 60)