from copy import deepcopy
from datetime import date
from datetime import datetime as dt
from datetime import time

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axis import Axis
from pouching import iTrak


def main():

    start_date = date(2022, 10, 12)
    end_date = date(2022, 10, 13)
    start = dt.combine(start_date, time(9))
    end = dt.combine(end_date, time(10))

    # new_start = dt.combine(start_date, time(9))
    # new_end = dt.combine(start_date, time(14))

    line = iTrak(8)

    pd.set_option('display.max_rows', 100)

    data_block_ = line.product_inspect.new_block(start, end)

    # print(line.product_inspect.cached_data.items())s

    # print(line.product_inspect.cached_data[start])

    data_block_.all_stats
    _ = data_block_.productivity

    data_block_.stats_to_xls()
    data_block_.stops_to_xls()
    data_block_.prod_to_xls()

    """
    OLD_VS_NEW

    t0 = dt.now()
    db_slow = deepcopy(db)

    df = pd.DataFrame(
            index=pd.date_range(
                db_slow.first_cycle, db_slow.last_cycle, freq='s'
            ), 
            columns=['count', 'standard']
            )
    df.at[df.index[0], 'count'] = 0

    df[['count', 'standard']] = [
            (
                db.parts[db.parts.index < x].__len__(), i * (140/60)
                ) for i, x in enumerate(df.index)
            ]
    tf = dt.now()
    print(f'\n\nSlow method finished in {tf - t0}')
    """

    # plt.plot(prod_.index, prod_['rate_Hz'].rolling(30).mean() * 60)
    # plt.draw()
    # # plt.show()
    # new_db = line.product_inspect.new_block(new_start, new_end)
    # # print(new_db)
    # new_db.all_stats
    # new_prod_ = new_db.productivity

    # winsize = 60

    # x = prod_.index
    # y = prod_['rate_Hz'].rolling(winsize).mean().fillna(0).values * 60
    # y_norm = y / max(y)

    # y_0 = np.zeros((len(y), 1)).flatten()

    # fig = plt.figure(figsize=(8,4), constrained_layout=True)

    # ax = fig.add_subplot()
    # plt.axes = ax

    # ax.set_facecolor('lightgrey')

    # xformat = mdates.DateFormatter('%H:%M\n%b-%d')
    # plt.axes.xaxis.set_major_formatter(xformat)

    # [plt.axvline(
    #     _, 0, 1, color='tab:blue', alpha=y_norm[i], lw=0.20
    #     ) for i, _ in enumerate(x)]

    # plt.fill_between(prod_.index, y_0, y, color='tab:blue', lw=.25)

    # plt.axes.draw
    # plt.show()


if __name__ == '__main__':
    main()
