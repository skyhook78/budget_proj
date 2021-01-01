# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 10:13:26 2020

Scraping.py - Logs into NAB internet banking and scrapes transactions. 
Uses Selenium, beautifulsoup, and chrome driver (copied into path)

Some code and ideas adapted from https://github.com/ArtS/nab-export
Transactions are outputted to a csv (raw_transactions.csv) for further cleaning

@author: Jonno Khoo
"""

##Imports

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from getpass import getpass
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.support.ui import Select

#Constants - dates of transactions. Note that NAB can only download the last 2 years of transactions
start_date='03/01/19'
end_date='01/01/21'

#Custom functions.
def get_credentials(filename):
    """
    -Looks for a file (called filename). 
    - If there is one, obtain username and password from the file 
    (username first line, password second line)
    - If file isn't available, prompt for user to enter filename and password
    """

    try:
        with open(filename, 'r') as f:
            lines = f.read().split('\n')

            if len(lines) < 2:
                print ('\n\n\tIt looks like there\'s only ' + str(len(lines)) + ' line in .credentials file')
                print ('\tPlease ensure the file contains two lines,')
                print ('\tfirst line - username, second line - password')
                print ('\n\n')
                return None

            return lines

    except Exception as e:
        lines = []
        print('Could not find .credentials file. Please enter username and password')
        print('Username:')
        lines.append(input())
        lines.append(getpass())

        return lines

# Custom function to select a box option using the selenium action object.
def dropdown_selector(box):
    """
    Select the last option in a dropdown box menu
    Element you are wanting to click is the variable box
    """    
    
    box.click()
    action = ActionChains(driver)
    action.move_to_element_with_offset(to_element=box,xoffset=245,yoffset=-24)
    action.click_and_hold()
    action.pause(3)
    action.release
    action.move_to_element_with_offset(to_element=box,xoffset=125,yoffset=-24)
    action.double_click()
    action.perform()
    
    return None

details=get_credentials('.credentials')
# Webdriver setup and website login
driver = webdriver.Chrome()
driver.implicitly_wait(15)
driver.maximize_window() 
driver.get('https://ib.nab.com.au/nabib/index.jsp')

driver.find_element_by_id('userid').send_keys(details[0])
driver.find_element_by_id('password').send_keys(details[1])
driver.find_element_by_id('loginBtn').click()

#Get list of account links and account details
links = driver.find_elements_by_xpath('//div[@class="account-nickname"]')
accounts = driver.find_elements_by_xpath('//div[@class="account-number "]')


link_list = []
for l in range(len(links)):
    link_list.append(links[l].text)


account_list = []
for l in range(len(accounts)):
    account_list.append(accounts[l].text)

    
df_transactions_all=pd.DataFrame()

  
# Loop through all accounts and get the transaction history.

for l in range(len(link_list)):
    
    print('Getting transaction history for ',link_list[l])
    driver.find_element_by_link_text(link_list[l]).click()
    
    #Shows the filter options, selects custom date range and selects the right range
    driver.find_element_by_xpath('//button[@class="btn btn-primary filter-button"]').click()


     
     
    #Define constants and select web elements
    date_range=driver.find_element_by_xpath('//div[@id="input-transaction-period"]')
    per_page_button=driver.find_element_by_xpath('//div[@id="input-page-size"]')

    
    ##### Select the correct custom date range, add the date range details, and display 200 transactions per page.
    dropdown_selector(per_page_button)  
    dropdown_selector(date_range)
    start_elem=driver.find_element_by_id('start-date')
    end_elem=driver.find_element_by_id('end-date')
    start_elem.clear()
    start_elem.send_keys(start_date)
    driver.find_element_by_xpath('//button[@id="displayBtn"]').click()
    end_elem.clear()
    end_elem.send_keys('01/01/2020')
    #Temp code to make it work with buggy calendar
    cal_icon = driver.find_element_by_xpath('//button[@id="displayBtn"]')
    cal_icon.click()
    dateclick = ActionChains(driver)
    dateclick.send_keys(Keys.ARROW_LEFT)
    dateclick.perform()
    driver.find_element_by_xpath('//button[@id="displayBtn"]').click()    

    end_elem.clear()
    end_elem.send_keys(end_date)
    driver.find_element_by_xpath('//button[@id="displayBtn"]').click()
    ActionChains(driver).pause(3).perform()
    
    
    complete = False
    
    # Now that pages are set up, cycle through and scrape to the master dataframe.
    while not complete:    
             
        #Get page info element as a text list. Last element is total number of pages, 3rd last element is current page
        #If page info doesn't exist, assume there is only one page of transactions and scrape them
        
        try:
            pages=driver.find_element_by_xpath('//p[@id="currentPageInfo"]').text.rsplit()
        except:
            #select and scrape the transaction history, add to transaction all dataframe.
            ActionChains(driver).pause(3).perform()
            transaction_table=driver.find_element_by_xpath('//table[@class="transaction-history-table"]').get_attribute('outerHTML')
            soup = BeautifulSoup(transaction_table, 'html.parser')
            df_transactions = pd.read_html(str(soup))[0]
            df_transactions['Nickname']=link_list[l]
            df_transactions['Account']=account_list[l] 
            df_transactions_all=pd.concat([df_transactions_all,df_transactions])
            complete = True
            print('Account extraction for time period',start_date,'to', end_date, 'is complete')
            driver.get('https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl#/')            
        else:        
            print('Parsing page ',pages[-3],' of ', pages[-1])
            
            #select and scrape the transaction history, add to transaction all dataframe.
            ActionChains(driver).pause(3).perform()
            transaction_table=driver.find_element_by_xpath('//table[@class="transaction-history-table"]').get_attribute('outerHTML')
            soup = BeautifulSoup(transaction_table, 'html.parser')
            df_transactions = pd.read_html(str(soup))[0]
            df_transactions['Nickname']=link_list[l]
            df_transactions['Account']=account_list[l] 
            df_transactions_all=pd.concat([df_transactions_all,df_transactions])
            
            if pages[-3] == pages[-1]:
                complete = True
                print('Loop completed')
                print('Account extraction for time period',start_date,'to', end_date, 'is complete')
                driver.get('https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl#/')
            else:
                driver.find_element_by_xpath('//button[@class="btn btn-pagination nextBtn"]').click()
        
        

#Save dataframe to csv for cleaning
df_transactions_all.to_csv('raw_transactions.csv')


