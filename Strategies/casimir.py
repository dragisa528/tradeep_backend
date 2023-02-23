# Start hyperopt with the following command:
# freqtrade hyperopt --config config.json --hyperopt-loss SharpeHyperOptLoss --strategy RsiStrat -e 500 --spaces  buy sell --random-state 8711

# --- Do not remove these libs ---
from operator import truediv
import numpy as np  # noqa
import pandas as pd  # noqa
from functools import reduce
from pandas import DataFrame


from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,IStrategy, IntParameter)

# --- Add your lib to import here ---
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

# --- Generic strategy settings ---

class casimir(IStrategy):
    INTERFACE_VERSION = 3
    # Determine timeframe and # of candles before strategysignals becomes valid
    timeframe = '1d'
    startup_candle_count: int = 25
    # Determine roi take profit and stop loss points
    minimal_roi = {
        "0": 0.03
    }

    stoploss = -0.15
    trailing_stop = False
    use_exit_signal = False
    exit_profit_only = False
    exit_profit_offset = 0.0
    ignore_roi_if_entry_signal = False
    trailing_stop_positive: 0.27
    trailing_stop_positive_offset: 0.29000000000000004
    trailing_only_offset_is_reached: False

    # Protection hyperspace params:

    @property
    def protections(self):
        prot = []

        cooldown_lookback: 46
        stop_duration: 20
        use_stop_protection: True

        return prot


        # --- Used indicators of strategy code ----

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        # mfi index voor de koop en verkoop

        dataframe['mfi'] = ta.MFI(dataframe, timeperiod=14)
        
        # EMA voor de strategy
        dataframe['ema12'] = ta.EMA(dataframe, timeperiod=12)



        return dataframe



# --- Buy settings ---

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['mfi'] > 50) &
                (dataframe['mfi'] > dataframe['mfi'].shift(1)) &
                (dataframe['volume'] > dataframe['volume'].shift(1))
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['mfi'] < 50) 
                    
            ),
            'exit_long'] = 1

        return dataframe