# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement 
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
from functools import reduce
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from datetime import datetime
from typing import Optional
from technical.util import resample_to_interval, resampled_merge
from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IStrategy,
    IntParameter,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta 
import freqtrade.vendor.qtpylib.indicators as qtpylib

# This class is a sample. Feel free to customize it.

class dema(IStrategy):
    
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: True

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:

        return 10

    # Trailing stoploss

    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 500

    # Optional order type mapping.

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    def informative_pairs(self):
        """
        """
        return []
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        dataframe_long = resample_to_interval(dataframe, 15)  # 240 = 4 * 60 = 4h
        df_shifted =  dataframe_long[['open','close']].shift()
        dataframe_long['ha_open'] = (df_shifted['open'] + df_shifted['close']) / 2
        dataframe_long['ha_close'] = (dataframe_long['open'] + dataframe_long['high'] + dataframe_long['low'] + dataframe_long['close']) / 4
        dataframe_long['ha_high'] = dataframe_long[['high', 'open', 'close']].max(axis=1)
        dataframe_long['ha_low'] = dataframe_long[['low', 'open', 'close']].min(axis=1) 
        dataframe_long['dema20'] = ta.DEMA(dataframe_long['ha_close'], timeperiod=20)
        dataframe_long['dema100'] = ta.DEMA(dataframe_long['ha_close'], timeperiod=100)
        
        dataframe = resampled_merge(dataframe, dataframe_long, fill_na=True)
        dataframe.drop(columns=['resample_15_ha_close','resample_15_ha_open', 'resample_15_ha_low','resample_15_ha_high', 'resample_15_high', 'resample_15_low', 'resample_15_close', 'resample_15_open', 'resample_15_volume', 'resample_15_date'],axis = 1, inplace = True)
        dataframe['ha_close_5m'] = (dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['fake_dema20'] = ( 2 * dataframe['resample_15_dema20']) - ((dataframe['ha_close_5m'] * 1/8 ) + (dataframe['resample_15_dema20'] * (1 - (1/8))))
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        dataframe.loc[
            (   
                (qtpylib.crossed_above(dataframe['fake_dema20'], dataframe['resample_15_dema100'])) & 
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            ['enter_long', 'enter_tag']] = (1, 'yukseliyooooor')
        dataframe.loc[
            (   
                (qtpylib.crossed_below(dataframe['fake_dema20'], dataframe['resample_15_dema100'])) & 
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            ['enter_short', 'enter_tag']] = (1, 'yukseliyooooor') 
        


        return dataframe
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (   (qtpylib.crossed_below(dataframe['resample_15_dema20'], dataframe['resample_15_dema100'])) &  
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            ['exit_long', 'exit_tag']] = (1, 'Dususe_gecti')
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['resample_15_dema20'], dataframe['resample_15_dema100'])) & 
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            ['exit_short', 'exit_tag']] = (1, 'yukselise_gecti')
        return dataframe
