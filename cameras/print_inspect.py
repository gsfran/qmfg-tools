from dataclasses import dataclass
from datetime import datetime as dt

from cameras import Camera
from datafiles import DataBlock


@dataclass
class PrintInspectCamera(Camera):
    """
    Poucher Print Inspect Camera (iTrak Poucher)
    """

    PROCESS_CODE = 'PP'
    MAX_CYCLE_TIME = 1.2
    

    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.data_folder = self.machine_info.get('data_folder')

    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        return DataBlock(
            self.data_folder, PrintInspectCamera.PROCESS_CODE,
            start_datetime, end_datetime
            )