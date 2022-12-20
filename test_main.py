from datetime import date

import machines
from datafiles import *
from workday import *


def main():

    production_date = date(2022, 12, 1)
    WorkDay(production_date)



if __name__ == '__main__':
    main()