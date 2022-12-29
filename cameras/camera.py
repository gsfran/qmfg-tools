from abc import ABC, abstractmethod
from datetime import datetime as dt

import pandas as pd

from datafiles import DataBlock


class Camera(ABC):
    """
    Machine vision system camera object. Any model capable of datalogging to /Process_Data/.
    """

    @abstractmethod
    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        pass