import pandas as pd
import pytz

from qstrader.system.rebalance.rebalance import Rebalance


class WeeklyRebalance(Rebalance):
    """
    Generates a list of rebalance timestamps for pre- or post-market,
    for a particular trading day of the week between the starting and
    ending dates provided.

    All timestamps produced are set to UTC.

    Parameters
    ----------
    start_date : `pd.Timestamp`
        The starting timestamp of the rebalance range.
    end_date : `pd.Timestamp`
        The ending timestamp of the rebalance range.
    weekday : `str`
        The three-letter string representation of the weekday
        to rebalance on once per week.
    pre_market : `Boolean`, optional
        Whether to carry out the rebalance at market open/close.
    """

    def __init__(
        self,
        start_date,
        end_date,
        weekday,
        data_handler,
        pre_market=False
    ):
        self.weekday = self._set_weekday(weekday)
        self.start_date = start_date
        self.end_date = end_date
        self.data_handler = data_handler
        self.pre_market_time = self._set_market_time(pre_market)
        self.rebalances = self._generate_rebalances()

    def _set_weekday(self, weekday):
        """
        Checks that the weekday string corresponds to
        a business weekday.

        Parameters
        ----------
        weekday : `str`
            The three-letter string representation of the weekday
            to rebalance on once per week.

        Returns
        -------
        `str`
            The uppercase three-letter string representation of the
            weekday to rebalance on once per week.
        """
        weekdays = ("MON", "TUE", "WED", "THU", "FRI")
        if weekday.upper() not in weekdays:
            raise ValueError(
                "Provided weekday keyword '%s' is not recognised "
                "or not a valid weekday." % weekday
            )
        else:
            return weekday.upper()

    def _set_market_time(self, pre_market):
        """
        Determines whether to use market open or market close
        as the rebalance time.

        Parameters
        ----------
        pre_market : `Boolean`
            Whether to use market open or market close
            as the rebalance time.

        Returns
        -------
        `str`
            The string representation of the market time.
        """
        return "09:30:00" if pre_market else "16:00:00"

    def _generate_rebalances(self):
        rebalance_dates = pd.date_range(
            start=self.start_date,
            end=self.end_date,
            freq=f'W-{self.weekday}'
        )
        if self.data_handler.data_sources:
            
            longest_asset = self.data_handler.get_longest_asset()
            
            if longest_asset is None:
                return []
            
            available_days = self.data_handler.data_sources[0].asset_bar_frames[longest_asset].index

            filtered_rebalance_dates = []
            for date in rebalance_dates:
                if date in available_days:
                    filtered_rebalance_dates.append(date)
                else:
                    # Find the next available trading day within the same week
                    next_day = date + pd.Timedelta(days=1)
                    while next_day.week == date.week and next_day <= self.end_date:
                        if next_day in available_days:
                            filtered_rebalance_dates.append(next_day)
                            break  # Important: Exit inner loop once a valid day is found
                        next_day += pd.Timedelta(days=1)
            #convert to time
            rebalance_times = [
                pd.Timestamp(
                    "%s %s" % (date, self.pre_market_time), tz='America/New_York'
                )
                for date in filtered_rebalance_dates
            ]
            return rebalance_times

        else:
            return []
