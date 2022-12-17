from dataclasses import dataclass
from datetime import datetime as dt

import pandas as pd

from .process_data import ProcessData


@dataclass
class DataBlock:
    """
    Object to store process data for a given process and time period.
    """
    machine_name: str
    process_code: str
    start_datetime: dt
    end_datetime: dt

    def __post_init__(self):
        self.data = ProcessData.load(
            self.machine_name, self.process_code,
            self.start_datetime, self.end_datetime
        )

    def split(self, freq: str = 'hour'):
        """
        Splits the DataBlock into multiple smaller objects
        at the specified frequency (default hourly).
        """

    ## OTHER METHODS TO MANIPULATE AND VISUALIZE DATA