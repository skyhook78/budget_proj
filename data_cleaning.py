# -*- coding: utf-8 -*-
"""
Created on Sat Jan  2 13:20:52 2021

@author: jonno
"""

import pandas as pd
from datetime import datetime

df=pd.read_csv('raw_transactions.csv')

#Remove empty observations
test = df[pd.notnull(df.Date)]

#clean and convert Date into appropriate format
test['Date']=test['Date'].apply(lambda x : datetime.strptime(x,'%d %b %y'))

#clean and convert debit and credit into a single numeric transaction variable 
test1 = test[pd.notnull(test.Debit)]
test1['Value'] = test1['Debit'].apply(lambda x: -1*float(x.split('$')[1].replace(',','')))
test2 = test[pd.notnull(test.Credit)]
test2['Value'] = test2['Credit'].apply(lambda x: float(x.split('$')[1].replace(',','')))
test3=pd.concat([test1,test2])

#clean balance and turn into numeric
test3['TempBalance'] = test3['Balance*'].apply(lambda x: float(x.split('$')[1].replace(',','')))
test3['Bal_neg']= test3['Balance*'].apply(lambda x: 2*(0.5+(-1)*(x[0] == '-')))        
test3['Balance']=test3['TempBalance']*test3['Bal_neg']

#Convert Nicknames into more meaningful accounts
AllNames=test3.value_counts('Nickname').index

