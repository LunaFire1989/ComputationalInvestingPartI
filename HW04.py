# -*- coding: utf-8 -*-

'''
@author: yize.jiang
@contact: 315135833@qq.com
@summary: Homework 04
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

class StockOrder():    
    def __init__(self, file_path):
        # Init Prop        
        self.__orders = {}
        self.__start_date = None
        self.__end_date = None
        self.__symbols = []
        
        # Load CSV File
        reader = csv.DictReader(open(file_path, "r"), fieldnames=["year", "month", "day", "symbol", "action", "qty"])
        for row in reader:
            # Parse Orders
            date_time = dt.datetime(int(row["year"]), int(row["month"]), int(row["day"]))
            self.__orders.setdefault(date_time, [])
            order = (row["symbol"], row["action"], int(row["qty"]))
            self.__orders[date_time].append(order)
            
            # Process Time, Symbol
            if row['symbol'] not in self.__symbols:
                self.__symbols.append(row['symbol'])
            
            if self.__start_date == None:
                self.__start_date = date_time
            else:
                self.__start_date = min(self.__start_date, date_time)
            
            if self.__end_date == None:
                self.__end_date = date_time
            else:
                self.__end_date = max(self.__end_date, date_time)
            
    def get_start_date(self):
        return self.__start_date
    
    def get_end_date(self):
        return self.__end_date + dt.timedelta(days=1)
        
    def get_symbols(self):
        return self.__symbols
        
    def get_orders(self, date_time):
        return self.__orders.get(date_time)
    
    def get_all_orders(self):
        return self.__orders

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

    return ls_symbols, d_data

def find_event_to_order(ls_symbols, d_data, event_price=5.0, order_file='HW4_Order.csv'):
    df_close = d_data['actual_close']
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN
    ldt_timestamps = df_close.index    

    writer = csv.writer(open(order_file, 'w'), delimiter=',')

    for s_symbol in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            # Calc Event Logic
            f_price_today = df_close[s_symbol].ix[ldt_timestamps[i]]
            f_price_yest = df_close[s_symbol].ix[ldt_timestamps[i - 1]]
            
            if f_price_yest >= event_price and f_price_today < event_price:
                df_events[s_symbol].ix[ldt_timestamps[i]] = 1
                # Output Order
                writer.writerow([ldt_timestamps[i].year, 
                                  ldt_timestamps[i].month,
                                  ldt_timestamps[i].day,
                                  s_symbol,
                                  'BUY',
                                  '100'])          
                writer.writerow([ldt_timestamps[min(i + 5, len(ldt_timestamps) - 1)].year, 
                                  ldt_timestamps[min(i + 5, len(ldt_timestamps) - 1)].month,
                                  ldt_timestamps[min(i + 5, len(ldt_timestamps) - 1)].day,
                                  s_symbol,
                                  'SELL',
                                  '100'])
                
    return df_events
    
def sim_trade(df_stock_data, stock_orders, init_cash=50000):
    df_trade_matrix = pd.DataFrame(np.zeros(df_stock_data.shape), columns=stock_orders.get_symbols(), index=df_stock_data.index)      
    df_trade_matrix['CASH'] = 0
    
    # Calc Info Change
    for i in range(len(df_trade_matrix)):
        # Find Date Order
        ts_date_time = df_trade_matrix.ix[i].name
        dt_date = dt.datetime(ts_date_time.year, ts_date_time.month, ts_date_time.day)
        orders = stock_orders.get_orders(dt_date)

        # Make the Stock Change       
        if orders == None:
            continue;
        for order in orders:
            symbol, action, qty = order
            #print symbol, action, qty
            if action == 'BUY':
                df_trade_matrix.ix[i, symbol] += qty
            else:
                df_trade_matrix.ix[i, symbol] += -qty
                
        # Calc the Cash Change
        for sym in stock_orders.get_symbols():
            df_trade_matrix.ix[i, 'CASH'] += -df_trade_matrix.ix[i, sym] * df_stock_data.ix[i, sym]
    
    # Calc Info Holding
    df_trade_matrix.ix[0, 'CASH'] += init_cash
    for i in range(1, len(df_trade_matrix)):
        df_trade_matrix.ix[i] = df_trade_matrix.ix[i - 1] + df_trade_matrix.ix[i]
        
    # Calc Daily Portfolio
    df_trade_matrix['PORTFOLIO'] = 0
    for i in range(len(df_trade_matrix)):
        df_trade_matrix.ix[i, 'PORTFOLIO'] = df_trade_matrix.ix[i, 'CASH']
        for sym in stock_orders.get_symbols():
            df_trade_matrix.ix[i, 'PORTFOLIO'] += df_trade_matrix.ix[i, sym] * df_stock_data.ix[i, sym]
    
    # Save to CSV        
    df_trade_matrix.to_csv('Portfilio.csv')
  
    return df_trade_matrix

def anal_protfilio(na_port_value):
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

if __name__ == '__main__':
    
    # Get S&P2012 Stock Data
    print '-------------------- Get Stock Data Start --------------------'
    ls_symbols, d_data = get_stock_data(dt.datetime(2008, 1, 1), dt.datetime(2009, 12, 31))
    print '--------------------- Get Stock Data End ---------------------'
    
    print '------------------- Find Event Order Start -------------------'
    df_events = find_event_to_order(ls_symbols, d_data, event_price=10.0)
    ep.eventprofiler(df_events, d_data, i_lookback=20, i_lookforward=20,
                     s_filename='EventStudyPrice5_2012.pdf', b_market_neutral=True, b_errorbars=True,
                     s_market_sym='SPY')
    print '-------------------- Find Event Order End --------------------'
    
    
    print '-------------------- Simulate Trade Start --------------------'
    file_path = 'HW4_Order.csv'
    stock_orders = StockOrder(file_path)    
    print 'Start Date: ', stock_orders.get_start_date()
    print 'End Date: ', stock_orders.get_end_date()
    print 'Symbols: ', stock_orders.get_symbols()
    
    ls_symbols, d_data = get_stock_data(stock_orders.get_start_date(), stock_orders.get_end_date(), stock_orders.get_symbols())
    df_stock_data = d_data['close']    
    df_stock_data.to_csv('StockHist.csv')
    df_trade_matrix = sim_trade(df_stock_data, stock_orders)
    print 'The final value of the portfolio using the sample file is ', df_trade_matrix.ix[-1, 'PORTFOLIO']
    print '--------------------- Simulate Trade End ---------------------'
    
    print '-------------------- Calculate Trade Start -------------------'
    na_port_value = df_trade_matrix['PORTFOLIO'].values
    na_port_value = na_port_value / na_port_value[0]
    vol, daily_ret, sharpe, cum_ret = anal_protfilio(na_port_value)
    print 'Sharpe Ratio of Fund : ', sharpe
    print 'Total Return of Fund : ', cum_ret
    print 'Standard Deviation of Fund : ', vol
    print 'Average Daily Return of Fund : ', daily_ret
    print '--------------------- Calculate Trade End --------------------'
    
    