from dataclasses import dataclass
from datetime import datetime as dt

from datafiles import DataBlock


@dataclass
class PrintInspectCamera:
    """
    Poucher Print Inspect Camera (iTrak Poucher)
    """
    machine_info: dict

    PROCESS_CODE = 'PP'
    

    def __post_init__(self):
        self.data_folder = self.machine_info.get('data_folder')

    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        return DataBlock(
            self.data_folder, PrintInspectCamera.PROCESS_CODE,
            start_datetime, end_datetime
            )