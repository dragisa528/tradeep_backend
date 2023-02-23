# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
from this import d
from tracemalloc import start
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from sklearn.neighbors import KNeighborsClassifier
import math
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.neighbors import KNeighborsClassifier


# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class BTCStrategy003(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.005
        # "0": 0.99
        # "30": 0.0002,
        # "0": 0.005
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.99

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = '3m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the "ask_strategy" section in the config.
    exit_profit_only = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 150

    CANDLES_TO_LOOK: int = 7

    # my vars
    NDTR: int = 150
    K: int = 13
    N_CANDLES: int = 4
    NDIM = N_CANDLES * 1  # NDTR velas * 4 datos por velas

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    def ret(n, n_1):
        return (n_1 - n) / n

    live = False

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:

        without_last = df.iloc[:len(df)]
        without_pre_last = df.iloc[:len(df) - 1]

        ret_c = (df['close'] - df['close'].shift(1)) / df['close'].shift(1)
        df['ret_c'] = ret_c

        # ret_o = (df['open'] - df['close'].shift(1)) / df['open'].shift(1)
        # df['ret_o'] = ret_o

        # ret_h = (df['high'] - df['high'].shift(1)) / df['high'].shift(1)
        # df['ret_h'] = ret_h

        # ret_l = (df['low'] - df['low'].shift(1)) / df['low'].shift(1)
        # df['ret_l'] = ret_l

        if ('ret' not in df.columns):
            rets = ((without_last.shift(-1)
                    ['close'] - without_pre_last['close']) / without_pre_last['close']).values
            rets = np.array(rets[:len(rets) - 1])
        else:
            rets = df['ret'].values

        last_ret = (df['close'].iloc[len(df) - 1] - df['close'].iloc[len(df) - 2]) / \
            df['close'].iloc[len(df) - 2]
        rets = np.append(rets, np.array(last_ret))
        df['ret'] = rets
        df['ret_s'] = df['ret'].apply(lambda x: np.sign(x))

        knn = KNeighborsClassifier(n_neighbors=self.K, weights="distance")
        START_INDEX = self.NDTR + 1

        xs = []
        ys_train = []

        print(len(df), self.K + 1 + self.N_CANDLES)

        for i in np.arange(self.K + 1 + self.N_CANDLES, self.K + 1 + self.N_CANDLES + self.NDTR):
            small_df = df.iloc[i - self.N_CANDLES:i]
            x_train = np.array(small_df[['ret_c']].values).reshape(self.NDIM)
            y_train = df.iloc[i]['ret_s']
            xs.append(x_train)
            ys_train.append(y_train)

        ys_test = []
        for j in np.arange(self.K + 1 + self.NDTR + self.N_CANDLES, len(df)):
            small_df = df.iloc[j - self.N_CANDLES: j].copy(deep=True)[
                ['ret_c', 'ret_s']].reset_index(
                drop=True)
            x = np.array(small_df[['ret_c']].values).reshape(self.NDIM)
            xs.append(x)
            ys_test.append(df.iloc[j - 1]['ret_s'])

        st_x = RobustScaler()
        xs_norm = st_x.fit_transform(xs)
        # print(len(xs_norm), xs_norm)
        x_train = xs_norm[:self.NDTR]
        print('x', len(x_train), x_train)
        x_test = xs_norm[self.NDTR:]
        print('y', len(ys_train), ys_train)
        knn.fit(x_train, ys_train)

        for j in range(len(x_test)):
            prediction = -(knn.predict([x_test[j]])[0])
            df.at[j + self.K + 1 + self.NDTR + self.N_CANDLES, 'ret_p'] = prediction
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        CANDLES_TO_LOOK = self.CANDLES_TO_LOOK
        buys = [0] * CANDLES_TO_LOOK
        for i in np.arange(CANDLES_TO_LOOK, len(df)):
            small_df = df.iloc[i - CANDLES_TO_LOOK: i + 1].copy(deep=True).reset_index(drop=True)
            # ultimas CANDLES_TO_LOOK velas
            ret_sum = small_df.iloc[:CANDLES_TO_LOOK]['ret'].sum()
            prediction = small_df['ret_p'].iloc[CANDLES_TO_LOOK]
            if prediction == 1 and ret_sum < -0.001:
                # print('buy', ret_sum)
                buys.append(1)
            else:
                buys.append(0)
        df['enter_long'] = buys
        # print('entries', len(df[df['enter_long'] == 1]))
        return df

    bought = False

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        CANDLES_TO_LOOK = self.CANDLES_TO_LOOK
        sells = [0] * CANDLES_TO_LOOK
        for i in np.arange(CANDLES_TO_LOOK, len(df)):
            small_df = df.iloc[i - CANDLES_TO_LOOK: i + 1].copy(deep=True).reset_index(drop=True)
            ret_sum = small_df.iloc[:CANDLES_TO_LOOK]['ret'].sum()
            prediction = small_df['ret_p'].iloc[CANDLES_TO_LOOK]

            if not self.bought:
                if prediction == 1:
                    self.bought = True
                    # print('sell', ret_sum)
                    sells.append(0)
                else:
                    sells.append(0)
            else:
                if ret_sum > 0.001:
                    self.bought = False
                    sells.append(1)
                else:
                    sells.append(0)

        df['exit_long'] = sells
        # print('exit', len(df[df['exit_long'] == 1]))

        return df
