from pandas import DataFrame
import pandas_ta as pta
import numpy as np
from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IStrategy,
    IntParameter,
)
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class FerrariStratV1(IStrategy):
    INTERFACE_VERSION = 3

    can_short: bool = False

    minimal_roi = {"0": 100}
    stoploss = -0.99

    # Trailing stoploss
    trailing_stop = False
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.025

    # Optimal timeframe for the strategy.
    timeframe = "5m"

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Hyperoptable parameters
    # Buy Supertrend Multipliers
    buy_m1 = IntParameter(1, 10, default=3)
    buy_m2 = IntParameter(4, 15, default=5)
    buy_m3 = IntParameter(7, 20, default=10)
    # Buy Supertrend Periods
    buy_p1 = IntParameter(10, 20, default=14)
    buy_p2 = IntParameter(21, 50, default=25)
    buy_p3 = IntParameter(51, 100, default=60)

    # MACD Parameters
    buy_macd_fast = IntParameter(4, 40, default=32)  # Schnelle Periode
    buy_macd_slow = IntParameter(10, 250, default=200)  # Langsame Periode
    buy_macd_sign = IntParameter(3, 20, default=9)  # Signal Smoothing (Signal)

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30
    plot_config = {}
    plot_config["subplots"] = {
        "SUPERTRENDS": {
            f"supertrend_1_buy": {"color": "red"},
            f"supertrend_2_buy": {"color": "red"},
            f"supertrend_3_buy": {"color": "red"},
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe[f"supertrend_1_buy"] = pta.supertrend(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=self.buy_p1.value,
            multiplier=self.buy_m1.value,
        )["SUPERTd_" + str(self.buy_p1.value) + "_" + str(self.buy_m1.value) + ".0"]

        dataframe[f"supertrend_2_buy"] = pta.supertrend(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=self.buy_p2.value,
            multiplier=self.buy_m2.value,
        )["SUPERTd_" + str(self.buy_p2.value) + "_" + str(self.buy_m2.value) + ".0"]

        dataframe[f"supertrend_3_buy"] = pta.supertrend(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=self.buy_p3.value,
            multiplier=self.buy_m3.value,
        )["SUPERTd_" + str(self.buy_p3.value) + "_" + str(self.buy_m3.value) + ".0"]

        macd = pta.macd(
            dataframe["close"],
            self.buy_macd_fast.value,
            self.buy_macd_slow.value,
            self.buy_macd_sign.value,
        )
        macd_suffix = f"_{self.buy_macd_fast.value}_{self.buy_macd_slow.value}_{self.buy_macd_sign.value}"
        dataframe["macd"] = macd["MACD" + macd_suffix]
        dataframe["macd_h"] = macd["MACDh" + macd_suffix]  # macd value
        dataframe["macd_s"] = macd["MACDs" + macd_suffix]  # signal value
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe[f"supertrend_1_buy"] == 1)
                & (dataframe[f"supertrend_2_buy"] == 1)
                & (dataframe[f"supertrend_3_buy"] == 1)
                & (dataframe["volume"] > 0)
                & (dataframe["macd_h"] > dataframe["macd_s"])
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            ((dataframe[f"supertrend_3_buy"] == -1) & (dataframe["volume"] > 0)),
            "exit_long",
        ] = 1
        return dataframe
