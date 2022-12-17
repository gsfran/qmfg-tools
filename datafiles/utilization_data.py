from dataclasses import dataclass
from datetime import datetime as dt
from warnings import filterwarnings

import pandas as pd


@dataclass
class OnlineUtilizationLog:
    """
    Tools for working with Online Utilization Log data.
    """

    PATH = '//kansas.us/qfs/Engineering/Shared/Online Utilization Logs'

    def load(machine_name:str, month:dt.month, sheets:list = None) -> pd.DataFrame:
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
                f'{OnlineUtilizationLog.PATH}/Current Month'
                )
        else:
            # use /History/ for any prior months
            folder_path = (
                f'{OnlineUtilizationLog.PATH}/History/{month:%Y/%Y%m}'
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