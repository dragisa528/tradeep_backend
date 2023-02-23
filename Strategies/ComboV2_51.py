
# --- Do not remove these libs ---
from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
from pandas import DataFrame, Series, DatetimeIndex, merge
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class ComboV2(IStrategy):
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

        dataframe['cci_two'] = ta.CCI(dataframe, timeperiod=34)
        dataframe['mfi'] = ta.MFI(dataframe)
        dataframe = self.resample(dataframe, self.timeframe, 5)

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
                dataframe['close'].le(dataframe['close'].shift()) &

                (dataframe['close'] <= 0.98 * dataframe['bb_lowerband']) &

                (dataframe['volume'] < (dataframe['volume'].rolling(window=30).mean().shift(1) * 20)) &

                (dataframe['cci_two'] < -100) &
                (dataframe['mfi'] < 25) &
                (dataframe['resample_medium'] > dataframe['resample_short']) &
                (dataframe['resample_long'] < dataframe['close'])

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

    def chaikin_mf(self, df, periods=20):
        close = df['close']
        low = df['low']
        high = df['high']
        volume = df['volume']

        mfv = ((close - low) - (high - close)) / (high - low)
        mfv = mfv.fillna(0.0)  # float division by zero
        mfv *= volume
        cmf = mfv.rolling(periods).sum() / volume.rolling(periods).sum()

        return Series(cmf, name='cmf')

    def resample(self, dataframe, interval, factor):
        # defines the reinforcement logic
        # resampled dataframe to establish if we are in an uptrend, downtrend or sideways trend
        df = dataframe.copy()
        df = df.set_index(DatetimeIndex(df['date']))
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }
        df = df.resample(str(int(interval[:-1]) * factor) + 'min', label="right").agg(ohlc_dict)
        df['resample_sma'] = ta.SMA(df, timeperiod=100, price='close')
        df['resample_medium'] = ta.SMA(df, timeperiod=50, price='close')
        df['resample_short'] = ta.SMA(df, timeperiod=25, price='close')
        df['resample_long'] = ta.SMA(df, timeperiod=200, price='close')
        df = df.drop(columns=['open', 'high', 'low', 'close'])
        df = df.resample(interval[:-1] + 'min')
        df = df.interpolate(method='time')
        df['date'] = df.index
        df.index = range(len(df))
        dataframe = merge(dataframe, df, on='date', how='left')
        return dataframe
