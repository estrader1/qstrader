import pandas as pd
import pytz

from qstrader.system.rebalance.rebalance import Rebalance


class EndOfMonthRebalance(Rebalance):
    """
    Generates a list of rebalance timestamps for pre- or post-market,
    for the final calendar day of the month between the starting and
    ending dates provided.

    All timestamps produced are set to UTC.

    Parameters
    ----------
    start_dt : `pd.Timestamp`
        The starting datetime of the rebalance range.
    end_dt : `pd.Timestamp`
        The ending datetime of the rebalance range.
    pre_market : `Boolean`, optional
        Whether to carry out the rebalance at market open/close on
        the final day of the month. Defaults to False, i.e at
        market close.
    """

    def __init__(
        self,
        start_dt,
        end_dt,
        data_handler,
        pre_market=False
    ):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.data_handler = data_handler
        self.market_time = self._set_market_time(pre_market)
        self.rebalances = self._generate_rebalances()

    def _set_market_time(self, pre_market):
        """
        Determines whether to use market open or market close
        as the rebalance time.

        Parameters
        ----------
        pre_market : `Boolean`
            Whether the rebalance is carried out at market open/close.

        Returns
        -------
        `str`
            The time string used for Pandas timestamp construction.
        """
        return "09:30:00" if pre_market else "16:00:00"

    def _generate_rebalances(self):
        if self.data_handler.data_sources:

            longest_asset = self.data_handler.get_longest_asset()
            
            if longest_asset is None:
                return []
            
            available_days = self.data_handler.data_sources[0].asset_bar_frames[longest_asset].index
            
            rebalance_dates = []
            for (year, month), month_df in available_days.to_series().groupby([available_days.year, available_days.month]):
                last_day = month_df.index.max()  # Last available day of the month
                rebalance_dates.append(last_day)

            # Ensure rebalances are within start/end date range
            filtered_rebalance_dates = [
                date for date in rebalance_dates
                if self.start_dt.date() <= date.date() <= self.end_dt.date()
            ]

            rebalance_times = [
                 pd.Timestamp(
                    "%s %s" % (date, self.market_time), tz='America/New_York'
                )
                for date in filtered_rebalance_dates
            ]
            return rebalance_times
        else:
            return []
