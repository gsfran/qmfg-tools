from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from datetime import datetime as dt

import numpy as np
import pandas as pd

from datafiles import *


@dataclass
class DataBlock:
    """
    Object to store process data for a given process and time period.
    """
    data_folder: str
    process_code: str
    start_datetime: dt
    end_datetime: dt
    data_headers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.data = ProcessData.load(
            self.data_folder, self.process_code, self.data_headers,
            self.start_datetime, self.end_datetime
            )


    def slice(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object sliced from the given start and end time.
        """
        new_block = DataBlock(
            self.data_folder, self.process_code, self.data_headers,
            start_datetime, end_datetime
            )
        new_block.data = ProcessData.slice(
            self.data, start_datetime, end_datetime
            )

        ## IMPLEMENT CHECKS FOR TIME VALIDITY

        return new_block


    def split(self, freq: str ='h') -> list:
        """
        Splits the DataBlock into multiple smaller objects
        at the specified datetime frequency (default hourly).
        """
        blocks = []
        datetimes = pd.date_range(
            self.start_datetime, self.end_datetime, freq=freq
            ).to_pydatetime()
        time_delta = pd.Timedelta(1, freq)

        for start_datetime in np.delete(datetimes, -1):
            end_datetime = start_datetime + time_delta
            blocks.append(DataBlock.slice(start_datetime, end_datetime))
        
        return blocks

    
    ## OTHER METHODS TO MANIPULATE AND VISUALIZE DATA