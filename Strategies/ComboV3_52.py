
# --- Do not remove these libs ---
from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class ComboV3(IStrategy):
    """
    author@: me_dium
    """
    INTERFACE_VERSION: int = 3

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "60":  0.01,
        "30":  0.03,
        "20":  0.04,
        "0":  0.05
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.3

    # Optimal timeframe for the strategy
    timeframe = '5m'

    buy_cci = IntParameter(low=-700, high=0, default=-50, space='buy', optimize=True)
    sell_cci = IntParameter(low=0, high=700, default=100, space='sell', optimize=True)

    # Buy hyperspace params:
    buy_params = {
        "buy_cci": -48,

        "buy_bbdelta": 7,
        "buy_closedelta": 17,
        "buy_tail": 25,
    }

    # Sell hyperspace params:
    sell_params = {
        "sell_cci": 687,
    }

    buy_closedelta = IntParameter(low=15, high=20, default=30, space='buy', optimize=True)
    buy_tail = IntParameter(low=20, high=30, default=30, space='buy', optimize=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        dataframe['cci'] = ta.CCI(dataframe)

        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=40, stds=2)
        dataframe['mid'] = bollinger['mid']
        dataframe['lower'] = bollinger['lower']
        dataframe['closedelta'] = (dataframe['close'] - dataframe['close'].shift()).abs()
        dataframe['bbdelta'] = (dataframe['mid'] - dataframe['lower']).abs()
        dataframe['tail'] = (dataframe['close'] - dataframe['low']).abs()

        bollinger2 = qtpylib.bollinger_bands(dataframe['close'], window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger2['lower']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['cci'] <= self.buy_cci.value) &

                dataframe['closedelta'].gt(dataframe['close'] * self.buy_closedelta.value / 1000) &
                dataframe['tail'].lt(dataframe['bbdelta'] * self.buy_tail.value / 1000) &
                dataframe['close'].le(dataframe['close'].shift())
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """

        return dataframe
