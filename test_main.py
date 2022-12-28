from datetime import date
from datetime import datetime as dt
from datetime import time

from cameras import ProductInspect
from datafiles import DataBlock, ProcessData
from machines import iTrakLine
from workday import WorkDay


def main():

    start_date = date(2022, 10, 12)
    end_date = date(2022, 10, 13)
    start = dt.combine(start_date, time(6, 0, 0))
    end = dt.combine(end_date, time(6, 0, 0))

    line = iTrakLine(8)
    
    db = line.poucher.product_inspect.load_data(start, end)

    ProductInspect.analyze_cycles(db.data)

    print(ProductInspect.stats(db.data))

    



if __name__ == '__main__':
    main()