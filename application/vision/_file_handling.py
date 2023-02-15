from datetime import datetime as dt
import os
from warnings import filterwarnings

import numpy as np
import pandas as pd


class ProcessData:
    """
    Object to fetch process data.
    """
    ROOT_PATH = os.environ['PD_PATH']

    @staticmethod
    def load(
        target_file: str, _data_headers: list
    ) -> pd.DataFrame | None:
        """
        Returns a Dataframe containing cleaned process data for the given file.
        """
        _t = dt.now()
        print(f'{_t}: Loading data files...\t\t\t', end='')

        _path = f'{ProcessData.ROOT_PATH}/{target_file}'
        _raw_data = ProcessData._load_raw_data(
            _path, _data_headers
        )

        print(f'Done in {dt.now() - _t}')
        if _raw_data is None:
            return None
        return ProcessData._clean_data(_raw_data)

    @staticmethod
    def _clean_data(data_: pd.DataFrame) -> pd.DataFrame:
        """
        Indexes the given data by timestamp and calculates
        the cycles time and instantaneous rate for each cycle.
        """
        _t = dt.now()
        print(f'{_t}: Cleaning raw data...\t\t\t', end='')
        # clean up cognex timestamp and index by DatetimeIndex
        # Could add a parsing function to better handle changes ##
        data_['datetime'] = pd.to_datetime(data_['cognex_timestamp'])

        # sets the DatetimeIndex and removes the cognex timestamp
        data_ = data_.set_index('datetime')
        data_ = data_.drop(['cognex_timestamp'], axis=1)

        # converts the datetime column to timestamp values,
        # needed to calculate cycle times
        data_['timestamp'] = (
            data_.index.values.astype(np.int64) / 10 ** 9
        )

        # adds cycle time and frequency data to the DataFrame
        data_['cycle_time'] = data_['timestamp'].diff()
        data_['cycle_Hz'] = 1 / data_['cycle_time']

        print(f'Done in {dt.now() - _t}')
        return data_

    @staticmethod
    def _load_raw_data(
        _filepath: str, _data_headers: list
    ) -> pd.DataFrame | None:
        """
        Returns a Dataframe containing all process data for the given file.
        """
        try:
            return pd.read_csv(_filepath, names=_data_headers)
        except FileNotFoundError:
            # if no file found, outputs warning to terminal
            print(f'{dt.now()}: File not found: {_filepath}')
            return None


class OnlineUtilizationLog:
    """
    Tools for working with Online Utilization Log data.
    """
    ROOT_PATH = os.environ['OUL_PATH']

    @staticmethod
    def load(
        machine_name: str, month: dt, sheets: list[str] = []
    ) -> dict[int | str, pd.DataFrame] | None:
        """
        Returns data from the machine's Online Utilization Log
        """

        first_of_this_month = dt(
            dt.today().year, dt.today().month, 1, 0, 0, 0
        )
        file_name = f'{machine_name} Online Utilization.xlsx'

        if (month >= first_of_this_month):
            # use /Current Month/ for current month
            folder_path = (
                f'{OnlineUtilizationLog.ROOT_PATH}/Current Month'
            )
        else:
            # use /History/ for any prior months
            folder_path = (
                f'{OnlineUtilizationLog.ROOT_PATH}/History/{month:%Y/%Y%m}'
            )

        file_path = f'{folder_path}/{file_name}'

        with pd.ExcelFile(file_path) as excel_reader:
            # reads the excel file into DataFrame
            filterwarnings(
                'ignore', category=UserWarning, module='openpyxl'
            )
            try:
                utilization_log_data = pd.read_excel(
                    excel_reader, sheet_name=[*sheets], header=None,
                    na_filter=False
                )
            except FileNotFoundError:
                raise

        return utilization_log_data
