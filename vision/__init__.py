from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as dt
from typing import Protocol

import pandas as pd


@dataclass
class Camera(Protocol):
    """
    Machine vision system camera object
    Any model capable of logging data to csv
    """

    def datablock(
        self: Camera, start_datetime: dt, end_datetime: dt
    ) -> DataBlock:
        ...

    def get_process_data(self: Camera, date: dt) -> pd.DataFrame:
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

    def data(self: DataBlock) -> pd.DataFrame:
        ...
