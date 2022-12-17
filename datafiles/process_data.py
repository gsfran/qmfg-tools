import datetime
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

    PATH: str = '//kansas.us/qfs/Engineering/Process_Data'


    @staticmethod
    def load(
            data_folder: str, process_code: str,
            start_datetime: dt, end_datetime: dt
        ) -> pd.DataFrame:
        """
        Returns process data from time 'initial_time' to time 'final_time'
        as a pandas DataFrame indexed by datetime.
        """

        # loads column headers from 'data_labels.json'
        column_headers = ProcessData.info(process_code).get(
                'process_data_headers'
                )

        # generates a DateTimeIndex for the given start and end datetime
        first_day = dt.combine(start_datetime, time(0))
        last_day = dt.combine(end_datetime, time(0))
        days = pd.date_range(first_day, last_day, freq='d')

        # generates a list of process data files to capture

        files = [
            f'{ProcessData.PATH}/{data_folder}/{process_code}'
            f'{day:%Y%m%d}.txt' for day in days
            ]

        # short DataBlock for quicker testing, use 10/11/22 for date
        # data = pd.read_csv('short_db.txt', names=column_headers)

        # instantiates a DataFrame for the data
        process_data = pd.DataFrame(columns=column_headers)

        for file in files:
            try:
                # reads file into DataFrame if it exists
                retrieved_data = pd.read_csv(file, names=column_headers)
            except FileNotFoundError:
                # if no file found, outputs to terminal
                print(f'File Not Found: {file}')
                continue
            
            # concatenates each file to 'data'
            process_data = pd.concat([process_data, retrieved_data])

            # clears the DataFrame for the next iteration
            retrieved_data.drop(retrieved_data.index, inplace=True)

        # converts the Cognex timestamp to a DateTime object
        process_data['datetime'] = pd.to_datetime(
            process_data['cognex_timestamp']
            )

        # sets index to datetime column and drops cognex timestamp
        process_data = process_data.set_index('datetime')
        process_data.drop(['cognex_timestamp'], axis=1, inplace=True)

        # adds timestamp column
        process_data['timestamp'] = [
            row_index.timestamp() for row_index in process_data.index
            ]

        # trims extraneous data from the DataFrame
        process_data.drop(
            process_data[process_data.index < start_datetime].index,
            axis=0, inplace=True
            )
        process_data.drop(
            process_data[process_data.index > end_datetime].index,
            axis=0, inplace=True
            )

        return process_data


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