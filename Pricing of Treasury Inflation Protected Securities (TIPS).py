#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''
TIPS Pricing Project
'''
import datetime
from datetime import date
import numpy as np
import pandas as pd
import math
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as td

class TIPS_Pricing():
    
    def __init__(self, issue_date, maturity, coupon_rate, interest_rate, P):
        self.issue_date = issue_date
        self.maturity = maturity
        self.coupon_rate = coupon_rate
        self.interest_rate = interest_rate
        self.P = P
    
    '''Created an array of coupon dates from issue date'''
    def coupon_date(self):
        
        coupon_date=[]
        coupon_date.append(self.issue_date)
        year=self.issue_date.year
        month=self.issue_date.month
        day=self.issue_date.day
        
        for i in range(2*self.maturity):
            month+=6
            if month>12:
                month=month-12
                year=year+1
            date=datetime.date(year,month,day)
            coupon_date.append(date)
            
        return np.array(coupon_date)
    
    '''Imported historical CPI rates from excel. Based on past monthly CPI rates, predicted future CPI rates.
    The CPI table imported from excel was updated until the maturity of the bond'''
    def CPI_Table(self):
        
        issue_date = self.issue_date
        maturity=self.maturity
        #Import historical CPI
        CPI = pd.read_csv(r'E:\Career Development\Project\CPI_Data.csv', parse_dates = ['Date'])
        CPI = CPI.dropna()
        CPI['Date'] = pd.to_datetime(CPI['Date'])
        month_count = CPI['Date'][CPI.shape[0]-1].month - CPI['Date'][0].month
        CAGR = (CPI['CPI'][CPI.shape[0]-1]/CPI['CPI'][0]) ** (1/month_count)
        maturity_date = issue_date+td(years=maturity)
        last_date = CPI['Date'][CPI.shape[0]-1]
        last_CPI = CPI['CPI'][CPI.shape[0]-1]
        n = 0
        month = CPI['Date'][CPI.shape[0]-1].month + 1
        year = CPI['Date'][CPI.shape[0]-1].year
        while month != maturity_date.month + 3 or year != maturity_date.year:
            n = n + 1
            CPI.loc[CPI.shape[0]] = [datetime.datetime(year, month, last_date.day), last_CPI * (CAGR ** n)]
            if month == 12:
                month = 1
                year = year + 1
            else:
                month = month + 1
        CPI['Date']=pd.to_datetime(CPI['Date'])

        return(CPI)
    
    '''Predicting linearly interpolated CPI values with 3 months lag on coupon dates from CPI table '''
    def CPI_Predict(self,CPI, coupon_date):

        CPIRatio_predict = []
        #Looping over the remaining dates of future payment
        for i in (coupon_date):
            #Calculating 3 month prior coupon date to calculate CPI
            y = i 
            y_first_date = datetime.datetime(y.year, y.month, 1)
            y_loc = CPI[CPI['Date'] == y_first_date].index.values
            a = datetime.datetime(y.year, y.month, y.day)-td(months=3)

            #Calculating interpolated CPI
            x = datetime.datetime(CPI['Date'][y_loc - 3].dt.year, CPI['Date'][y_loc - 3].dt.month, CPI['Date'][y_loc - 3].dt.day)
            z = datetime.datetime(CPI['Date'][y_loc - 2].dt.year, CPI['Date'][y_loc - 2].dt.month, CPI['Date'][y_loc - 2].dt.day)
            Interpolated_CPI = (((CPI['CPI'][y_loc - 2].values - CPI['CPI'][y_loc - 3].values)  * (a - x).days / (z-x).days) + CPI['CPI'][y_loc -3]).values

            CPIRatio_predict.append(float(Interpolated_CPI))

        return np.array(CPIRatio_predict)
    
    '''Calculating  and creating array of un-adjusted dollar values of coupons'''
    def unadjusted_coupon(self, CPIRatio_predict):
        
        ref=CPIRatio_predict[0]
        unadjusted_coupon = [(cpi_rate*self.P*self.coupon_rate/(100*ref*2)) for cpi_rate in CPIRatio_predict]
        
        return np.array(unadjusted_coupon)

    '''Calculating and creating array time interval from coupon dates to present date'''
    def time_interval(self,coupon_date):
        
        t=[]
        for i in range(len(coupon_date)):
            t.append((coupon_date[i]-dt.today().date()).days)
            
        return np.array(t)
    
    '''Based on given interest rates of TIPS in the market, calculating array of interest rates for discounting.
    This is based on linear interpolation'''
    def rate_interpolate(self,intervals):
        
        zero_rates = pd.read_csv(r'E:\Career Development\Project\Future_Interest_Rate.csv')
        tips=[]
        for t in intervals:
            if t>0:
                for i in range(1,len(zero_rates)):
                    if t<zero_rates['month'][i]:
                        tips.append(float((zero_rates['rate'][i]-zero_rates['rate'][i-1])*(t-zero_rates['month'][i-1]))/float((zero_rates['month'][i]-zero_rates['month'][i-1]))+zero_rates['rate'][i-1])
                        break
                    if t==zero_rates['month'][i]:
                        tips.append(zero_rates['rate'][i])
                        break
            else:
                tips.append(0)

        return tips
    
    '''Calculating array of adjusted coupon from unadjusted coupon with it's respetive
    time interval (t) and discounting rate (r) '''
    def adjusted_coupon(self,unadjusted_coupon, t , r): 

        A_C = []
        for i in range(len(t)):
            if (t[i] >= 0):
                A_C.append(unadjusted_coupon[i] * (math.e ** (-r[i] * t[i]/360)))
            else:
                A_C.append(0)
        #U_C is Unadjusted coupon payment
        #i is interest rate
        #U_C is Unadjusted coupon payment
        
        return np.array(A_C)
    
    '''Creating present value of prinicipal received at maturity'''
    def Mat(self,CPIRatio_predict, r ):
        
        mt = max(1000, (CPIRatio_predict[len(CPIRatio_predict)-1]/CPIRatio_predict[0])*1000)
        print(mt)
        pmat = mt*math.e**(-r.iloc[len(r)-1]*20)
        
        return pmat
    
    '''Calculating accrued interest'''
    def Accrued_Coupon(self, coupon_date, A_C):
        
        i = 0
        while dt.today().date() < coupon_date[i]:
            i = i + 1
        ac_t = (dt.today().date() - coupon_date[i]).days
        ac = ac_t/((coupon_date[i+1] - coupon_date[i]).days) * A_C[i+1]

        return ac
    
    '''Creating dataframe of arrays created above. Later, we print the required values'''
    def final(self):
        
        final_table = pd.DataFrame()
        final_table['Date'] = self.coupon_date()
        final_table['CPI Rate']=self.CPI_Predict(self.CPI_Table(),self.coupon_date())
        final_table['Unadjusted_Coupon']= self.unadjusted_coupon(final_table['CPI Rate'])
        final_table['Time']=self.time_interval(final_table['Date'])
        final_table['Rate']=self.rate_interpolate(final_table['Time'])
        final_table['Adjusted_Coupon']=self.adjusted_coupon(final_table['Unadjusted_Coupon'],final_table['Time'],final_table['Rate'])
        Pmat=self.Mat(final_table['CPI Rate'],final_table['Rate'])
        AC = self.Accrued_Coupon(final_table['Date'], final_table['Adjusted_Coupon'])
        
        print (final_table.head())
        print('\n')
        print('The present value of the coupon is ' + str(round(sum(final_table['Adjusted_Coupon']),2)))
        print('\n')
        print('The price of present value of balloon payment is {P}'.format(P = round(Pmat,2)))
        print('\n')
        print('The interest accrued is {AI}'.format(AI = round(AC,2)))
        print('\n')
        print('The price of the bond is {P0}'.format(P0 = round(sum(final_table['Adjusted_Coupon']) + Pmat - AC,2)))
        
        


# In[2]:


price=TIPS_Pricing(datetime.date(2021,6,1),10,8,6,1000)


# In[3]:


price.final()

