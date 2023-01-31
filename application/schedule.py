from __future__ import annotations

import math
from datetime import date
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd
from sqlalchemy import and_, or_

from application import db
from application.models import WorkOrders, WorkWeeks


def current_hour() -> dt:
    return dt.combine(dt.now().date(), time(dt.now().hour))


class Schedule:
    """Schedule for a single production week.

    Returns:
        Instance of Schedule class.
    """
    _year_week_format = '%G-%V'

    def __init__(self: Schedule, year_week: str) -> None:
        self.year_week = year_week
        self._init_week()

    def _init_week(self) -> None:
        """Initializes database info for the week.
        """
        self._week = self._get_work_week()
        self._week_config()
        self._init_dates()

    def _get_work_week(self: Schedule) -> WorkWeeks:
        try:
            week_ = db.get_or_404(WorkWeeks, self.year_week)
        except:
            week_ = WorkWeeks(year_week=self.year_week)
            db.session.add(week_)
            db.session.commit()
        return week_

    def _week_config(self: Schedule) -> None:
        self._production_days = self._get_days()
        self.workday_start = time(self._week.workday_start_time)
        self.workday_end = time(self._week.workday_end_time)
        self.lines = self._get_lines()

    def _get_days(self: Schedule) -> list[int]:
        """Returns a list of integers representing the days scheduled
        for the given week. 

        Returns:
            list[int]: List of days scheduled. 0 = Monday, 6 = Sunday.
        """
        bin_list_str = list(bin(self._week.prod_days))[2:]
        bin_list_int = list(map(int, bin_list_str))

        days = range(7) # 0 - 6
        _days = []

        for day, scheduled in zip(days, bin_list_int):
            if scheduled:
                _days.append(day) 
        return _days

    def _get_lines(self: Schedule) -> list[int]:
        """Returns list of integers representing the lines (5-12)
        in production for the given week.

        Returns:
            list[int]: Line numbers available for production.
        """
        bin_list_str = list(bin(self._week.lines))[2:]
        bin_list_int = list(map(int, bin_list_str))
        
        lines = range(5, 13) # 5 - 12
        _lines = []

        for line, scheduled in zip(lines, bin_list_int):
            if scheduled:
                _lines.append(line)
        return _lines

    def _init_dates(self: Schedule) -> None:
        self.start_datetime = dt.strptime(
            f'{self.year_week}-Mon',
            f'{Schedule._year_week_format}-%a'
            )
        self.end_date = self.start_datetime + timedelta(days=6)
        self.end_datetime = dt.combine(self.end_date, time().max)
        self.dates = pd.date_range(
            self.start_datetime, self.end_datetime,
            freq='d'
            )
        self._set_schedule_type()

    def _set_schedule_type(self: Schedule) -> None:
        if self.start_datetime < dt.now() < self.end_datetime:
            self.schedule_type = 'current'
        elif self.end_datetime < dt.now():
            self.schedule_type = 'past'
        elif self.start_datetime > dt.now():
            self.schedule_type = 'future'
        else:
            raise Exception('Error setting week type (Current/Past/Future).')


    def set_hours(self: Schedule, workday_start: int, workday_end: int) -> None:
        self._week.workday_start_time = time(workday_start)
        self._week.workday_end_time = time(workday_end)
        db.session.commit()
        self.refresh()

    def set_days(self: Schedule, days: int) -> None:
        self._week.prod_days = days
        db.session.commit()
        self.refresh()

    @property
    def _index(self: Schedule) -> pd.DatetimeIndex:
        try:
            return self.index_
        except AttributeError:
            self.index_ = pd.date_range(
                start=self.start_datetime, end=self.end_datetime, freq='h'
                )
            return self.index_

    @property
    def schedule_frame(self: Schedule) -> pd.DataFrame:
        try:
            return self._schedule_frame
        except AttributeError:
            self._schedule_frame = pd.DataFrame(
                index=self.hours.index[self.hours == True],
                columns=self.lines
                )
            return self._schedule_frame

    @property
    def hours(self: Schedule) -> pd.Series:
        try:
            return self._hours
        except AttributeError:
            self.hour_mask
            self.day_mask
            self._hours = self._day_mask & self._hour_mask
            return self._hours

    @property
    def hour_mask(self: Schedule) -> pd.Series:
        try:
            return self._hour_mask
        except AttributeError:
            self._hour_mask = pd.Series(False, index=self._index)
            last_hour = self.workday_end.replace(hour=self.workday_end.hour-1)
            self._hour_mask.loc[self.workday_start:last_hour] = True
            return self._hour_mask

    @property
    def day_mask(self: Schedule) -> pd.Series:
        try:
            return self._day_mask
        except AttributeError:
            self._day_mask = pd.Series(False, index=self._index)
            for _day in self._production_days:
                self._day_mask[self._index.to_series().dt.weekday == _day] = True
            return self._day_mask

    @property
    def work_orders(self: Schedule) -> list[WorkOrders]:
        def _get_work_orders() -> list[WorkOrders]:
            return db.session.execute(db.select(WorkOrders).where(
                    and_(
                        WorkOrders.end_datetime >= self.start_datetime,
                        WorkOrders.start_datetime < self.end_datetime
                        )
                    ).order_by(WorkOrders.start_datetime.desc())).scalars()
        try:
            return self._work_orders
        except AttributeError:
            self._work_orders = _get_work_orders()
            return self._work_orders

    def _map_work_order(self: Schedule, work_order: WorkOrders) -> None:
        pass # map work orders to css grid values

    @property
    def prior_week(self: Schedule) -> str:
        try:
            return self._prior_year_week
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week = dt.strftime(
                prior_week_start, Schedule._year_week_format
                )
            return self._prior_year_week

    @property
    def next_week(self: Schedule) -> str:
        try:
            return self._next_year_week
        except AttributeError:
            next_week_start = self.start_datetime + timedelta(days=7)
            self._next_year_week = dt.strftime(
                next_week_start, Schedule._year_week_format
                )
            return self._next_year_week

    def refresh(self: Schedule) -> None:
        self.__init__(self.year_week)

    @staticmethod
    def parking_lot() -> list[WorkOrders]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return WorkOrders.parking_lot()
        
    @staticmethod
    def pouching() -> list[WorkOrders]:
        """
        Returns database query for all 'Pouching' jobs.
        """
        return WorkOrders.pouching()
    
    @staticmethod
    def queued() -> list[WorkOrders]:
        """Returns db query for all Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return WorkOrders.queued()

    @staticmethod
    def scheduled_jobs() -> list[WorkOrders]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return WorkOrders.scheduled_jobs()

    @staticmethod
    def week_hour(datetime_: dt) -> int:
        """
        Returns integer representing the grid column for the
        given datetime hour. Ranges from 0 - 167, with 0 representing
        12AM - 1AM Monday morning.
        """
        return (datetime_.weekday() * 24) + datetime_.hour

    def __str__(self: Schedule) -> str:
        return (
            f'{self.start_datetime:%b %d, %Y} - '
            f'{self.end_datetime:%b %d, %Y}'
            )


class CurrentSchedule(Schedule):

    def __init__(self: CurrentSchedule) -> None:
        year_week = dt.strftime(dt.now(), Schedule._year_week_format)
        super().__init__(year_week=year_week)
        self._update_work_orders()

    @property
    def current_week_hour(self: CurrentSchedule) -> int:
        self._current_week_hour = self.week_hour(dt.now())
        return self._current_week_hour

    @property
    def current_hour(self: CurrentSchedule) -> time:
        return current_hour()

    def _multi_week_frame(self: CurrentSchedule) -> pd.DataFrame:
        _next_week_obj = Schedule(self.next_week)
        _multi = pd.concat(
            [self.schedule_frame, _next_week_obj.schedule_frame]
            )
        _frame_after_next = Schedule(_next_week_obj.next_week).schedule_frame
        _multi = pd.concat([_multi, _frame_after_next])

        return _multi
    
    def _update_work_orders(self: CurrentSchedule) -> None:
        self.current_week_hour
        self._update_pouching()
            
    def _update_pouching(self: CurrentSchedule) -> None:
        for work_order in self.pouching():
            print(work_order.lot_number)
            self._update_work_order(work_order, self._multi_week_frame())
            
    def _update_queued(self: CurrentSchedule) -> None:
        pass

    def _update_work_order(
            self: Schedule,
            work_order: WorkOrders, _schedule_frame: pd.DataFrame
        ) -> None:
        # self.update_pouched_qty()
        line = work_order.line
        print(line)
        _frame = self._crop_frame(_schedule_frame, line)
        work_order, _frame = WorkOrders.update_work_order(
            work_order=work_order, _frame=_frame
            )
        print(_frame)

        _schedule_frame[work_order.line] = _frame

        if work_order.status == 'Queued':
            pass # update queued work orders start/completion times
    
    def _crop_frame(
            self: CurrentSchedule,
            _schedule_frame: pd.DataFrame, line: int
            ) -> pd.DataFrame:
        
        curr_hour = dt.now().replace(minute=0, microsecond=0)
        
        _frame = _schedule_frame.loc[curr_hour:, line]
        if _frame.index[0] > self.end_datetime:
            # next schedule hour is not in the current week
            # need to fix
            raise Exception('Needs to fix scheduling next week.')

        return _frame