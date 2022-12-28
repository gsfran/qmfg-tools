import json
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import time

import pandas as pd


@dataclass
class ProcessData:
    """
    Object to manipulate process data and relevant info.
    """

    PATH: str = './testdata'#//kansas.us/qfs/Engineering/Process_Data'


    @staticmethod
    def load(
            data_folder: str, process_code: str, 
            start_datetime: dt, end_datetime: dt, data_headers: list
        ) -> pd.DataFrame:
        """
        Returns process data from time 'initial_time' to time 'final_time'
        as a pandas DataFrame indexed by datetime.
        """

        # creates a DateTimeIndex for the given start and end datetime
        first_day = dt.combine(start_datetime.date(), time(6))
        last_day = dt.combine(end_datetime.date(), time(6))
        days = pd.date_range(first_day, last_day, freq='d')

        # creates a list of process data files to capture
        files = [
            f'{ProcessData.PATH}/{data_folder}/{process_code}'
            f'{day:%Y%m%d}.txt' for day in days
            ]

        # test data, use 10/11/22 for date
        # data = pd.read_csv('short_db.txt', names=column_headers)

        # instantiates a DataFrame for the data
        data = pd.DataFrame(columns=data_headers)

        for file in files:
            try:
                # reads file into DataFrame if it exists
                retrieved_data = pd.read_csv(file, names=data_headers)
            except FileNotFoundError:
                # if no file found, outputs to terminal
                print(f'File Not Found: {file}')
                continue
            
            # concatenates each file to 'data'
            data = pd.concat([data, retrieved_data])

            # clears the DataFrame for the next iteration
            retrieved_data.drop(retrieved_data.index, inplace=True)

        # converts the Cognex timestamp to a DateTime object
        data['datetime'] = pd.to_datetime(data['cognex_timestamp'])

        # sets index to datetime column and drops cognex timestamp
        data = data.set_index('datetime')
        data.drop(['cognex_timestamp'], axis=1, inplace=True)

        # adds timestamp column
        data['timestamp'] = [row_index.timestamp() for row_index in data.index]

        # trims extraneous data from the DataFrame
        data.drop(data[data.index < start_datetime].index, inplace=True)
        data.drop(data[data.index > end_datetime].index, inplace=True)

        return data

    @staticmethod
    def info(process_code: str) -> dict:
        """
        Returns process-specific information.

        Reads from 'processes.json'.
        """

        # load the json containing column headers
        with open('processes.json', 'r') as reader:
                process_info = json.load(reader)

        # self.process_info = process_info[process_code]
        return process_info[process_code]

    @staticmethod
    def slice(
            data: pd.DataFrame, start_datetime: dt, end_datetime: dt
        ) -> pd.DataFrame:
        """
        Slices the given data into the given timespan.
        """
        return data[
            (data.index > start_datetime) and (data.index < end_datetime)
            ]