import copy
import datetime
import json
from warnings import filterwarnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PD_PATH = '//kansas.us/qfs/Engineering/Process_Data'
# OUL_PATH = '//kansas.us/qfs/Engineering/Shared/Online Utilization Logs'

# test vars
# PD_PATH = './testdata/fixed'
OUL_PATH = './'
NOW_TS = datetime.datetime.now().strftime('%Y%m%d%H%M%S')


class Machine:

    """
    Generic class for a machine or production line. 
    Contains methods common to all machines compatible with this module.
    
    """

    @staticmethod
    def get_process_data(machine, process_id, t_start, t_end):

        """
        Returns process data from time 't_start' to time 't_end'
        as a pandas DataFrame indexed by datetime.

        """
        days_start = datetime.datetime.combine(t_start, datetime.time(0))
        days_end = datetime.datetime.combine(t_end, datetime.time(0))

        days = pd.date_range(days_start, days_end, freq='d')

        # generates a list of process data files for the
        # given time span (one for each calendar day)
        process_data_files = [
                f'{PD_PATH}/{machine}/{process_id}'
                f'{day:%Y%m%d}.txt' for day in days
            ]
        
        # data labels are loaded from 'labels.json'
        data_labels = Machine.get_labels(process_id, 'process_data')

        # short DataBlock for quicker testing, use 10/11/22 for date
        # data = pd.read_csv('short_db.txt', names=data_labels)

        # load empty dataframe with the given columns
        data = pd.DataFrame(columns=data_labels)


        for file in process_data_files:
            # loop through the process data files and
            # concatenate them into a single DataFrame
            try:
                # read file into DataFrame if it exists
                df = pd.read_csv(file, names=data_labels)
            except FileNotFoundError:
                # if no file found, output to terminal
                print(f'No process data found: {file}')
                continue
            
            # concatenate each file to 'data'
            data = pd.concat([data, df])

            # clears the DataFrame for the next iteration
            df.drop(df.index, inplace=True)

        # converts the 't_stamp' column of data
        # from a string object to a datetime object
        data['datetime'] = pd.to_datetime(data['t_stamp'])

        # sets the datetime column as the DataFrame index,
        # very useful for slicing data by date and time
        data = data.set_index('datetime')

        # drops DataFrame rows that represent cycles
        # which are outside of the given time range
        data.drop(
            data[data.index < t_start].index, axis=0, inplace=True
                )
        data.drop(
            data[data.index > t_end].index, axis=0, inplace=True
                )

        # drops the string-type timestamp column from the DataFrame
        data.drop(['t_stamp'], axis=1, inplace=True)

        return data

    @staticmethod
    def get_labels(process_id, label_id):

        """
        Returns list of data labels or stat labels 
        for a given process. 

        Reads labels from 'data_labels.json'.

        """

        with open('labels.json', 'r') as reader:
                # load the json containing all labels
                label_dict = json.load(reader)

        # retrieves the list of labels by process_id
        labels = label_dict.get(process_id).get(label_id)

        return labels

    @staticmethod
    def load_recipes(process_id):

        """
        Returns dict object of recipes for the given process.

        Reads recipes from 'recipes.json'.
        
        """
        with open('recipes.json', 'r') as reader:
            # load the json containing recipes
            recipe_dict = json.load(reader)

        # retrieves the recipe list by process_id
        recipes = recipe_dict.get(process_id)

        return recipes

    @staticmethod
    def get_utilization_log(machine, month, sheets=None):

        today = datetime.datetime.today()

        if (month > datetime.datetime(today.year, today.month, 1, 0, 0, 0)):
            # use /Current Month/ for current month
            path = (f'{OUL_PATH}/Current Month')
        else:
            # use /History/ for any prior months
            path = (f'{OUL_PATH}/History/{month:%Y/%Y%m}')

        # sets the file path for the Utilization Log
        file = f'{path}/{machine} Online Utilization.xlsx'

        with pd.ExcelFile(file) as xls:
            # reads the excel file into DataFrame
            filterwarnings(
                'ignore', category=UserWarning, module='openpyxl'
                )
            try:
                df = pd.read_excel(
                    xls, sheet_name=sheets, header=None,
                    na_filter=False
                    )
            except Exception:
                raise Exception(f'{file} could not be loaded.')

        return df


class iTrak: 

    """
    iTrak Production Line object.
    
    """
    def __init__(self, name):
        self.line = name
        self.MACHINE_ID = name.replace(' ','')
        print(f'{name}')
        self.poucher = iTrakPoucher(self.line)


class iTrakPoucher:

    """
    iTrak Poucher object.
    
    """
    PROCESS_ID = 'PR'

    # standard and ideal rates, converted to per second
    IDEAL_RUN_RATE = 140 / 60
    STD_RATE = 5000 / 3600

    def __init__(self, line):
        self.name = f'{line} Poucher'
        self.line = line
        self.MACHINE_ID = line.replace(' ','')

    # region data-load

    def load_workday(self, date, startup, shutdown, shift_change):
       
        """
        Loads process data for the workday and sets
        'self.data' to the whole workday.
        
        """
        self.date = date
        self.startup = startup
        self.shutdown = shutdown
        self.shift_change = shift_change
        self.workday = DataBlock(
            self.MACHINE_ID, self.PROCESS_ID,
            startup, shutdown, shift_change
        )
        self.workday.get_data()
        self.analyze_cycle_data()

    # endregion

    def slice_hours(self):

        """
        Slices the workday data into hour-long DataBlocks. 
        
        """
        self.hour_list = pd.date_range(self.startup, self.shutdown, freq='h')
        self.hour_blocks = []

        for hour in self.hour_list:
            hour_start_time = hour
            hour_end_time = hour + datetime.timedelta(hours=1)
            self.hour_blocks.append(
                DataBlock(
                    self.MACHINE_ID, self.PROCESS_ID, 
                    hour_start_time, hour_end_time
                )
            )
        
        for hour_block in self.hour_blocks:
            hour_block.data = self.workday.data[
                (
                    self.workday.data.index >= hour_block.t_start
                    ) & (
                        self.workday.data.index < hour_block.t_end
                        )
                ]
            hour_block.stops = self.workday.stops[
                (
                    self.workday.stops.index >= hour_block.t_start
                    ) & (
                        self.workday.stops.index < hour_block.t_end
                        )
                ]
            hour_block.yields = self.workday.yields[
                (
                    self.workday.yields.index >= hour_block.t_start
                    ) & (
                        self.workday.yields.index < hour_block.t_end
                        )
                ]

    def slice_shifts(self):

        """
        Slices the workday data into shift-long DataBlocks. 
        
        """

        self.first_shift = DataBlock(self.MACHINE_ID, self.PROCESS_ID, self.startup, self.shift_change)
        self.second_shift = DataBlock(self.MACHINE_ID, self.PROCESS_ID, self.shift_change, self.shutdown)

        shifts = [self.first_shift, self.second_shift]

        for shift in shifts:
            shift.data = self.workday.data[
                (
                    self.workday.data.index >= shift.t_start
                    ) & (
                        self.workday.data.index < shift.t_end
                        )
                ]

            shift.stops = self.workday.stops[
                (
                    self.workday.stops.index >= shift.t_start
                    ) & (
                        self.workday.stops.index < shift.t_end
                        )
                ]

            shift.yields = self.workday.yields[
                (
                    self.workday.yields.index >= shift.t_start
                    ) & (
                        self.workday.yields.index < shift.t_end
                        )
                ]


    def analyze_cycle_data(self):

        """
        Calculates cycle statistics for poucher data.

        't' = timestamp (in epoch time)
        'dt' = cycle time
        'Hz', 'upm' = rate in units per second and units per minute
        
        """

        # adds timestamps to data
        self.workday.data['t'] = [
            d.timestamp() for d in self.workday.data.index
            ]

        # adds 'dt' column to data
        self.workday.data['dt'] = self.workday.data['t'].diff()

        # adds rate columns to data
        self.workday.data['Hz'] = 1 / self.workday.data['dt']
        self.workday.data['upm'] = self.workday.data['Hz'] * 60


    def calculate_workday_stats(self):
        
        """
        Runs all statistics on the production data.
        
        """
        self.calculate_stats()
        self.find_stops()
        self.calculate_stop_stats()


    def get_span_stats(self):
        
        """
        Runs all statistics on the timespan loaded by slice_workday().
        
        """
        self.calculate_stats('span')
        self.find_stops('span')
        self.calculate_stop_stats('span')


    def calculate_stats(self):

        """
        Calculates run statistics for poucher data in a given span.
        Mode arguments: 'w' for workday, 's' for slice.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Getting stats.')

        # get stats labels from json file
        stats_labels = Machine.get_labels(self.PROCESS_ID, 'stats')

        db = self.workday
       
        db.stats = pd.DataFrame(
            index=[f'{self.MACHINE_ID}-{self.date}'], columns=stats_labels)

        # empty flights
        db.empties = db.data[db.data['part'] == 0]
        db.stats['empty'] = db.empties.__len__()
        db.stats['empty_perc'] = (db.stats['empty'] / db.data.__len__())

        # parts
        db.parts = db.data[db.data['part'] != 0]
        db.stats['parts'] = db.parts.__len__()
        
        # reworks
        db.reworks = db.parts[db.parts.duplicated('serial')]
        db.stats['reworks'] = db.reworks.__len__()
        db.stats['rework_perc'] = (db.reworks.__len__() / db.parts.__len__())

        # first and last part
        db.stats['first_part'] = db.first_part = (min(db.parts.index))
        db.stats['last_part'] = db.last_part = (max(db.parts.index))

        # total production time
        db.stats['total_time'] = db.total_time = (
            db.last_part.timestamp() - db.first_part.timestamp()
            )


    def find_stops(self):

        """
        Finds and bins poucher stops by length.
        
        The bins consist of Short, Medium, Long, and Extra-Long stops.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Getting stops.')

        # minimum size for each stop bin [s]
        self.ss_min = 1.2
        self.ms_min = 12
        self.ls_min = 120
        self.xls_min = 600

        # set mode to slice or full workday
        db = self.workday

        # # finds short stops
        db.shortstops = db.data.loc[
            (db.data['dt'] > self.ss_min) & (db.data['dt'] < self.ms_min)
            ].drop(['Hz','upm'], axis=1)

        # finds medium stops
        db.mediumstops = db.data.loc[
            (db.data['dt'] > self.ms_min) & (db.data['dt'] < self.ls_min)
            ].drop(['Hz','upm'], axis=1)

        # finds long stops
        db.longstops = db.data.loc[
            (db.data['dt'] > self.ls_min) & (db.data['dt'] < self.xls_min)
            ].drop(['Hz','upm'], axis=1)

        # finds extra-long stops
        db.xlongstops = db.data.loc[
            db.data['dt'] > self.xls_min
            ].drop(['Hz','upm'], axis=1)

        # combine stop bins into single dataframe
        db.stops = pd.concat(
            [db.shortstops, db.mediumstops,
                db.longstops, db.xlongstops]
            ).sort_index()

        # package stops together for passing to functions
        db.stops_binned = [
            db.shortstops, db.mediumstops,
            db.longstops, db.xlongstops
            ]


    def calculate_stop_stats(self):

        """
        Get statistics for stops for the time duration.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Getting stop stats.')

        db = self.workday
        
        # stop parameters
        db.stats[['ss_min', 'ms_min', 'ls_min', 'xls_min']] = [
            self.ss_min, self.ms_min, self.ls_min, self.xls_min
        ]
        
        # stops - occurrences
        db.stats[
            ['ss_count', 'ms_count', 'ls_count', 'xls_count']
            ] = (
                [ss_count, ms_count, ls_count, xls_count]
            ) = [
                db.shortstops.__len__(),
                db.mediumstops.__len__(),
                db.longstops.__len__(),
                db.xlongstops.__len__()
        ]

        # stops - time
        db.stats[['ss_time', 'ms_time', 'ls_time', 'xls_time']] = (
            [ss_time, ms_time, ls_time, xls_time]
        ) = [
            db.shortstops['dt'].sum(),
            db.mediumstops['dt'].sum(),
            db.longstops['dt'].sum(),
            db.xlongstops['dt'].sum()
        ]

        # stops - percentage of total time
        bins = [ss_time, ms_time, ls_time, xls_time]
        db.stats[['ss_perc', 'ms_perc', 'ls_perc', 'xls_perc']] = [
            bin/db.total_time for bin in bins
        ]

        # total stop time
        db.stats['total_stop_time'] = total_stop_time = (
            ss_time + ms_time + ls_time + xls_time
        )

        # total stop percentage
        db.stats['total_stop_perc'] = total_stop_perc = (
            total_stop_time / db.total_time
        )

        # oee availability rate
        db.stats['avail_loss'] = avail_loss = (
            total_stop_time - (ss_time + ms_time)
        )
        db.stats['oee_net_run_time'] = net_run_time = (
            db.total_time - avail_loss
        )
        db.stats['ar'] = net_run_time / db.total_time

        # oee performance rate
        ideal_run_rate = 140 / 60
        db.stats['pr'] = (
            db.parts.__len__() / net_run_time
        ) / ideal_run_rate

        # partial oee
        db.stats['oee_ar_pr_only'] = (
            db.stats['ar'] * db.stats['pr']
        )

        # total run time
        db.stats['total_run_time'] = db.total_run_time = (
            db.total_time - total_stop_time
        )

        # average rate while running
        db.stats['avg_rate_upm'] = db.parts.__len__() / (db.total_run_time / 60)

        # effective rate over entire day
        db.stats['eff_rate_upm'] = db.parts.__len__() / (db.total_time / 60)

        # total run percentage
        db.stats['total_run_perc'] = total_run_perc = (
            db.total_run_time / db.total_time
        )


    def calculate_yields_1s(self):

        """
        Counts the cumulative number of parts made 
        at each second of the DataBlock.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Getting yields.')

        db = self.workday
        db.yields = pd.DataFrame(
            index=pd.date_range(
                self.startup, self.shutdown, freq='s'
            ), 
            columns=['count', 'standard']
            )
        db.yields.at[db.yields.index[0], 'count'] = 0

        # comprehension list to determine parts made at each second of the day
        db.yields[['count', 'standard']] = [
            (
                db.parts[db.parts.index < x].__len__(), i * self.STD_RATE
                ) for i, x in enumerate(db.yields.index)
            ]

        db.yields['upm'] = 60 * db.yields['count'].diff()
        db.yields['upm_rolling5s'] = db.yields['upm'].rolling(5).mean()
        db.yields['upm_rolling30s'] = db.yields['upm'].rolling(30).mean()
        db.yields['upm_rolling60s'] = db.yields['upm'].rolling(60).mean()
        db.yields['upm_rolling120s'] = db.yields['upm'].rolling(120).mean()
        
        db.yields['upm_ideal'] = self.IDEAL_RUN_RATE


    def calculate_yields_30min(self):
        
        """
        Counts the cumulative number of parts made 
        at each half-hour of the DataBlock.
        
        """

        db = self.workday

    def workday_to_excel(self):
        
        """
        Exports all machine data to Excel file.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Exporting to .csv')

        self.rates_to_excel()
        self.stops_to_excel()
        self.stats_to_excel()
        self.yields_to_excel()


    def rates_to_excel(self):

        """
        Exports machine cycle rates to Excel file.
        
        """
        self.workday.data.to_excel(
            f'./xls/rates/{self.MACHINE_ID}/'
            f'{self.date:%Y-%m-%d}_{self.MACHINE_ID}_Poucher_Rates.xlsx'
        )


    def stops_to_excel(self):

        """
        Exports machine stops to Excel file.

        """
        self.workday.stops.to_excel(
            f'./xls/stops/{self.MACHINE_ID}/'
            f'{self.date:%Y-%m-%d}_{self.MACHINE_ID}_Poucher_Stops.xlsx'
        )


    def stats_to_excel(self):

        """
        Exports machine runtime stats to Excel file.

        """
        self.workday.stats.to_excel(
            f'./xls/stats/{self.date:%Y-%b}_'
            f'{self.MACHINE_ID}-{date}_Poucher_Stats.xlsx'
        )


        # path = (
        #     f'./xls/stats/{self.date:%Y-%b}_'
        #     f'Poucher_Stats.xlsx'
        # )

        # if not os.path.exists(path):
        #     return None
        
        # book = load_workbook(path)
        # sheetname = f'{self.MACHINE_ID}' 
        # # with pd.ExcelWriter(
        # #         path, engine='openpyxl', mode='a', if_sheet_exists='overlay'
        # #         ) as writer:
        # writer = pd.ExcelWriter(
        #     path, engine='openpyxl', mode='a', if_sheet_exists='overlay'
        #     )
        # writer.book = book
        # startrow = self.date.day
        # self.workday.stats.to_excel(
        #     writer, sheet_name=sheetname, startrow=startrow
        #     )
        # writer.save()


    def create_stats_file(self):

        """
        Creates a blank stats file if it doesn't already exist.
        
        """
        pass

    
    def yields_to_excel(self):

        """
        Exports machine yield vs. time to Excel file.

        """
        self.workday.yields.to_excel(
            f'./xls/yields/{self.MACHINE_ID}/'
            f'{self.date:%Y-%m-%d}_{self.MACHINE_ID}_Poucher_'
            f'Yield_vs_Time.xlsx'
        )


    def make_plots(self, date, mode='day'):

        """
        Generates charts of production data for a given timespan.
        
        """
        # status output to terminal
        print(f'{datetime.datetime.now()}: Making plots.')

        # figure size
        fig_size = (24,9)

        # plot figure
        fig = plt.figure(figsize=fig_size, constrained_layout=True)
        fig.set_facecolor('whitesmoke')

        # main 3 plots
        gs_main = fig.add_gridspec(
            nrows=3, ncols=1, hspace=0, 
            height_ratios=[27,2,1], left=0.15, right=0.80
        )

        # overlay to display au
        gs_overlay = fig.add_gridspec(
            nrows=3, ncols=5, wspace=0,
            width_ratios=[2,4,1,4,20], height_ratios=[2,8,13]
        )

        # set mode to slice or full workday
        if mode == 'span':
            db = self.span
            fig.suptitle(
                f'{self.name} Performance\n{db.t_start:%H:%M} - '
                f'{db.t_end:%H:%M} Workday {date:%b-%d-%y}', fontsize=16
                )
            
        elif mode == 'day':
            db = self.workday
            fig.suptitle(
                f'{self.name} Performance\nFull Workday {date:%b-%d-%y}',
                fontsize=16
                )
        else:
            raise Exception(f'Invalid mode specified.')

        # yield vs. time plot
        db.ax1 = fig.add_subplot(gs_main[0])
        self.draw_yield_plot(
            db.ax1, db.yields, db.t_start, db.t_end, self.shift_change, mode
        )

        # rate plot
        db.ax2 = fig.add_subplot(gs_main[1])
        self.draw_rate_plot(
            db.ax2, db.data, db.yields, db.stops,
            db.t_start, db.t_end, self.shift_change, mode
        )

        # stops plot
        db.ax3 = fig.add_subplot(gs_main[2])
        self.draw_stops_plot(
            db.ax3, db.data, db.parts, db.stops_binned,
            db.t_start, db.t_end, self.shift_change, mode
        )

        fig.savefig(
            f'./charts/{date}_{self.MACHINE_ID}_'
            f'performance({NOW_TS}).png',
            dpi=1200
        )


    def draw_yield_plot(
        self, ax, yields, 
        t_start, t_end, shift_change, mode
        ):

        """
        Draws the plot displaying yield over time for a given dataset.
        
        """
        # set mode to slice or full workday
        if mode == 'span':
            pass
        elif mode == 'day':
            [ymin, ymax] = [0, 120_000]
        else:
            raise Exception(f'Invalid mode specified: {mode}')

        # x-axis range
        [xmin, xmax] = [t_start, t_end]

        plt.axes = ax

        # plot style
        plt.ylabel('Yield', rotation=90, labelpad=10, fontsize=14)
        plt.axes.set_facecolor('lightgrey')

        # plot grid
        plt.grid(color='black', ls='--', lw=0.5, alpha=0.8)

        # defines plot limits
        plt.xlim([xmin, xmax])
        plt.ylim([ymin, ymax])

        # standard yield plot
        plt.fill_between(
            yields.index, 0, yields['standard'],
            lw=0.01, color='dimgrey', alpha=1.0
            )
        plt.fill_between(
            yields.index, 0, yields['standard'],
            lw=0.01, color='red', alpha=0.40
            )
        
        # actual yield plot (with black outline)
        plt.fill_between(yields.index, 0, yields['count'], lw=0.01, color='xkcd:cerulean')
        plt.plot(yields.index, yields['count'], 'black', lw=0.05)

        # standard yield line drawn over actual yield
        plt.plot(yields.index, yields['standard'], lw=0.15, color='purple')
        
        # dashed line to indicate shift change
        plt.axvline(x=shift_change, lw=1.0, color='k', linestyle='dashed')

        # Show x labels on bottom plot only
        plt.axes.label_outer()

        # y-axis formatting
        plt.axes.tick_params(axis='y', which='major', labelsize=7)

        plt.axes.draw


    def draw_rate_plot(
        self, ax, data, yields, stops,
        t_start, t_end, shift_change, mode
        ):

        """
        Draws the plot displaying rate over time for a given dataset.
        
        """
        # axis ranges
        [xmin, xmax, ymin, ymax] = [t_start, t_end, 60, 140]

        plt.axes = ax
        plt.ylabel('Rate\n[upm]', rotation=90,  labelpad=20, fontsize=10)
        plt.axes.set_facecolor('tab:orange')

        # defines plot limits
        plt.xlim([xmin, xmax])
        plt.ylim([ymin, ymax])

        # y-axis ticks
        plt.yticks([60, 100, 140])

        # draw plot of rate
        plt.fill_between(
            yields.index, yields['upm_rolling60s'], lw=0.01, color='xkcd:cerulean'
        )

        # plot grid
        plt.grid(color='black', ls='--', lw=0.5, alpha=0.8)

        # draws rectangles to limits of plot
        plt.axvspan(
            t_start, data[data['part'] == 1].index[0], 
            color='lightgrey', lw=0.01, alpha=1.0
            )
        plt.axvspan(
            data[data['part'] == 1].index[-1], t_end,
            color='lightgrey', lw=0.01, alpha=1.0
            )

        # draws rectangles over stops
        self.draw_x_rects(ax, stops, 'lightgrey', 0.01, 1.0)

        # dashed line to indicate shift change
        plt.axvline(x=shift_change, lw=1.0, color='k', linestyle='dashed')

        # show x labels on bottom plot only
        plt.axes.label_outer()

        # y-axis formatting
        plt.axes.tick_params(axis='y', which='major', labelsize=7)

        plt.axes.draw


    def draw_stops_plot(
        self, ax, data, parts, stops_binned,
        t_start, t_end, shift_change, mode
        ):

        """
        Draws the plot displaying machine stops over time for a given dataset.
        
        """
        # axis ranges
        [xmin, xmax, ymin, ymax] = [t_start, t_end, 0, 1]
        [short_stops, medium_stops, long_stops, xlong_stops] = stops_binned

        # add plot style
        plt.axes = ax
        plt.axes.set_facecolor('xkcd:true green')
        plt.ylabel('Stops', rotation=90, labelpad=47, fontsize=10)

        # defines axis limits
        plt.xlim([xmin, xmax])
        plt.ylim([ymin, ymax])

        # plot grid
        plt.grid(color='black', ls='--', lw=0.5, alpha=0.8)

        # formats datetime axis
        xformat = mdates.DateFormatter('%H:%M\n%b-%d')
        plt.axes.xaxis.set_major_formatter(xformat)

        # draws rectangles from first and last cycle
        # to the limits of the x-axis
        plt.axvspan(
            t_start, data.index[0], color='lightgrey', lw=0.01, alpha=1.0
            )
        plt.axvspan(
            data.index[-1], t_end, color='lightgrey', lw=0.01, alpha=1.0
            )
        plt.axvspan(
            data.index[0], parts.index[0], lw=0.01, color='dimgrey'
            )
        plt.axvspan(
            parts.index[-1], data.index[-1], lw=0.01, color='dimgrey'
            )

        # short stops rectangles
        self.draw_x_rects(ax, short_stops, 'xkcd:yellowish', 0.01, 1.0)

        # medium stops rectangles
        self.draw_x_rects(ax, medium_stops, 'tab:orange', 0.01, 1.0)

        # long stops rectangles
        self.draw_x_rects(ax, long_stops, 'tab:red', 0.01, 1.0)

        # extra long stops rectangles
        self.draw_x_rects(ax, xlong_stops, 'darkred', 0.01, 1.0)

        # hides y-axis labels
        plt.axes.get_yaxis().set_ticks([])

        # dashed line to indicate shift change
        plt.axvline(x=shift_change, lw=1.0, color='k', linestyle='dashed')

        # x-axis formatting
        plt.axes.tick_params(axis='x', which='major', labelsize=7)

        # show x labels on bottom plot only
        plt.axes.label_outer()

        plt.axes.draw


    def draw_x_rects(self, ax, stops, color, line_width, alpha_value):

        """
        Draw rectangles on the given plot for each stop.
        
        """
        plt.axes = ax

        # calculate rectangle coordinates (min, max)
        rect_coords = [
            (
                (stops.index[i] - datetime.timedelta(seconds=(dt))),
                stops.index[i]
            ) for i, dt in enumerate(stops['dt'])
        ]

        # draw the rectangles
        [
            plt.axvspan(
                x[0], x[1], color=color, lw=line_width, alpha=alpha_value
                ) for i, x in enumerate(rect_coords)
        ]


class DataBlock:
    
    """
    Object consisting of a block of data for a given process and Work Day.

    The basic unit of reporting, can be any length. 
    
    """
    def __init__(self, machine_id, process_id, t_start, t_end, shift_change):
        self.machine_id = machine_id
        self.process_id = process_id
        self.t_start = t_start
        self.t_end = t_end
        self.t_start_str = t_start.strftime('%Y%m%d_%H%M%S')
        self.t_end_str = t_end.strftime('%Y%m%d_%H%M%S')


    def get_data(self):

        """
        Loads the process data for the DataBlock.
        
        """
        # prevents accidental data loss if machine is running
        # need to write an override, for now it just blocks the query entirely
        if False:#((self.t_start >= datetime.datetime.combine(
            # datetime.datetime.today().date(), datetime.time(0)
            # )) or self.t_end >= datetime.datetime.combine(
            # datetime.datetime.today().date(), datetime.time(0)
            # )):
            raise Exception(
                f'Cannot acquire data while machine is running,'
                f'this is a safeguard.'
                )
        else:
            self.data = Machine.get_process_data(
                self.machine_id, self.process_id,
                self.t_start, self.t_end
            )


class Shift:
    
    """
    Object containing production info for a given shift.
    
    """
    def __init__(self, shift_id, workday, lines):
        self.shift_id = shift_id
        self.workday = workday

        with open('shift_times.json', 'r') as reader:
            # load the json containing shift info
            times_dict = json.load(reader)

        times = times_dict.get(self.shift_id)
        
        self.shiftstart = times.get('start')
        self.shiftend = times.get('end')

        # self.break1 = times.get('break1')
        # self.break2 = times.get('break2')
        # self.lunch = times.get('lunch')


    # def get_data(self, line, process_id)


class ProductionDay:

    """
    Object containing production info for a given work day.
    
    A Work Day spans from 3AM of the given date to 3AM of the following date.
    
    """
    def __init__(self, date, lines, startup, shutdown, shift_change):
        self.date = date
        self.lines = lines

        self.t_start = (
            datetime.datetime.combine(date, datetime.time(3))
        )

        self.t_end = (
            self.t_start + datetime.timedelta(days=1)
            )

        # shift start and end times
        self.startup = startup
        self.shutdown = shutdown

        # shift change time
        self.shift_change = shift_change

    def poucher_data(self):

        """
        Processes the iTrak poucher data for the Work Day.
        
        """
        for line in self.lines:
            # instantiate an iTrakLine object and load the poucher data
            line = iTrak(line)
            line.poucher.load_workday(
                self.date, self.startup, self.shutdown, self.shift_change
            )
            line.poucher.calculate_workday_stats()
            line.poucher.calculate_yields_1s()
            line.poucher.workday_to_excel()
            # line.poucher.slice_hours()
            line.poucher.make_plots(self.date)


    def create_shifts(self):

        """
        Creates workshifts based on 'shift_times.json'.
        
        """
        self.firstshift = Shift('first')
        self.secondshift = Shift('second')


###########
print(f'\n\n{datetime.datetime.now()}: Initiated.')
start_date = datetime.date(2022, 11, 16)
end_date = datetime.date(2022, 11, 16)
dates = pd.date_range(start_date, end_date, freq='d')
lines = ['Line 7', 'Line 8']

for date in dates:
    date = date.date()
    print(f'\n{date}')
    startup = datetime.datetime.combine(
        date, datetime.time(5, 0, 0, 0)
    )
    shutdown = datetime.datetime.combine(
        date + datetime.timedelta(days=1), datetime.time(1, 0, 0, 0)
    )
    print(f'{startup} - {shutdown}')

    # shift change time
    shift_change = datetime.datetime.combine(
        date, datetime.time(14, 30)
    )


    w = ProductionDay(date, lines, startup, shutdown, shift_change)
    w.poucher_data()
    print(f'\n\n{datetime.datetime.now()}: Day complete.')