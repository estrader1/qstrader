import pandas as pd
import pytz

from qstrader.system.rebalance.rebalance import Rebalance


class DailyRebalance(Rebalance):
    """
    Generates a list of rebalance timestamps for pre- or post-market,
    for all business days (Monday-Friday) between two dates.

    Does not take into account holiday calendars.

    All timestamps produced are set to UTC.

    Parameters
    ----------
    start_date : `pd.Timestamp`
        The starting timestamp of the rebalance range.
    end_date : `pd.Timestamp`
        The ending timestamp of the rebalance range.
    pre_market : `Boolean`, optional
        Whether to carry out the rebalance at market open/close.
    """

    def __init__(
        self,
        start_date,
        end_date,
        data_handler,
        pre_market=False
    ):
        self.start_date = start_date
        self.end_date = end_date
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
            Whether to use market open or market close
            as the rebalance time.

        Returns
        -------
        `str`
            The string representation of the market time.
        """
        return "09:30:00" if pre_market else "16:00:00" 

    def _generate_rebalances(self):

        rebalance_dates = pd.bdate_range(
            start=self.start_date, end=self.end_date
        )

        if self.data_handler.data_sources:

            longest_asset = self.data_handler.get_longest_asset()
            
            if longest_asset is None:  # Handle case where no data is loaded
                return []
            
            available_days = self.data_handler.data_sources[0].asset_bar_frames[longest_asset].index  # Use the first data frame
            # Filter rebalance_dates first
            filtered_rebalance_dates = [
                date for date in rebalance_dates if date in available_days
            ]

            # Then create rebalance_times
            rebalance_times = [
                pd.Timestamp(
                    "%s %s" % (date, self.market_time), tz='America/New_York'
                )
                for date in filtered_rebalance_dates
            ]
            return rebalance_times
        else:
            return []
