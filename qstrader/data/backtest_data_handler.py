import numpy as np


class BacktestDataHandler(object):
    """
    """

    def __init__(
        self,
        universe,
        data_sources=None
    ):
        self.universe = universe
        self.data_sources = data_sources
        self.data_source_stats = {}  # Store start/end/length for each source
        self._calculate_data_source_stats()

    def _calculate_data_source_stats(self):
        """
        Calculates and stores start/end/length for each data source.
        """
        for ds in self.data_sources:
            for asset, df in ds.asset_bar_frames.items():
                if asset not in self.data_source_stats:
                        self.data_source_stats[asset] = {}
                self.data_source_stats[asset]['start_date'] = df.index.min()
                self.data_source_stats[asset]['end_date'] = df.index.max()
                self.data_source_stats[asset]['length'] = len(df)

    def get_longest_asset(self):
        """
        Returns the asset symbol with the longest data history.
        """
        if not self.data_source_stats:
            return None  # No data sources

        longest_asset = None
        max_length = -1

        for asset, stats in self.data_source_stats.items():
            if stats['length'] > max_length:
                max_length = stats['length']
                longest_asset = asset
        return longest_asset
    
    def get_asset_latest_bid_price(self, dt, asset_symbol):
        """
        """
        # TODO: Check for asset in Universe
        bid = np.nan
        for ds in self.data_sources:
            try:
                bid = ds.get_bid(dt, asset_symbol)
                if not np.isnan(bid):
                    return bid
            except Exception:
                bid = np.nan
        return bid

    def get_asset_latest_ask_price(self, dt, asset_symbol):
        """
        """
        # TODO: Check for asset in Universe
        ask = np.nan
        for ds in self.data_sources:
            try:
                ask = ds.get_ask(dt, asset_symbol)
                if not np.isnan(ask):
                    return ask
            except Exception:
                ask = np.nan
        return ask

    def get_asset_latest_bid_ask_price(self, dt, asset_symbol):
        """
        """
        # TODO: For the moment this is sufficient for OHLCV
        # data, which only usually provides mid prices
        # This will need to be revisited when handling intraday
        # bid/ask time series.
        # It has been added as an optimisation mechanism for
        # interday backtests.
        bid = self.get_asset_latest_bid_price(dt, asset_symbol)
        return (bid, bid)

    def get_asset_latest_mid_price(self, dt, asset_symbol):
        """
        """
        bid_ask = self.get_asset_latest_bid_ask_price(dt, asset_symbol)
        try:
            mid = (bid_ask[0] + bid_ask[1]) / 2.0
        except Exception:
            # TODO: Log this
            mid = np.nan
        return mid
    
    def get_asset_dividend(self, dt, asset_symbol):
        dividend = 0.0
        for ds in self.data_sources:
            try:
                dividend = ds.get_dividend(dt, asset_symbol)
                if not np.isnan(dividend):
                    return dividend
            except Exception:
                dividend = 0.0
        return dividend

    def get_assets_historical_range_close_price(
        self, start_dt, end_dt, asset_symbols
    ):
        """
        """
        prices_df = None
        for ds in self.data_sources:
            try:
                prices_df = ds.get_assets_historical_closes(
                    start_dt, end_dt, asset_symbols
                )
                if prices_df is not None:
                    return prices_df
            except Exception:
                raise
        return prices_df
