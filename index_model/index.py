import datetime as dt
import pandas as pd
import numpy as np
import calendar
import os

class IndexModel:
    
    backtest_start = None
    backtest_end = None
    w = None
       
    def __init__(self) -> None:
        cwd = os.getcwd()
        input_folder = r'\data_sources'
        self.prices = pd.read_csv(cwd+ input_folder + r'\stock_prices.csv')
        self.prices.index = [dt.date(year=int(date[2]), month=int(date[1]), day=int(date[0])) for date in [date.split("/") for date in list(self.prices.Date)]]
        self.prices['Weekday'] = [calendar.day_name[date.weekday()] for date in self.prices.index]
        self.prices = self.prices.loc[(self.prices['Weekday'] != 'Saturday') & (self.prices['Weekday'] != 'Sunday')] #keep only bus days 
        self.prices = self.prices.drop(columns=['Date', 'Weekday'])
        self.prices = self.prices.iloc[1:, :]
        

    def calc_index_level(self,start_date: dt.date, end_date: dt.date, w: list) -> pd.Series:
        
        #this method calculates the index level by normalizing the index level after each inception date (by dusing divisor)
        
        self.backtest_start = start_date
        self.backtest_end = end_date
        self.w = w
        
        
        #initialize index level pd.Series object
        idx_level = pd.Series(np.nan*len(self.prices.loc[self.backtest_start:self.backtest_end].index), index= self.prices.loc[self.backtest_start:self.backtest_end].index, name='Index Level')
        idx_level[0] = 100
        
        #create empty lists to save intermediate results
        stock_reb_list =[]  #stock selection at each rebalnce date
        div_list = []     #divisors list et eaceach rebalnce date
        reb_date_list = []  # rebalance dates list
        div_list_by_date = []  #divisors at each date
        stock_prices_reb = [] #selected stock at the rebalance date prices 
        
        i = 1
        for date in self.prices.loc[self.backtest_start:(self.backtest_end - dt.timedelta(days=1))].index:
            #check whether the indx should be rebalanced. Given that the data set (aka, prices df) is already cleaned to get just business days, it checks if the month of 2 consecutive dates is not the same
            if date.month != self.prices.index[i-1].month:           
                stocks_reb = self.prices.iloc[i-1,:].sort_values(ascending=False)[:3].index   #select the top 3 stocks based of the previous date
                stock_reb_list.append(stocks_reb)
                stock_prices_reb.append(self.prices.loc[date, stocks_reb])
                sel = self.prices.loc[date, stocks_reb]
                #divsor calculation at the rebalance date: index level after rebalnce at the rebalance date, divided by the index level
                div = round(round(sum(sel*w),5)/idx_level[idx_level.index[i-1]],6)     
                div_list.append(div)
                reb_date_list.append(date)
        
            div_list_by_date.append(div)
            date_c = idx_level.index[i]
            
            #Index level at t+1 ("The selection becomes effective close of business on the first business date of each month", at least this is my understading) as weighted avg of the selected stock normalized for the divisor
            idx_level[i]= round(sum(self.prices.loc[date_c, stocks_reb]*w)/div,2)  
            i = i+1
        
        return(idx_level)



    def calc_index_level_v2(self, start_date: dt.date, end_date: dt.date, w: list) -> pd.Series:
        
        #this method calculates the index level by compounding the index level as follow: Index_level(t) = Index_level(t -1)*return(t)
        #where ret(t) is the %change of the weighted avg of the selected stocks 
        #please note that if t is a rebelance date, the return in t+1 will be calculated using the new selected stocks in t: w_avg(t+1)/w_avg(t)-1, where both weighted avg are caluclated using the new selection
        
        self.backtest_start = start_date
        self.backtest_end = end_date
        self.w = w
        
        
        idx_level = pd.Series(np.nan*len(self.prices.loc[self.backtest_start:self.backtest_end].index), index= self.prices.loc[self.backtest_start:self.backtest_end].index, name='Index Level')
        idx_level[0] = 100
        
        #create emptylist to save intermediate results
        stock_reb_list =[]
        reb_date_list = []
        stock_prices_reb = []   
        
        
        #calculation of the weighted averages for each date based on the rule (top 3 stocks at the previous bus day of the rebalcance date)
        idx_level_pre = pd.Series(np.nan*len(self.prices.loc[self.backtest_start:self.backtest_end].index), index= self.prices.loc[self.backtest_start:self.backtest_end].index, name='Index Level Pre')
        
        i = 1
        for date in idx_level_pre.loc[self.backtest_start:self.backtest_end].index:
            
            if date.month != self.prices.index[i-1].month:
                stocks_reb = self.prices.iloc[i-1,:].sort_values(ascending=False)[:3].index
                stock_reb_list.append(stocks_reb)
                stock_prices_reb.append(self.prices.loc[date, stocks_reb])
                reb_date_list.append(date)
            idx_level_pre[i-1] = sum(self.prices.loc[date, stocks_reb]*w)
            i= i+1 
        
        idx_at_reb_date = pd.Series([sum(p*w) for p in stock_prices_reb], index = reb_date_list)
        
        #compounding the index using returns of the weighted averages. Again, if t is a rebelance date the return in t+1 would be w_avg(t+1)/w_avg(t)-1, where both weighted avg are caluclated using the new selection
        # the returns is calculated for t+1, given that "The selection becomes effective close of business on the first business date of each month" (at least this is my understading)
        i = 0
        j = 0
        for date in idx_level[self.backtest_start + dt.timedelta(days=1):self.backtest_end].index:
            if date in idx_at_reb_date.index:
                idx = sum(self.prices.loc[date, stock_reb_list[j]]*w)
                ret =(idx/idx_level_pre[i])-1
                j = j+1
            else:
                ret = (idx_level_pre[i+1]/idx_level_pre[i])-1
    
            idx_level[date] = round((1+ret)*idx_level[i],2)
            i = i+1
        
        return(idx_level)
            
    
    def export_values(self, file_name: str, file_name2: str) -> None:
        
        cwd = os.getcwd()
        output_folder = r'\Output'
        
        
        index_level = self.calc_index_level(self.backtest_start, self.backtest_end, self.w)
        index_level.to_csv(cwd + output_folder + r'\ ' +  file_name)
        
        index_level_2 = self.calc_index_level_v2(self.backtest_start, self.backtest_end, self.w)
        index_level_2.to_csv(cwd + output_folder + r'\ ' +  file_name2)    
        
        
        
