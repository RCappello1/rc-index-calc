import datetime as dt
from index_model.index import IndexModel

if __name__ == "__main__":
     
    backtest_start = dt.date(year=2020, month=1, day=1)
    backtest_end = dt.date(year=2020, month=12, day=31)
    w_1 = [0.5, 0.25, 0.25] #I left the weights as variables, in case one wants to test different weighting schemes.
    index = IndexModel()

    index.calc_index_level(start_date=backtest_start, end_date=backtest_end, w = w_1)  #this method returns the index level caluclated using divisors at the each inception date (by normalizng the index level)
    index.calc_index_level_v2(start_date=backtest_start, end_date=backtest_end, w = w_1) #this method returns the index level by compounding the index levels
    
    index.export_values("export_RC_divisor.csv", "export_RC_v2_compounding.csv")



