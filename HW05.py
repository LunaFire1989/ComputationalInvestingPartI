# -*- coding: utf-8 -*-

'''
@author: yize.jiang
@contact: 315135833@qq.com
@summary: Homework 05
'''

# Third Party Imports
import csv
import copy
import datetime as dt
import pandas as pd
import numpy as np

# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep

def get_stock_data(dt_start, dt_end, ls_symbols=None):
    # Config Stock Time
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))
    
    dataobj = da.DataAccess('Yahoo')
    # Get Symbols
    if ls_symbols==None:
        ls_symbols = dataobj.get_symbols_from_list('sp5002012')
        ls_symbols.append('SPY')
    
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    return d_data['close']
    
    
if __name__ == '__main__':
    d_data = get_stock_data(dt.datetime(2010, 1, 1), dt.datetime(2010, 12, 31), ['AAPL', 'GOOG', 'IBM', 'MSFT'])
    
    df_mean = pd.rolling_mean(d_data, 20)   
    df_std = pd.rolling_std(d_data, 20)    
    df_boll_val = (d_data - df_mean) / df_std
    df_boll_val.to_csv('BollVal.csv')    
    
    print df_boll_val

    