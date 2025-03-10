# dividend/dividend_model.py
from qstrader import settings
from qstrader.execution.order import Order
from qstrader.execution.execution_algo.market_order import MarketOrderExecutionAlgorithm
from qstrader.execution.execution_handler import ExecutionHandler
import numpy as np

class DividendModel(object):
    """
    Handles dividend payments and reinvestment.

    Parameters
    ----------
    data_handler : `DataHandler`
        Used to look up dividend information.
    broker : `Broker`
        Used to execute reinvestment orders and update cash.
    portfolio_id : `str`
        The ID of the portfolio to apply dividends to.
    process_dividends : `bool`, optional
        Whether to process dividends at all. Defaults to True.
    reinvest_dividends : `bool`, optional
        Whether to reinvest dividends. Defaults to False.
    universe : `Universe`, optional.
        The universe to get assets from.
    qts : `QuantTradingSystem`, optional
        The quantitative trading system instance.
    """

    def __init__(
        self,
        data_handler,
        broker,
        portfolio_id,
        process_dividends=True,
        reinvest_dividends=False,
        universe = None,
        qts = None
    ):
        self.data_handler = data_handler
        self.broker = broker
        self.portfolio_id = portfolio_id
        self.process_dividends = process_dividends
        self.reinvest_dividends = reinvest_dividends
        self.universe = universe
        self.qts = qts  # Store the qts instance


    def __call__(self, dt, event=None, stats=None):

        if not self.process_dividends:
            return

        all_reinvest_orders = []  # List to store all reinvestment orders
        total_cash_dividend = 0.0  # Accumulate total cash dividend

        # Use a temporary dictionary to aggregate dividends for the day
        daily_dividends = {
            'date': dt,
            'dividends': [],  # List to hold individual asset dividends
            'total_cash_dividend': 0.0,
            'total_reinvested_quantity': 0,
            'event': event.event_type if event else None
        }
        # Determine if target allocations should be checked
        check_target_allocations = (
            self.qts and
            hasattr(self.qts, 'portfolio_construction_model') and
            hasattr(self.qts.portfolio_construction_model, 'recent_rebalance_dt') and
            self.qts.portfolio_construction_model.recent_rebalance_dt == dt
        )

        # Access target allocations directly from qts (if available and needed)
        target_allocations = {}
        if check_target_allocations:
            if (hasattr(self.qts.portfolio_construction_model, 'recent_target_portfolio') and
                self.qts.portfolio_construction_model.recent_target_portfolio):
                target_allocations = self.qts.portfolio_construction_model.recent_target_portfolio


        # Get current portfolio.
        current_portfolio = self.broker.get_portfolio_as_dict(self.portfolio_id)

        # First, collect all dividends and calculate reinvestment quantities
        for asset, details in current_portfolio.items():

            quantity = details['quantity']
            if quantity == 0:
                continue

            dividend = self.data_handler.get_asset_dividend(dt, asset)
            price = np.nan

            if dividend > 0.0:
                cash_dividend = dividend * quantity
                total_cash_dividend += cash_dividend  # Accumulate the total

                reinvest_quantity = 0
                if self.reinvest_dividends:
                    # Check target allocation (using the direct access)
                    should_reinvest = True

                    if check_target_allocations: #modified.
                        if asset not in target_allocations or target_allocations[asset]['quantity'] == 0:
                            should_reinvest = False

                    if should_reinvest:
                        price = self.data_handler.get_asset_latest_ask_price(dt, asset)
                        if price > 0 and not np.isnan(price):
                            reinvest_quantity = int(cash_dividend / price)
                            if reinvest_quantity > 0:
                                reinvest_order = Order(dt, asset, reinvest_quantity)
                                all_reinvest_orders.append(reinvest_order)

                # Store individual asset dividend information
                daily_dividends['dividends'].append({
                    'asset': asset,
                    'dividend': dividend,
                    'quantity': quantity,
                    'cash_dividend': cash_dividend,
                    'reinvest_price': price,
                    'reinvested_quantity': reinvest_quantity,
                })
                daily_dividends['total_reinvested_quantity'] += reinvest_quantity


        # Update the portfolio cash balance *once*
        if total_cash_dividend > 0.0:
        #    self.broker.subscribe_funds_to_portfolio(self.portfolio_id, total_cash_dividend)
        #    the above is causing an error, so updating the cash at the portfolio directly now
           self.broker.portfolios[self.portfolio_id].cash += total_cash_dividend

           daily_dividends['total_cash_dividend'] = total_cash_dividend

        # After iterating through all assets, append the aggregated info to stats
        if stats is not None:
            stats['dividends'].append(daily_dividends)

        # Execute reinvestment orders using the ExecutionHandler
        if all_reinvest_orders:
            execution_algo = MarketOrderExecutionAlgorithm()
            execution_handler = ExecutionHandler(
                self.broker,
                self.portfolio_id,
                self.universe,
                submit_orders=True,
                execution_algo=execution_algo,
                data_handler=self.data_handler
            )
            execution_handler(dt, all_reinvest_orders)