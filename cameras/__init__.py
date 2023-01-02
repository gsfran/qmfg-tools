from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as dt
from typing import Protocol

from ._file_handling import ProcessData

import pandas as pd


@dataclass
class Camera(Protocol):
    """
    Machine vision system camera object. Any model capable of datalogging to /Process_Data/.
    """

    def datablock(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        ...

    def get_process_data(self, date: dt) -> pd.DataFrame:
        ...

@dataclass
class DataBlock(Protocol):
    """
    Object to store data for a given process and time period.
    """
    _source: Camera
    _data: pd.DataFrame
    start_datetime: dt
    end_datetime: dt

    def data(self) -> pd.DataFrame:
        ...