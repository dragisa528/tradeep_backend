
from pandas import DataFrame
from functools import reduce
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter

import talib.abstract as ta

class TouchEmaStrategy(IStrategy):

    timeframe = "5m"

    buy_ema_period = IntParameter(40, 100, default=60, space="buy")
    buy_bars_delay = IntParameter(60, 120, default=60, space="buy")

    sell_ema_period = IntParameter(40, 100, default=60, space="sell")
    sell_bars_delay = IntParameter(60, 120, default=60, space="sell")


    # ROI table:
    minimal_roi = {
        "0": 0.242,
        "13": 0.044,
        "51": 0.02,
        "170": 0
    }

    # Stoploss:
    stoploss = -0.271

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = False

    bars_delay_long = 0
    bars_delay_short = 0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Calculate all ema values
        for val in self.buy_ema_period.range:
            dataframe[f'ema_long_{val}'] = ta.EMA(dataframe, timeperiod=val)
            dataframe[f'bars_delay_long_{val}'] = dataframe.apply( lambda x: self._delay_bars_long(x['high'], x[f'ema_long_{val}']), axis=1 )

        for val in self.sell_ema_period.range:
            dataframe[f'ema_short_{val}'] = ta.EMA(dataframe, timeperiod=val)
            dataframe[f'bars_delay_short_{val}'] = dataframe.apply( lambda x: self._delay_bars_short(x['low'], x[f'ema_short_{val}']), axis=1 )


        return dataframe

    def _delay_bars_long(self, high, ema):
        if high < ema:
            self.bars_delay_long = self.bars_delay_long + 1
        else:
            self.bars_delay_long = 0
        return self.bars_delay_long

    def _delay_bars_short(self, low, ema):
        if low > ema:
            self.bars_delay_short = self.bars_delay_short + 1
        else:
            self.bars_delay_short = 0
        return self.bars_delay_short


    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions_long = []
        conditions_short = []

        conditions_long.append(
                dataframe['high'] > dataframe[f'ema_long_{self.buy_ema_period.value}']
            )

        # Check the dalay
        conditions_long.append(
                dataframe[f'bars_delay_long_{self.buy_ema_period.value}'].shift(1) >= self.buy_bars_delay.value
            )


        conditions_short.append(
                dataframe['low'] < dataframe[f'ema_short_{self.sell_ema_period.value}']
            )

        # Check the dalay
        conditions_short.append(
                dataframe[f'bars_delay_short_{self.sell_ema_period.value}'].shift(1) >= self.sell_bars_delay.value
            )

        dataframe.loc[
            (
                reduce(lambda x, y: x & y, conditions_long)
            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                reduce(lambda x, y: x & y, conditions_short)
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return super().populate_exit_trend(dataframe, metadata)
