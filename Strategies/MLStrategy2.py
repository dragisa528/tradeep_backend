import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from freqtrade.strategy.interface import IStrategy
from sklearn.ensemble import RandomForestClassifier
import talib
import ccxt
import pickle
import os
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

class MLStrategy2(IStrategy):
    sma_periods = [10, 20, 50]
    rsi_period = 14
    bbands_period = 20
    window_length = 50
    model_kind = 'RandomForest'
    models = {}
    model_timeframes = {'5m': 1, '15m': 3, '30m': 6}  #timeframes of models with their corresponding dividers    
    pairs = ['DOGE/USDT', 'ETH/USDT', 'BTC/USDT'] #, 'BTC/USDT', 'ETH/USDT'
    stoploss = -0.271
    timeframe = '5m'

    def bot_start(self, **kwargs) -> None:
        for pair in self.pairs:
            self.models[pair] = {}
            for timeframe in self.model_timeframes.keys():
                with open(f'model_{self.model_kind}_{pair.replace("/", "-")}_{timeframe}.pkl', 'rb') as file:
                    self.models[pair][timeframe] = pickle.load(file)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Calculate the Bollinger Bands
        for sma_period in self.sma_periods:
            dataframe[f'sma_{sma_period}'] = talib.SMA(dataframe['close'], timeperiod=sma_period)
        dataframe['rsi'] = talib.RSI(dataframe['close'], timeperiod=self.rsi_period)
        upper, _, lower = talib.BBANDS(dataframe['close'], timeperiod=self.bbands_period, nbdevup=2, nbdevdn=2, matype=0)
        # Add the Bollinger Bands as columns to the DataFrame
        dataframe['bband_lower'] = lower
        dataframe['bband_upper'] = upper

        return dataframe
    
    def preprocess_dataframe_for_prediction(self, temp_df):
        cols = ['open', 'high', 'low', 'close', 'volume']   #columns to be stacked in one row
        i = 1
        while i < self.window_length-1:
            for col in cols:
                temp_df[f'{col}_{i}'] = temp_df[col].shift(self.window_length-i)
            i = i + 1
        for col in cols:
            temp_df[f'{col}_{self.window_length-1}'] = temp_df[col]
            temp_df[col] = temp_df[col].shift(self.window_length)

        cols = temp_df.columns.tolist()

        indicator_cols = [f'sma_{period}' for period in self.sma_periods]    #columns to be moved to end
        indicator_cols.extend(['rsi', 'bband_lower', 'bband_upper'])
        for indicator in indicator_cols:
            cols.append(cols.pop(cols.index(indicator)))
        temp_df = temp_df[cols]
        
        temp_df = temp_df.drop(columns=['date'])
        if 'enter_long' in temp_df.columns:
            temp_df = temp_df.drop(columns=['enter_long'])
        temp_df = temp_df.dropna(axis=0)
        return temp_df

    def predict_with_model(self, models, dataframe, sell=False):
        all_predictions = []
        for timeframe in self.model_timeframes.keys():
            divider = self.model_timeframes[timeframe]
            predictions = []
            temp_df = dataframe.copy()
            target_mod = (temp_df.shape[0]-1) % divider
            temp_df = temp_df[temp_df.index % divider == target_mod].reset_index(drop=True)  #takes df.length/divider rows from df, ending with the most recent row
            #print(f'df with divider {divider}: ({temp_df.shape})', temp_df)
            for i in range(self.window_length):
                predictions.append(False)
            if sell:
                predictions.extend([not a for a in models[timeframe].predict(self.preprocess_dataframe_for_prediction(temp_df))])
            else:
                predictions.extend(models[timeframe].predict(self.preprocess_dataframe_for_prediction(temp_df)))
            predictions = np.repeat(predictions, divider)

            all_predictions.append(predictions)
        
        majority_predictions = [sum(pred)/len(pred) > 0.5 for pred in zip(*all_predictions)]    #True if over half of the models predicted True for this timestep
        return majority_predictions
        
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Use the trained model to generate buy signals
        print('buy meta:', metadata)
        if metadata['pair'] in self.pairs:
            predictions = self.predict_with_model(self.models[metadata['pair']], dataframe)
            print(len(predictions))
            print(predictions)
            dataframe['buy'] = predictions
        else:
            dataframe['buy'] = False
        print('buy df-populated:', dataframe)
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Use the trained model to generate sell signals
        print('sell meta:', metadata)
        if metadata['pair'] in self.pairs:
            predictions = self.predict_with_model(self.models[metadata['pair']], dataframe, True)
            print(predictions)
            dataframe['sell'] = 0
        else:
            dataframe['sell'] = False
        print('sell df-populated:', dataframe)
        return dataframe

'''
    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: Optional[float], max_stake: float,
                            leverage: float, entry_tag: Optional[str], side: str,
                            **kwargs) -> float:
        
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        current_candle = dataframe.iloc[-1].squeeze()

        if current_candle['fastk_rsi_1h'] > current_candle['fastd_rsi_1h']:
            if self.config['stake_amount'] == 'unlimited':
                # Use entire available wallet during favorable conditions when in compounding mode.
                return max_stake
            else:
                # Compound profits during favorable conditions instead of using a static stake.
                return self.wallets.get_total_stake_amount() / self.config['max_open_trades']

        # Use default stake amount.
        return proposed_stake
'''
