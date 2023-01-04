from datetime import date
from datetime import datetime as dt
from datetime import time

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from matplotlib.axis import Axis

from machines import iTrak


def main():

    start_date = date(2022, 10, 12)
    end_date = date(2022, 10, 13)
    start = dt.combine(start_date, time(9))
    end = dt.combine(end_date, time(10))

    new_start = dt.combine(start_date, time(9))
    new_end = dt.combine(start_date, time(14))

    line = iTrak(8)

    pd.set_option('display.max_rows', 100)

    db = line.product_inspect.new_block(start, end)

    # print(line.product_inspect.cached_data.items())s

    # print(line.product_inspect.cached_data[start])

    # db.all_stats
    prod_ = db.productivity

    # plt.plot(prod_.index, prod_['rate_Hz'].rolling(30).mean() * 60)
    # plt.draw()
    # # plt.show()
    # new_db = line.product_inspect.new_block(new_start, new_end)
    # # print(new_db)
    # new_db.all_stats
    # new_prod_ = new_db.productivity


    winsize = 60

    x = prod_.index
    y = prod_['rate_Hz'].rolling(winsize).mean().fillna(0).values * 60
    y_norm = y / max(y)

    y_0 = np.zeros((len(y), 1)).flatten()

    fig = plt.figure(figsize=(8,4), constrained_layout=True)

    ax = fig.add_subplot()
    plt.axes = ax

    ax.set_facecolor('lightgrey')

    xformat = mdates.DateFormatter('%H:%M\n%b-%d')
    plt.axes.xaxis.set_major_formatter(xformat)

    # [plt.axvline(_, 0, 1, color='tab:blue', alpha=y_norm[i], lw=0.20) for i, _ in enumerate(x)]


    plt.fill_between(prod_.index, y_0, y, color='tab:blue', lw=.25)


    plt.axes.draw
    plt.show()


if __name__ == '__main__':
    main()