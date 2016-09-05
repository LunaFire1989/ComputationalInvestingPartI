# -*- coding: utf-8 -*-

'''
@author: yize.jiang
@contact: 315135833@qq.com
@summary: Homework 02
'''

# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkstudy.EventProfiler as ep

# Third Party Imports
import numpy as np
import copy
import datetime as dt

def find_events(ls_symbols, d_data):
    df_close = d_data['actual_close']
    ts_market = df_close['SPY']
    print "Finding Events..."

    # Creating Empty Dataframe
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    # Time Stamps for the Event Range
    ldt_timestamps = df_close.index

    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            # Calc Event Logic
            f_symprice_today = df_close[s_sym].ix[ldt_timestamps[i]]
            f_symprice_yest = df_close[s_sym].ix[ldt_timestamps[i - 1]]
            
            if f_symprice_yest >= 10.0 and f_symprice_today < 10.0:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1
            
            '''
            f_marketprice_today = ts_market.ix[ldt_timestamps[i]]
            f_marketprice_yest = ts_market.ix[ldt_timestamps[i - 1]]
            f_symreturn_today = (f_symprice_today / f_symprice_yest) - 1
            f_marketreturn_today = (f_marketprice_today / f_marketprice_yest) - 1

            # Event is found if the symbol is down more then 3% while the
            # market is up more then 2%
            if f_symreturn_today <= -0.03 and f_marketreturn_today >= 0.02:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1
            '''

    return df_events


if __name__ == '__main__':
    # Config Stock Time
    dt_start = dt.datetime(2008, 1, 1)
    dt_end = dt.datetime(2009, 12, 31)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))
    
    # Get S&P500 Data
    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    ls_symbols.append('SPY')
    
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    df_events = find_events(ls_symbols, d_data)
    
    print "Creating Event Study"
    ep.eventprofiler(df_events, d_data, i_lookback=20, i_lookforward=20,
                s_filename='EventStudyPrice5_2012.pdf', b_market_neutral=True, b_errorbars=True,
                s_market_sym='SPY')
                
    
                