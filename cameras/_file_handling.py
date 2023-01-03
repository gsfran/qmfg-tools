from datetime import datetime as dt
from warnings import filterwarnings

import numpy as np
import pandas as pd


class ProcessData:
    """
    Object to fetch process data.
    """

    # ROOT_PATH = '//kansas.us/qfs/Engineering/Process_Data'
    ROOT_PATH = './testdata'

    @staticmethod
    def load(
            target_file: str, _data_headers: list
        ) -> pd.DataFrame:
        """
        Returns a Dataframe containing cleaned process data for the given file.
        """
        _path = f'{ProcessData.ROOT_PATH}/{target_file}'
        data = ProcessData._load_raw_data(
            _path, _data_headers
            )
        print(f'{dt.now()}: Data loaded.')

        if data is None:
            raise Exception("Empty DataFrame Loaded.")

        return ProcessData._clean_data(data)

    @staticmethod
    def _clean_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        Indexes the given data by timestamp and calculates
        the cycles time and instantaneous rate for each cycle.
        """
        # clean up cognex timestamp and index by DatetimeIndex
        ## Could add a parsing function to better handle changes ##
        data['datetime'] = pd.to_datetime(data['cognex_timestamp'])

        # sets the DatetimeIndex and removes the cognex timestamp
        data = data.set_index('datetime')
        data.drop(['cognex_timestamp'], axis=1, inplace=True)

        # converts the datetime column to timestamp values, 
        # needed to calculate cycle times
        data['timestamp'] = (
            data.index.values.astype(np.int64) / 10 ** 9
            )

        # adds cycle time and frequency data to the DataFrame
        data['cycle_time'] = data['timestamp'].diff()
        data['cycle_Hz'] = 1 / data['cycle_time']

        print(f'{dt.now()}: Cleaning data.')

        return data

    @staticmethod
    def _load_raw_data(_filepath: str, _data_headers: list) -> pd.DataFrame:
        """
        Returns a Dataframe containing all process data for the given file.
        """
        try:
            data = pd.read_csv(_filepath, names=_data_headers)
        except FileNotFoundError:
            # if no file found, outputs to terminal
            print(f'{dt.now()}: Requested data file not found: {_filepath}')
            return None

        print(f'{dt.now()}: Loading file: {_filepath}')
        return data


class OnlineUtilizationLog:
    """
    Tools for working with Online Utilization Log data.
    """

    ROOT_PATH = '//kansas.us/qfs/Engineering/Shared/Online Utilization Logs'

    def load(
        machine_name:str, month:dt.month, sheets:list = None
        ) -> pd.DataFrame:
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
                    excel_reader, sheet_name=sheets, header=None,
                    na_filter=False
                    )
            except Exception:
                raise Exception(f'{file_path} could not be loaded.')

        return utilization_log_data