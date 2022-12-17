from dataclasses import dataclass

import pandas as pd

from cameras import PrintInspectCamera, ProductInspectCamera


@dataclass
class Poucher:
    """
    Tools and analytics for the poucher on iTrak production lines.
    """
    machine_info: dict

    MAX_CYCLE_TIME = 1.2


    def __post_init__(self):
        self.product_inspect = ProductInspectCamera(self.machine_info)
        self.print_inspect = PrintInspectCamera(self.machine_info)

    @staticmethod
    def analyze_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates cycle times and instantaneous run rates for poucher cycles.
        """
        data['cycle_time'] = Poucher.cycle_times(data)
        data['cycle_rates'] = Poucher.cycle_rates(data)
        return data

    @staticmethod
    def cycle_times(data: pd.DataFrame) -> pd.Series:
        """
        Returns cycle times for the given data.
        """
        return data['timestamp'].diff()

    @staticmethod
    def cycle_rates(data: pd.DataFrame) -> pd.Series:
        """
        Returns instantaneous machine speeds for the given data.
        """
        return 60 / data['cycle_time']

    @staticmethod
    def first_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns time of first cycle for the given data.
        """
        return min(data.index)

    @staticmethod
    def last_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns instantaneous machine speeds for the given data.
        """
        return max(data.index)

    @staticmethod
    def stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        return data[
            data['cycle_time'] > Poucher.MAX_CYCLE_TIME
            ]    