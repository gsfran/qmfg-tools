from datetime import date
from datetime import datetime as dt
from datetime import time

import matplotlib.pyplot as plt
import pandas as pd

from machines import iTrak


def main():

    start_date = date(2022, 10, 12)
    end_date = date(2022, 10, 13)
    start = dt.combine(start_date, time(6))
    end = dt.combine(end_date, time(6))

    new_start = dt.combine(start_date, time(9))
    new_end = dt.combine(start_date, time(14))

    line = iTrak(8)

    pd.set_option('display.max_rows', 100)

    db = line.product_inspect.new_block(start, end)

    # print(line.product_inspect.cached_data.items())

    # print(line.product_inspect.cached_data[start])

    db.all_stats()
    prod_ = db.productivity()

    plt.plot(prod_.index, prod_['rate_Hz'].rolling(60).mean() * 60)
    plt.draw()
    plt.show()
    print('New DataBlock')
    new_db = line.product_inspect.new_block(new_start, new_end)
    print(new_db)
    new_db.all_stats()
    new_prod_ = new_db.productivity()

    plt.plot(new_prod_.index, new_prod_['rate_Hz'].rolling(60).mean() * 60)
    plt.draw()
    plt.show()


if __name__ == '__main__':
    main()