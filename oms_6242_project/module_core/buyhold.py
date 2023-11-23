import pandas as pd
from module_core.core import BTCore
from module_core.container.portfolio import Portfolio
from module_core.container.stock import Stock
from module_datalayer.reader import get_dbreader, DbReader
from module_core.container.BackTestInfo import NotionalInfo, PerformanceInfo

DB_PATH = "../module_datalayer/resource/db/backtest_db"

class BuyHoldBT(BTCore):

    def __init__(self, start_date: str, end_date: str, path: str, df_portfolio: pd.DataFrame):
        self.start_date = start_date
        self.end_date = end_date
        self.__path = path
        self.__df_portfolio = df_portfolio
        super(BuyHoldBT, self).__init__(start_date)

    def run(self):
        """
        This is the run function to track pnl for each stock in the portfolio
        :return:
        """
        df_portfolio = self.__df_portfolio
        path = self.__path
        db_reader = get_dbreader(path)
        start_date = self.start_date
        end_date = self.end_date
        portfolio = self.build(df_portfolio=df_portfolio, start_date=start_date, db_reader=db_reader)
        dates = pd.bdate_range(start=start_date, end=end_date)
        for date in dates:
            trade_date = str(date.date())
            portfolio = self.update(portfolio=portfolio, date=trade_date, db_reader=db_reader)

    def build(self, df_portfolio: pd.DataFrame, start_date: str, db_reader: DbReader) -> Portfolio:
        """

        :param df_portfolio:
        :param start_date:
        :param db_reader:
        :return:
        """
        date = pd.Timestamp(start_date)
        portfolio = self.portfolio
        rics = df_portfolio["ric"].drop_duplicates().to_list()
        stock_price = db_reader.get_stock_price(rics=rics, start_date=start_date, end_date=start_date)
        for index, (ric, side, qty) in df_portfolio.iterrows():
            df_price = stock_price.get(ric)
            price = df_price["close"].iloc[0]
            stock = Stock(ric=ric, position=qty, price=price, trade_date=date)
            portfolio.update(stock)
        return portfolio

    def update(self, portfolio: Portfolio, date: str, db_reader: DbReader) -> Portfolio:
        """

        :param portfolio:
        :param date:
        :param db_reader:
        :return:
        """
        trade_date = pd.Timestamp(date)
        stocks = portfolio.stocks
        for ric, stock in stocks.items():
            price = db_reader.get_stock_price(rics=[ric], start_date=date, end_date=date)
            df_price = price.get(ric)
            if df_price is None:
                last_trade = stock.trades[-1]
                price = last_trade.price
                stock.update_trade(trade_date=trade_date, current_last=price, trade_qty=0)
                continue
            price = df_price["close"].iloc[0]
            stock.update_trade(trade_date=trade_date, current_last=price, trade_qty=0)
            portfolio.update(stock)
        return portfolio


def mock_portfolio() -> pd.DataFrame:
    data = {"ric": ["00001.HK", "00002.HK", "00003.HK", "00005.HK"], "side": ["buy"] * 4,
            "qty": [1000, 2000, 3000, 5000]}
    return pd.DataFrame(data=data)


def run():
    start_date = "2023-06-01" 
    end_date = "2023-06-30"
    path = DB_PATH
    df_portfolio = mock_portfolio()
    buyhold_test = BuyHoldBT(start_date=start_date, end_date=end_date, path=path, df_portfolio=df_portfolio)
    buyhold_test.run()
    portfolio = buyhold_test.portfolio
    df_stock_metric = buyhold_test.get_stock_metric(ric="00001.HK", field=PerformanceInfo.PriceChange.value)
    stocks_price_change_metric = buyhold_test.get_portfolio_metric(field=PerformanceInfo.PriceChange.value)
    notional_metric = buyhold_test.get_portfolio_metric(field=NotionalInfo.Notional.value)
    debug_point = 3


if __name__ == '__main__':
    run()
