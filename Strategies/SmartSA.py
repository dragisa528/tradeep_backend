# This is an integration of LunarCrush APIs to Freqtrade to execute spot market orders
import json
import os
import requests
from datetime import datetime

from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


def get_exchange_info():
    base_url = 'https://api.binance.com'
    endpoint = '/api/v3/exchangeInfo'

    return requests.get(base_url + endpoint).json()


def quote_symbols_list(quote='USDT'):
    symbols = get_exchange_info()['symbols']
    pairs = {s['symbol']: s for s in symbols if quote in s['symbol']}

    return pairs.keys()


def going2trade():
    data_path = os.path.join(os.getcwd(), 'lunarcrush')
    files = os.listdir(data_path)
    usdt_pairs = quote_symbols_list('USDT')
    print(usdt_pairs.__len__())
    to_trade = []
    for file in files:
        data = json.load(open(data_path + file))
        acr = data["acr"]

        if max(acr) < 1500 and min(acr) < 150 and acr[acr.__len__() - 1] < 150:
            symbol = file.split('.')[0]
            stablecoins = json.load(open('stablecoins.json'))["symbols"]
            if symbol not in stablecoins:
                pair = symbol+"USDT"
                if pair in usdt_pairs:
                    to_trade.append(pair)

            # p = data["p"]
            # dt = data["dt"]
            # plot_lunar_graph(acr, p, dt)

    print(to_trade)


class SmartSA(IStrategy):
    INTERFACE_VERSION: int = 3

    # Buy hyperspace params - None
    buy_params = {}
    # Sell hyperspace params - None
    sell_params = {}

    # ROI table - None
    minimal_roi = {}

    # Stoploss - 5%
    stoploss = -0.05

    # Trailing stop - Disabled
    trailing_stop = False
    trailing_stop_positive = 1
    trailing_stop_positive_offset = 1
    trailing_only_offset_is_reached = True

    # Timeframe is not necessary
    timeframe = "1m"
    startup_candle_count = 1

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No Indicator
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # metadata['pair'] == 'SOL/USDT'  -------  metadata['pair'] == 'ALGO/USDT'

        # going2trade()

        dataframe.loc[
            (),
            "enter_long"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No Exit
        dataframe.loc[(), 'exit_long'] = 1
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):

        # Sell any positions at a loss if they are held for more than one day.
        if current_profit < -0.3 and (current_time - trade.open_date_utc).days >= 6:
            return 'unclog'
