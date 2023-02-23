import logging
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from sqlalchemy.orm.base import RELATED_OBJECT_OK
from sqlalchemy.sql.elements import or_
import talib.abstract as ta
import pandas_ta as pta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.exchange import timeframe_to_minutes
from freqtrade.persistence import Trade
from technical import indicators
from datetime import datetime, timezone
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter, RealParameter,
                                IStrategy, IntParameter, merge_informative_pair)


class flawless_lambo(IStrategy):

    # Add some logging
    logger = logging.getLogger(__name__)
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    @property
    def protections(self):
        return [
            {
                "method": "MaxDrawdown",
                "lookback_period": 360,
                "trade_limit": 1,
                "stop_duration": 720,
                "max_allowed_drawdown": 0.05
            },
            {
                "method": "StoplossGuard",
                "lookback_period": 4320,
                "trade_limit": 1,
                "stop_duration": 10080,
                "only_per_pair": True
            },
            {
                "method": "LowProfitPairs",
                "lookback_period": 1440,
                "trade_limit": 1,
                "stop_duration": 1440,
                "required_profit": 0.003
            }
        ]

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    # ROI1 table:
    
    minimal_roi = {
            # every 30 min
            "120": 0.3,
            "150": 0.226,
            "180": 0.223,
            "210": 0.21,
            "240": 0.216,
            "270": 0.213,
            "300": 0.21,
            "330": 0.206,
            "360": 0.203,
            "390": 0.2,
            "420": 0.196,
            "450": 0.193,
            "480": 0.19,
            "510": 0.186,
            "540": 0.183,
            "570": 0.18,
            "600": 0.176,
            "630": 0.173,
            "660": 0.17,
            "690": 0.166,
            "720": 0.163,
            "750": 0.16,
            "780": 0.156,
            "810": 0.153,
            "840": 0.15,
            "870": 0.146,
            "900": 0.143,
            "930": 0.14,
            "960": 0.136,
            "990": 0.133,
            "1020": 0.13,
            "1050": 0.12,
            "1080": 0.11,
            "1110": 0.1,
            "1140": 0.09,
            "1170": 0.086,
            "1200": 0.083,
            "1230": 0.08,
            "1260": 0.07,
            "1290": 0.066,
            "1320": 0.063,
            "1350": 0.06,
            "1380": 0.056,
            "1410": 0.053,
            "1440": 0.05,
            # every 3 hours after 24
            "1620": 0.046,
            "1800": 0.043,
            "1980": 0.04,
            "2160": 0.036,
            "2340": 0.033,
            "2520": 0.03,
            "2700": 0.026,
            "2880": 0.023,
            "3060": 0.02,
            "3240": 0.016,
            "3420": 0.013,
            "3600": 0.01,
            "3780": 0.006,
            "3900": -0.01,
            "3960": -0.02,
            "4020": -0.03
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    # use_custom_stoploss = True
    stoploss = -1 #-0.10

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.019
    trailing_only_offset_is_reached = False
    process_only_new_candles = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30 #30

    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    # sell_profit_offset = 0.019
    ignore_roi_if_buy_signal = False


    # hyperopt params
    sell_rsi = DecimalParameter(60, 100, default=70)
    sell_williams = DecimalParameter(-30, 0, default=-10)

    # trailing sell (borrowed from UziChanTB2)
    custom_info_trail_sell = dict()
    trailing_sell_order_enabled = True    
    # trailing_expire_seconds = 1800      #NOTE 5m timeframe
    # trailing_expire_seconds = 1800/5    #NOTE 1m timeframe
    trailing_expire_seconds = 1800*3    #NOTE 15m timeframe
    # trailing_expire_seconds = 1800*6
    trailing_sell_uptrend_enabled = True    
    trailing_expire_seconds_uptrend = 300
    min_uptrend_trailing_profit = 0.02
    debug_mode = True
    trailing_sell_max_stop = 0.01   # stop trailing sell if current_price < starting_price * (1+trailing_buy_max_stop)
    trailing_sell_max_sell = 0.000  # sell if price between downlimit (=max of serie (current_price * (1 + trailing_sell_offset())) and (start_price * 1+trailing_sell_max_sell))
    abort_trailing_when_sell_signal_triggered = False

    
    init_trailing_sell_dict = {
        'trailing_sell_order_started': False,
        'trailing_sell_order_downlimit': 0,        
        'start_trailing_sell_price': 0,
        'sell_tag': None,
        'start_trailing_time': None,
        'offset': 0,
        'allow_sell_trailing': False,
    }

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }
    
    @property
    def plot_config(self):
        return {
            "main_plot": {
                "bb.lower": {
                    "color": "#9c6edc",
                    "type": "line"
                },
                "bb.upper": {
                    "color": "#9c6edc",
                    "type": "line"
                },
                "vwma": {
                    "color": "#4f9f02",
                    "type": "line"
                }
            },
            "subplots": {
                "obv": {
                    "OBV": {
                        "color": "#1b61ab",
                        "type": "line"
                    },
                    "OBVSlope": {
                        "color": "#f18b7a",
                        "type": "line"
                    }
                },
                "vpci": {
                    "vpci": {
                        "color": "#d59a7a",
                        "type": "line"
                    }
                },
                "macd": {
                    "macd": {
                        "color": "#1c3d6a",
                        "type": "line"
                    },
                    "macdsignal": {
                        "color": "#873480",
                        "type": "line"
                    },
                    "macdhist": {
                        "color": "#478a87",
                        "type": "bar"
                    }
                },
                "wiliams": {
                    "williamspercent": {
                        "color": "#10f551",
                        "type": "line"
                    }
                },
                "stoch + rsi": {
                    "rsi": {
                        "color": "#d7affd",
                        "type": "line"
                    },
                    "slowd": {
                        "color": "#d7cc5c",
                        "type": "line"
                    },
                    "fastk": {
                        "color": "#186f86",
                        "type": "line"
                    }
                },
                "adx": {
                    "adx": {
                        "color": "#c392cd",
                        "type": "line"
                    },
                    "plus.di": {
                        "color": "#bcd6c5",
                        "type": "line"
                    },
                    "plus.di.slope": {
                            "color": "#ffffff",
                            "type": "line"
                    },
                    "minus.di": {
                        "color": "#eb044c",
                        "type": "line"
                    }
                }
            }
        }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.timeframe) for pair in pairs]

        return informative_pairs

    def trailing_sell(self, pair, reinit=False):
        # returns trailing sell info for pair (init if necessary)
        if not pair in self.custom_info_trail_sell:
            self.custom_info_trail_sell[pair] = dict()
        if (reinit or not 'trailing_sell' in self.custom_info_trail_sell[pair]):
            self.custom_info_trail_sell[pair]['trailing_sell'] = self.init_trailing_sell_dict.copy()
        
        return self.custom_info_trail_sell[pair]['trailing_sell']

    def trailing_sell_info(self, pair: str, current_price: float):
        # current_time live, dry run
        current_time = datetime.now(timezone.utc)
        if not self.debug_mode:
            return
        trailing_sell = self.trailing_sell(pair)

        duration = 0
        try:
            duration = (current_time - trailing_sell['start_trailing_time'])
        except TypeError:
            duration = 0
        finally:
            self.logger.info("'\033[36m'SELL: "
                f"pair: {pair} : "
                f"start: {trailing_sell['start_trailing_sell_price']:.4f}, "
                f"duration: {duration}, "
                f"current: {current_price:.4f}, "
                f"downlimit: {trailing_sell['trailing_sell_order_downlimit']:.4f}, "
                f"profit: {self.current_trailing_sell_profit_ratio(pair, current_price)*100:.2f}%, "
                f"offset: {trailing_sell['offset']}")

    def current_trailing_sell_profit_ratio(self, pair: str, current_price: float) -> float:
        trailing_sell = self.trailing_sell(pair)
        if trailing_sell['trailing_sell_order_started']:
            return (current_price - trailing_sell['start_trailing_sell_price'])/ trailing_sell['start_trailing_sell_price']
            #return 0-((trailing_sell['start_trailing_sell_price'] - current_price) / trailing_sell['start_trailing_sell_price'])
        else:
            return 0
    
    def trailing_sell_offset(self, dataframe, pair: str, current_price: float):
        current_trailing_sell_profit_ratio = self.current_trailing_sell_profit_ratio(pair, current_price)
        last_candle = dataframe.iloc[-1]
        adapt  = (last_candle['perc_norm']).round(5)
        default_offset = 0.003 * (1 + adapt)        #NOTE: default_offset 0.003 <--> 0.006
        
        trailing_sell  = self.trailing_sell(pair)
        if not trailing_sell['trailing_sell_order_started']:
            return default_offset

        # example with duration and indicators
        # dry run, live only
        last_candle = dataframe.iloc[-1]
        current_time = datetime.now(timezone.utc)
        trailing_duration =  current_time - trailing_sell['start_trailing_time']
        if trailing_duration.total_seconds() > self.trailing_expire_seconds:
            if ((current_trailing_sell_profit_ratio > 0) and (last_candle['sell'] != 0)):
                # more than 1h, price over first signal, sell signal still active -> sell
                return 'forcesell'
            else:
                # wait for next signal
                return None
        elif (self.trailing_sell_uptrend_enabled and (trailing_duration.total_seconds() < self.trailing_expire_seconds_uptrend) and (current_trailing_sell_profit_ratio < (-1 * self.min_uptrend_trailing_profit))):
            # less than 90s and price is falling, sell 
            return 'forcesell'

        if current_trailing_sell_profit_ratio > 0:
            # current price is lower than initial price
            return default_offset

        trailing_sell_offset = {
            # 0.06: 0.02,
            # 0.03: 0.01,
            0.1: default_offset,
        }

        for key in trailing_sell_offset:
            if current_trailing_sell_profit_ratio < key:
                return trailing_sell_offset[key]

        return default_offset


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Retrieve best bid and best ask from the orderbook
        # ------------------------------------
        
        # first check if dataprovider is available
        # if self.dp:
        #    if self.dp.runmode.value in ('live', 'dry_run'):
        #        ob = self.dp.orderbook(metadata['pair'], 1)
        #        dataframe['best_bid'] = ob['bids'][0][0]
        #        dataframe['best_ask'] = ob['asks'][0][0]


        # Bollinger!
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb.lower'] = bollinger['lower']
        dataframe['bb.middle'] = bollinger['mid']
        dataframe['bb.upper'] = bollinger['upper']

        # Added PCB Style OBV
        dataframe['OBV'] = ta.OBV(dataframe)
        dataframe['OBVSlope'] = pta.momentum.slope(dataframe['OBV'])

        # VWMA
        # vwma_period = 13
        # dataframe['vwma'] = ((dataframe["close"] * dataframe["volume"]).rolling(vwma_period).sum() / 
                    # dataframe['volume'].rolling(vwma_period).sum())
        
        # VWAP
        # vwap_period = 20
        # dataframe['vwap'] = qtpylib.rolling_vwap(dataframe, window=vwap_period)
        
        # VPCI
        dataframe['vpci'] = indicators.vpci(dataframe, period_long=14)
        
        #williamsR
        dataframe['williamspercent'] = indicators.williams_percent(dataframe)

        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        dataframe['plus.di'] = ta.PLUS_DI(dataframe)
        dataframe['minus.di'] = ta.MINUS_DI(dataframe)
        dataframe['plus.di.slope'] = pta.momentum.slope(dataframe['plus.di'])

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # Stochastic Fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']


        # Stochastic Slow
        stoch_slow = ta.STOCH(dataframe)
        dataframe['slowd'] = stoch_slow['slowd']
        dataframe['slowk'] = stoch_slow['slowk']

        # Perc
        dataframe['perc'] = ((dataframe['high'] - dataframe['low']) / dataframe['low']*100)
        dataframe['avg3_perc'] = ta.EMA(dataframe['perc'], 3)
        dataframe['perc_norm'] = (dataframe['perc'] - dataframe['perc'].rolling(50).min())/(dataframe['perc'].rolling(50).max() - dataframe['perc'].rolling(50).min())

        self.trailing_sell(metadata['pair'])

        return dataframe


    def do_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Bollinger!
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb.lower'] = bollinger['lower']
        dataframe['bb.middle'] = bollinger['mid']
        dataframe['bb.upper'] = bollinger['upper']

        # Added PCB Style OBV
        dataframe['OBV'] = ta.OBV(dataframe)
        dataframe['OBVSlope'] = pta.momentum.slope(dataframe['OBV'])
        

        # VWMA
        # vwma_period = 13
        # dataframe['vwma'] = ((dataframe["close"] * dataframe["volume"]).rolling(vwma_period).sum() / 
                    # dataframe['volume'].rolling(vwma_period).sum())

        # VWAP
        # vwap_period = 20
        # dataframe['vwap'] = qtpylib.rolling_vwap(dataframe, window=vwap_period)
                
        # VPCI
        dataframe['vpci'] = indicators.vpci(dataframe, period_long=14)

        #williamsR
        dataframe['williamspercent'] = indicators.williams_percent(dataframe)

        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        dataframe['plus.di'] = ta.PLUS_DI(dataframe)
        dataframe['minus.di'] = ta.MINUS_DI(dataframe)
        dataframe['plus.di.slope'] = pta.momentum.slope(dataframe['plus.di'])

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # Stochastic Fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']

        # Stochastic Slow
        stoch_slow = ta.STOCH(dataframe)
        dataframe['slowd'] = stoch_slow['slowd']
        dataframe['slowk'] = stoch_slow['slowk']

        # Perc
        dataframe['perc'] = ((dataframe['high'] - dataframe['low']) / dataframe['low']*100)
        dataframe['avg3_perc'] = ta.EMA(dataframe['perc'], 3)
        dataframe['perc_norm'] = (dataframe['perc'] - dataframe['perc'].rolling(50).min())/(dataframe['perc'].rolling(50).max()-dataframe['perc'].rolling(50).min())

        self.trailing_sell(metadata['pair'])

        return dataframe

    def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, sell_reason: str, **kwargs) -> bool:
        val = super().confirm_trade_exit(pair, trade, order_type, amount, rate, time_in_force, sell_reason, **kwargs)        
        
        if val:
            if self.trailing_sell_order_enabled and self.config['runmode'].value in ('live', 'dry_run'):
                val = False
                dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
                if(len(dataframe) >= 1):
                    last_candle = dataframe.iloc[-1].squeeze()
                    current_price = rate
                    trailing_sell= self.trailing_sell(pair)
                    trailing_sell_offset = self.trailing_sell_offset(dataframe, pair, current_price)

                    if trailing_sell['allow_sell_trailing']:
                        if (not trailing_sell['trailing_sell_order_started'] and (last_candle['sell'] != 0)):
                            trailing_sell['trailing_sell_order_started'] = True
                            trailing_sell['trailing_sell_order_downlimit'] = last_candle['close']
                            trailing_sell['start_trailing_sell_price'] = last_candle['close']
                            trailing_sell['sell_tag'] = last_candle['sell_tag']
                            trailing_sell['start_trailing_time'] = datetime.now(timezone.utc)
                            trailing_sell['offset'] = 0
                            
                            self.trailing_sell_info(pair, current_price)
                            self.logger.info(f'start trailing sell for {pair} at {last_candle["close"]}')

                        elif trailing_sell['trailing_sell_order_started']:
                            if trailing_sell_offset == 'forcesell':
                                # sell in custom conditions
                                val = True
                                ratio = "%.2f" % ((self.current_trailing_sell_profit_ratio(pair, current_price)) * 100)
                                self.trailing_sell_info(pair, current_price)
                                self.logger.info(f"FORCESELL for {pair} ({ratio} %, {current_price})")

                            elif trailing_sell_offset is None:
                                # stop trailing sell custom conditions
                                self.trailing_sell(pair, reinit=True)
                                self.logger.info(f'STOP trailing sell for {pair} because "trailing sell offset" returned None')

                            elif current_price > trailing_sell['trailing_sell_order_downlimit']:
                                # update downlimit
                                old_downlimit = trailing_sell["trailing_sell_order_downlimit"]
                                self.custom_info_trail_sell[pair]['trailing_sell']['trailing_sell_order_downlimit'] = max(current_price * (1 - trailing_sell_offset), self.custom_info_trail_sell[pair]['trailing_sell']['trailing_sell_order_downlimit'])
                                self.custom_info_trail_sell[pair]['trailing_sell']['offset'] = trailing_sell_offset
                                self.trailing_sell_info(pair, current_price)
                                self.logger.info(f'update trailing sell for {pair} at {old_downlimit} -> {self.custom_info_trail_sell[pair]["trailing_sell"]["trailing_sell_order_downlimit"]}')

                            elif current_price > (trailing_sell['start_trailing_sell_price'] * (1 - self.trailing_sell_max_sell)):
                                # sell! current price < downlimit && higher than starting price
                                val = True
                                ratio = "%.2f" % ((self.current_trailing_sell_profit_ratio(pair, current_price)) * 100)
                                self.trailing_sell_info(pair, current_price)
                                self.logger.info(f"current price ({current_price}) < downlimit ({trailing_sell['trailing_sell_order_downlimit']}) but higher than starting price ({(trailing_sell['start_trailing_sell_price'] * (1 + self.trailing_sell_max_sell))}). OK for {pair} ({ratio} %)")

                            elif current_price < (trailing_sell['start_trailing_sell_price'] * (1 - self.trailing_sell_max_stop)):
                                # stop trailing, sell fast, price too low
                                val = True                                
                                self.trailing_sell_info(pair, current_price)
                                self.logger.info(f'STOP trailing sell for {pair} because of the price is much lower than starting price * {1 + self.trailing_sell_max_stop}')
                            else:
                                # uplimit > current_price > max_price, continue trailing and wait for the price to go down
                                self.trailing_sell_info(pair, current_price)
                                self.logger.info(f'price too low for {pair} !')

                    else:
                        self.logger.info(f"Wait for next sell signal for {pair}")

                if (val == True):
                    self.trailing_sell_info(pair, rate)
                    self.trailing_sell(pair, reinit=True)
                    self.logger.info(f'STOP trailing sell for {pair} because I SOLD it')

        if sell_reason != 'sell_signal':
            val = True

        return val
        
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
            (dataframe['volume'] > 0) &
            (dataframe['OBVSlope'] > 0) &
            (dataframe['plus.di.slope'] > 0) &
            (dataframe['williamspercent'] < -66) &
            (qtpylib.crossed_above(dataframe['close'], dataframe['bb.lower']))
            ),'buy'] = 1
        
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                (dataframe['volume'] > 0) &
                (dataframe['close'] > dataframe['bb.upper']) &
                (dataframe['plus.di.slope'] < 0) &
                (dataframe['williamspercent'] >= self.sell_williams.value) &
                (dataframe['rsi'] >= self.sell_rsi.value)
            ),
            'sell'] = 1

        if self.trailing_sell_order_enabled and self.config['runmode'].value in ('live', 'dry_run'): 
            last_candle = dataframe.iloc[-1].squeeze()
            trailing_sell = self.trailing_sell(metadata['pair'])
            if (last_candle['sell'] != 0):
                if not trailing_sell['trailing_sell_order_started']:
                    open_trades = Trade.get_trades([Trade.pair == metadata['pair'], Trade.is_open.is_(True), ]).all()
                    if open_trades:
                        self.logger.info(f"Set 'allow_SELL_trailing' to True for {metadata['pair']} to start *SELL* trailing")
                        # self.custom_info_trail_buy[metadata['pair']]['trailing_buy']['allow_trailing'] = True
                        trailing_sell['allow_sell_trailing'] = True
                        initial_sell_tag = last_candle['sell_tag'] if 'sell_tag' in last_candle else 'sell signal'
                        dataframe.loc[:, 'sell_tag'] = f"{initial_sell_tag} (start trail price {last_candle['close']})"
            else:
                if (trailing_sell['trailing_sell_order_started'] == True):
                    self.logger.info(f"Continue trailing for {metadata['pair']}. Manually trigger sell signal!")
                    dataframe.loc[:,'sell'] = 1
                    dataframe.loc[:, 'sell_tag'] = trailing_sell['sell_tag']

        return dataframe

    
    # "All watched over by machines with loving grace..."
