from datetime import date
from datetime import datetime as dt
from datetime import time

import matplotlib.pyplot as plt
import pandas as pd

from cameras import ProductInspectCamera, ProductInspectData
from datafiles import DataBlock, ProcessData
from machines import iTrakLine
from workday import WorkDay


def main():

    start_date = date(2022, 10, 12)
    end_date = date(2022, 10, 13)
    start = dt.combine(start_date, time(6))
    end = dt.combine(end_date, time(6))

    line = iTrakLine(8)

    pd.set_option('display.max_rows', 100)

    db = line.poucher.product_inspect.load_data(start, end)

    db.stats()

    print(db)

    prod_ = db.productivity()

    new_db = db.slice(dt.combine(start_date, time(11)), dt.combine(start_date, time(12)))

    plt.plot(prod_.index, prod_['rate_Hz'].rolling(60).mean() * 60)
    plt.draw()
    plt.show()


if __name__ == '__main__':
    main()