from freqtrade.strategy import IntParameter, IStrategy, DecimalParameter
from pandas import DataFrame
import pandas_ta as pta
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class PenisV69(IStrategy):
    INTERFACE_VERSION: int = 3

    # ROI table:
    minimal_roi = {
        "10": 100
    }

    # Stoploss:
    stoploss = -0.1
    
    #use_exit_signal = False
    
    trailing_stop = True

    # Optimal timeframe
    timeframe = '5m'

    startup_candle_count: int = 50
    
    
    st_candles = IntParameter(3, 50, default=10, space="buy") # Wie viele Candles
    st_multipl = DecimalParameter(0.1, 10.0, default=3.0, space="buy") # Multiplikator
    
    macd_fast = IntParameter(4, 35, default=12, space="buy") # Schnelle Periode
    macd_slow = IntParameter(5, 50, default=26, space="buy") # Langsame Periode
    macd_sign = IntParameter(3, 20, default=9, space="buy") # Signal Smoothing (Signal)
    
    macd_buy = DecimalParameter(0.1, 20.0, default=1.2, space="buy") # Wie hoch macd um buy
    
    stoch_k = IntParameter(3, 40, default=14, space="buy")
    stoch_d = IntParameter(1, 20, default=3, space="buy")
    stoch_smooth_k = IntParameter(1, 20, default=3, space="buy")
    
    short_has = IntParameter(2, 5, default=3, space="buy")
    strng_has = IntParameter(5, 15, default=10, space="buy")
    
    def pivotid(s, df1: DataFrame, l, n1, n2): #n1 n2 before and after candle l
        if l-n1 < 0 or l+n2 >= len(df1): return 0
        pividlow,pividhigh=1,1
        for i in range(l-n1, l+n2+1):
            if(df1.low[l]>df1.low[i]): pividlow=0
            if(df1.high[l]<df1.high[i]): pividhigh=0
        if pividlow and pividhigh: return 3
        elif pividlow: return 1
        elif pividhigh: return 2
        else: return 0

    def populate_indicators(s, df: DataFrame, metadata: dict) -> DataFrame:
        st = pta.supertrend(df['high'], df['low'], df['close'], length=s.st_candles.value, multiplier=s.st_multipl.value)
        st_suffix = f"_{s.st_candles.value}_{s.st_multipl.value}"
        df['st'] = st['SUPERT' + st_suffix]
        df['st_d'] = st['SUPERTd' + st_suffix]
        df['st_s'] = st['SUPERTs' + st_suffix]
        df['st_l'] = st['SUPERTl' + st_suffix]

        macd = pta.macd(df['close'], s.macd_fast.value, s.macd_slow.value, s.macd_sign.value)
        macd_suffix = f"_{s.macd_fast.value}_{s.macd_slow.value}_{s.macd_sign.value}"
        df['macd'] = macd['MACD' + macd_suffix]    # macd signal difference (relevant)
        df['macd_h'] = macd['MACDh' + macd_suffix] # macd value
        df['macd_s'] = macd['MACDs' + macd_suffix] # signal value
        
        #stoch = pta.stoch(df['high'], df['low'], df['close'], s.stoch_k.value, s.stoch_d.value, s.stoch_smooth_k.value)
        #stoch_suffix = f"_{s.stoch_k.value}_{s.stoch_d.value}_{s.stoch_smooth_k.value}"
        #what output?
        #print(stoch)
        #print("start")
        #df['short_has'] = df.apply(lambda x: s.pivotid(df, x.name,s.short_has.value,s.short_has.value), axis=1)
        #df['strng_has'] = df.apply(lambda x: s.pivotid(df, x.name,s.strng_has.value,s.strng_has.value), axis=1)

        #print("start")
        return df

    def populate_entry_trend(s, df: DataFrame, metadata: dict) -> DataFrame:
        #df.loc[(True), 'enter_long'] = 0
        #df.loc[
        #    (
        #        (qtpylib.crossed_above(df['ema5'], df['ema15']))
        #    ),
        #    'enter_long'] = 1
        df.loc[(
                (df['st_d'] == 1) &
                (df['st_d'].shift() == -1) &
                (df['macd'] >= s.macd_buy.value)
            ), ['enter_long', 'enter_tag']] = (1, 'st_macd')
        return df

    def populate_exit_trend(s, df: DataFrame, metadata: dict) -> DataFrame:
        #df.loc[
        #    (
        #        (qtpylib.crossed_below(df['ema5'], df['ema15'])) |
        #        (df['ema5'].values[-1] < df['ema5'].values[-2])
        #    ),
        #    'exit_long'] = 1
        df.loc[(
                (df['st_d'] == -1) | #&
                (df['macd'] < 0)
                #(df['supertrend_direction'].shift() == 1)
            ), ['exit_long', 'exit_tag']] = (1, 'st_macd_change')
        return df
