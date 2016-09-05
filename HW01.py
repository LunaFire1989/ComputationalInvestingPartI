# -*- coding:utf-8 -*-  

'''
@author: yize.jiang
@contact: 315135833@qq.com
@summary: Homework 01
'''

# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

# Third Party Imports
import numpy as np
import datetime as dt


def simulate(na_norm_price, lf_port_alloc):
    # Get All Daily Return
    na_port_value = np.sum(na_norm_price * lf_port_alloc, axis=1)
    all_daily_ret = na_port_value.copy()
    tsu.returnize0(all_daily_ret)
    #print "All Daily Return: \n", all_daily_ret

    # Calc Volatility, Average Daily Return, Sharpe Ratio
    vol = np.std(all_daily_ret)
    daily_ret = np.mean(all_daily_ret)
    sharpe = np.sqrt(252) * daily_ret / vol

    # Calc Cumulative Return
    cum_ret = 1.0
    for ret in all_daily_ret:
        cum_ret = cum_ret * (1.0 + ret)
    
    return vol, daily_ret, sharpe, cum_ret

def optimize(dt_start, dt_end, ls_symbols):
    # Get Trading Day Close Time
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)

    # Get Stock Data
    c_dataobj = da.DataAccess('Yahoo', cachestalltime=0)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # Filling Data with NAN
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)
    
    # Get Norm Close Data
    na_price = d_data['close'].values
    na_norm_price = na_price / na_price[0, :]
    #print "NA Norm Price: \n", na_norm_price    

    # Get Opti Allocations
    opti_sharpe = 0.0
    for i1 in np.linspace(0.0, 1.0, 11):
        for i2 in np.linspace(0.0, 1.0, 11):
            for i3 in np.linspace(0.0, 1.0, 11):
                i4 = 1.0 - i1 - i2 - i3
                if i4 < 0 or i4 > 1:
                    continue
                lf_port_alloc = [i1, i2, i3, i4]
                vol, daily_ret, sharpe, cum_ret = simulate(na_norm_price, lf_port_alloc)
                if sharpe > opti_sharpe:
                    opti_alloc = lf_port_alloc
                    opti_sharpe = sharpe

    # Output the Result
    vol, daily_ret, sharpe, cum_ret = simulate(na_norm_price, opti_alloc)
    print "Start Date: ", dt_start
    print "End Date:", dt_end
    print "Symbols: ", ls_symbols
    print "Optimal Allocations:  ", opti_alloc
    print "Volatility (stdev of daily returns): ", vol
    print "Average Daily Return: ", daily_ret
    print "Sharpe Ratio: ", sharpe
    print "Cumulative Return: ", cum_ret

    # Process SPX Data
    ldf_data = c_dataobj.get_data(ldt_timestamps, ["$SPX"], ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    na_price = d_data['close'].values
    na_norm_price = na_price / na_price[0, :]
    #print "SPX Norm Price: \n", na_norm_price
    all_daily_ret = na_norm_price.copy()
    tsu.returnize0(all_daily_ret)

    vol = np.std(all_daily_ret)
    daily_ret = np.mean(all_daily_ret)
    sharpe = np.sqrt(252) * daily_ret / vol
    cum_ret = 1.0
    for ret in all_daily_ret:
        cum_ret = float(cum_ret * (1.0 + ret))

    # Output SPX Result
    print "SPX Volatility (stdev of daily returns): ", vol
    print "SPX Average Daily Return: ", daily_ret
    print "SPX Sharpe Ratio: ", sharpe
    print "SPX Cumulative Return: ", cum_ret

def main():
    # Start Date, End Date, Stock Symbol
    dt_start = dt.datetime(2010, 1, 1)
    dt_end = dt.datetime(2010, 12, 31)
    ls_symbols = ['C', 'GS', 'IBM', 'HNZ']

    # Calc Portfolio Optimization
    optimize(dt_start, dt_end, ls_symbols)

if __name__ == '__main__':
    print "Calc Portfolio Optimization"
    main()

