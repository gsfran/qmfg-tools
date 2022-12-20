from __future__ import annotations

import datetime
from dataclasses import dataclass
from datetime import datetime as dt

import pandas as pd

from datafiles import ProcessData


@dataclass
class DataBlock:
    """
    Object to store process data for a given process and time period.
    """
    machine_name: str
    process_code: str
    start_datetime: dt
    end_datetime: dt

    def __post_init__(self) -> None:
        self.data = ProcessData.load(
            self.machine_name, self.process_code,
            self.start_datetime, self.end_datetime
        )


    def sliced(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object sliced from the given start and end time.
        """
        new_block = DataBlock(
            self.machine_name, self.process_code, 
            start_datetime, end_datetime
            )
        new_block.data = ProcessData.slice(
            self.data, start_datetime, end_datetime
            )

        return new_block


    def split(self, freq: str ='h') -> list:
        """
        Splits the DataBlock into multiple smaller objects
        at the specified datetime frequency (default hourly).
        """
        blocks = []
        times = pd.date_range(
            self.start_datetime, self.end_datetime, freq=freq
            ).to_pydatetime()
        time_delta = pd.Timedelta(1, freq)

        for _, start_datetime in enumerate(times):
            end_datetime = start_datetime + time_delta
            blocks.append(
                DataBlock(self.machine_name, self.process_code,
                start_datetime, end_datetime)
            )
        
        return blocks

    


    ## OTHER METHODS TO MANIPULATE AND VISUALIZE DATA