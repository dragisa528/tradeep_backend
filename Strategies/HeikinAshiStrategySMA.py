# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class HeikinAshiStrategySMA(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = '4h'

    can_short: bool = False

    minimal_roi = {
        "0": 0.592,
        "629": 0.165,
        "2552": 0.058,
        "8139": 0
    }

    stoploss = -0.226

    # Trailing stop-loss
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.011
    trailing_stop_positive_offset = 0.088  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    def leverage(self, pair: str, current_rate: float,
                 proposed_leverage: 3.0, max_leverage: 5.0, side: str, **kwargs) -> float:
        return 3.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # # Chart type
        # # ------------------------------------
        # Heikin Ashi Strategy
        heikinashi = qtpylib.heikinashi(dataframe)
        dataframe['ha_open'] = heikinashi['open']
        dataframe['ha_close'] = heikinashi['close']
        dataframe['ha_high'] = heikinashi['high']
        dataframe['ha_low'] = heikinashi['low']

        # Adding Moving Average (MA)
        dataframe['ma_20'] = dataframe['ha_close'].rolling(window=20).mean()
        dataframe['ma_50'] = dataframe['ha_close'].rolling(window=50).mean()
        # dataframe['sma20'] = ta.SMA(dataframe['ha_close'], timeperiod=20)
        # dataframe['sma50'] = ta.SMA(dataframe['ha_close'], timeperiod=50)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['ha_close'].shift(1) < dataframe['ha_high'].shift(2)) &
                    (dataframe['ha_close'] > dataframe['ha_open']) &
                    (dataframe['ha_close'] > dataframe['ha_high'].shift(1)) &
                    # Confirming the buy signal with Moving Average (MA)
                    (dataframe['ha_close'] > dataframe['ma_20']) &
                    (dataframe['ma_20'] > dataframe['ma_50'])
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['ha_close'] < dataframe['ha_open']) &
                    (dataframe['ha_close'] < dataframe['ha_low'].shift(1))
            ),
            'exit_long'] = 1

        return dataframe
