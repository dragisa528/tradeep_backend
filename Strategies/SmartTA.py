import datetime
from typing import Optional
from freqtrade.persistence import Trade

from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import numpy as np


class SmartTA(IStrategy):
    INTERFACE_VERSION: int = 3

    # Buy hyperspace params:
    buy_params = {
        "buy_m1": 4,
        "buy_m2": 7,
        "buy_m3": 1,
        "buy_p1": 8,
        "buy_p2": 9,
        "buy_p3": 8,
    }

    # Sell hyperspace params:
    sell_params = {
        "sell_m1": 1,
        "sell_m2": 3,
        "sell_m3": 6,
        "sell_p1": 16,
        "sell_p2": 18,
        "sell_p3": 18,
    }

    # ROI table:
    minimal_roi = {
        "0": 0.04,
        "1704": 0.03,
        "3712": 0.018,
        "5605": 0
    }

    # Stoploss:
    stoploss = -1

    # enable short
    can_short = True

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    timeframe = "6h"
    startup_candle_count = 18

    buy_m1 = IntParameter(1, 7, default=4)
    buy_m2 = IntParameter(1, 7, default=7)
    buy_m3 = IntParameter(1, 7, default=1)
    buy_p1 = IntParameter(7, 21, default=8)
    buy_p2 = IntParameter(7, 21, default=9)
    buy_p3 = IntParameter(7, 21, default=8)

    sell_m1 = IntParameter(1, 7, default=1)
    sell_m2 = IntParameter(1, 7, default=3)
    sell_m3 = IntParameter(1, 7, default=6)
    sell_p1 = IntParameter(7, 21, default=16)
    sell_p2 = IntParameter(7, 21, default=18)
    sell_p3 = IntParameter(7, 21, default=18)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Reverse Candle Detection (Stochastic)
        stochd = ta.STOCHF(dataframe, fastk_period=3)
        reversed_stochd = 100 - stochd
        dataframe['stochd'] = stochd.fastk * 1.3 - 15
        dataframe['stochd_re'] = reversed_stochd.fastk * 1.3 - 15

        for multiplier in self.buy_m1.range:
            for period in self.buy_p1.range:
                dataframe[f"supertrend_1_buy_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        for multiplier in self.buy_m2.range:
            for period in self.buy_p2.range:
                dataframe[f"supertrend_2_buy_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        for multiplier in self.buy_m3.range:
            for period in self.buy_p3.range:
                dataframe[f"supertrend_3_buy_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        for multiplier in self.sell_m1.range:
            for period in self.sell_p1.range:
                dataframe[f"supertrend_1_sell_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        for multiplier in self.sell_m2.range:
            for period in self.sell_p2.range:
                dataframe[f"supertrend_2_sell_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        for multiplier in self.sell_m3.range:
            for period in self.sell_p3.range:
                dataframe[f"supertrend_3_sell_{multiplier}_{period}"] = self.supertrend(dataframe, multiplier, period)["STX"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Reverse Mode
        # if metadata['pair'] == 'SOL/USDT' or metadata['pair'] == 'ALGO/USDT':

        # Forward Mode
        dataframe.loc[
            (dataframe[f"supertrend_1_buy_{self.buy_m1.value}_{self.buy_p1.value}"] == "up")
            & (dataframe[f"supertrend_2_buy_{self.buy_m2.value}_{self.buy_p2.value}"] == "up")
            & (dataframe[f"supertrend_3_buy_{self.buy_m3.value}_{self.buy_p3.value}"] == "up")
            & (dataframe['stochd'] > 85)
            & (dataframe["volume"] > 0),
            "enter_long"] = 1

        dataframe.loc[
            (dataframe[f"supertrend_1_buy_{self.buy_m1.value}_{self.buy_p1.value}"] == "down")
            & (dataframe[f"supertrend_2_buy_{self.buy_m2.value}_{self.buy_p2.value}"] == "down")
            & (dataframe[f"supertrend_3_buy_{self.buy_m3.value}_{self.buy_p3.value}"] == "down")
            & (dataframe['stochd_re'] > 85)
            & (dataframe["volume"] > 0),
            "enter_short"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            # (dataframe[f"supertrend_1_sell_{self.sell_m1.value}_{self.sell_p1.value}"] == "down")
            (dataframe[f"supertrend_2_sell_{self.sell_m2.value}_{self.sell_p2.value}"] == "down"),
            # & (dataframe[f"supertrend_3_sell_{self.sell_m3.value}_{self.sell_p3.value}"] == "down"),
            "exit_long"] = 1

        dataframe.loc[
            # (dataframe[f"supertrend_1_sell_{self.sell_m1.value}_{self.sell_p1.value}"] == "up")
            (dataframe[f"supertrend_2_sell_{self.sell_m2.value}_{self.sell_p2.value}"] == "up"),
            # & (dataframe[f"supertrend_3_sell_{self.sell_m3.value}_{self.sell_p3.value}"] == "up"),
            "exit_short"] = 1

        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):

        # Sell any positions at a loss if they are held for more than one day.
        if current_profit < -0.3 and (current_time - trade.open_date_utc).days >= 6:
            return 'unclog'

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:

        return 1.0

    @staticmethod
    def supertrend(dataframe: DataFrame, multiplier, period):
        df = dataframe.copy()

        df["TR"] = ta.TRANGE(df)
        df["ATR"] = ta.SMA(df["TR"], period)

        st = "ST_" + str(period) + "_" + str(multiplier)
        stx = "STX_" + str(period) + "_" + str(multiplier)

        # Compute basic upper and lower bands
        df["basic_ub"] = (df["high"] + df["low"]) / 2 + multiplier * df["ATR"]
        df["basic_lb"] = (df["high"] + df["low"]) / 2 - multiplier * df["ATR"]

        # Compute final upper and lower bands
        df["final_ub"] = 0.00
        df["final_lb"] = 0.00
        for i in range(period, len(df)):
            df["final_ub"].iat[i] = (
                df["basic_ub"].iat[i]
                if df["basic_ub"].iat[i] < df["final_ub"].iat[i - 1] or df["close"].iat[i - 1] > df["final_ub"].iat[i - 1]
                else df["final_ub"].iat[i - 1]
            )
            df["final_lb"].iat[i] = (
                df["basic_lb"].iat[i]
                if df["basic_lb"].iat[i] > df["final_lb"].iat[i - 1] or df["close"].iat[i - 1] < df["final_lb"].iat[i - 1]
                else df["final_lb"].iat[i - 1]
            )

        # Set the Supertrend value
        df[st] = 0.00
        for i in range(period, len(df)):
            df[st].iat[i] = (
                df["final_ub"].iat[i]
                if df[st].iat[i - 1] == df["final_ub"].iat[i - 1] and df["close"].iat[i] <= df["final_ub"].iat[i]
                else df["final_lb"].iat[i]
                if df[st].iat[i - 1] == df["final_ub"].iat[i - 1] and df["close"].iat[i] > df["final_ub"].iat[i]
                else df["final_lb"].iat[i]
                if df[st].iat[i - 1] == df["final_lb"].iat[i - 1] and df["close"].iat[i] >= df["final_lb"].iat[i]
                else df["final_ub"].iat[i]
                if df[st].iat[i - 1] == df["final_lb"].iat[i - 1] and df["close"].iat[i] < df["final_lb"].iat[i]
                else 0.00
            )
        # Mark the trend direction up/down
        df[stx] = np.where((df[st] > 0.00), np.where((df["close"] < df[st]), "down", "up"), np.NaN)

        # Remove basic and final bands from the columns
        df.drop(["basic_ub", "basic_lb", "final_ub", "final_lb"], inplace=True, axis=1)

        df.fillna(0, inplace=True)

        return DataFrame(index=df.index, data={"ST": df[st], "STX": df[stx]})
