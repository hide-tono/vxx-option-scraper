'''
Copyright (C) 2017, hide-tono
Class fetching options data from www.nasdaq.com
option_scraper
QuantCorner @ http://tono-n-chi.com/blog
'''
import re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


class NasdaqOptions(object):
    '''
    Class NasdaqOptions fetches options data from Nasdaq website

    User inputs:
        Ticker: ticker
            - Ticker for the underlying
        Moneyness: money
            - All moneyness: all
            - In-the-money: in
            - Out-of-the-money: out
            - Near the money: near
        Market: market
            - Composite quote: Composite
            - Chicago Board Options Exchange: CBO
            - American Options Exchange: AOE
            - New York Options Exchange: NYO
            - Philadelphia Options Exchange: PHO
            - Montreal Options Exchange: MOE
            - Boston Options Exchange: BOX
            -  International Securities Exchange: ISE
            - Bats Exchange Options Market: BTO
            - NASDAQ Options: NSO
            - C2(Chicago) Options Exchange: C2O
            - NASDAQ OMX BX Options Exchange: BXO
            - MIAX: MIAX
        Option category: expi
            - Weekly options: week
            - Monthly options: stand
            - Quarterly options: quart
            - CEBO options (Credit Event Binary Options): cebo
    '''

    def __init__(self, ticker, money='near', market='cbo', expi='stan'):
        self.ticker = ticker
        # self.type = type   # Deprecated
        self.market = market
        self.expi = expi
        if money == 'near':
            self.money = ''
        else:
            self.money = '&money=' + money

    def get_options_table(self, nearby):
        '''
        - Loop over as many webpages as required to get the complete option table for the
        option desired
        - Return a pandas.DataFrame() object
        '''
        self.nearby = nearby
        # Create an empty pandas.Dataframe object. New data will be appended to
        old_df = pd.DataFrame()

        # Variables
        loop = 0  # Loop over webpages starts at 0
        page_nb = 1  # Get the top of the options table
        flag = 1  # Set a flag that will be used to call get_pager()
        old_rows_nb = 0  # Number of rows so far in the table

        # Loop over webpages
        while loop < int(page_nb):
            # Construct the URL
            '''url = 'http://www.nasdaq.com/symbol/' + self.ticker + '/option-chain?dateindex='\
               + str(self.nearby) + '&callput=' + self.type + '&money=all&expi='\
               + self.expi + '&excode=' + self.market + '&page=' + str(loop+1)'''
            url = 'http://www.nasdaq.com/symbol/' + self.ticker + '/option-chain?excode=' + self.market + self.money + '&expir=' + self.expi + '&dateindex=' + str(self.nearby) + '&page=' + str(loop + 1)

            # Query NASDAQ website
            try:
                response = requests.get(url)  # , timeout=0.1)
            # DNS lookup failure
            except requests.exceptions.ConnectionError as e:
                print('''Webpage doesn't seem to exist!\n%s''' % e)
                pass
            # Timeout failure
            except requests.exceptions.ConnectTimeout as e:
                print('''Slow connection!\n%s''' % e)
                pass
            # HTTP error
            except requests.exceptions.HTTPError as e:
                print('''HTTP error!\n%s''' % e)
                pass

            # Get webpage content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Determine actual number of pages to loop over
            if flag == 1:  # It is run only once
                # Get the number of page the option table lies on
                last_page_raw = soup.find('a', {'id': 'quotes_content_left_lb_LastPage'})
                last_page = re.findall(pattern='(?:page=)(\d+)', string=str(last_page_raw))
                page_nb = ''.join(last_page)
                # 1ページ分しかない場合はページ移動のリンク自体が表示されない
                if page_nb == '':
                    page_nb = 1
                flag = 0

            # Extract table containing the option data from the webpage
            table = soup.find_all('table')[5]  # table #5 in the webpage is the one of interest

            # Extract option data from table as a list
            elems = table.find_all('td')  # Python object
            lst = [elem.text for elem in elems]  # Option data as a readable list

            # Rearrange data and create a pandas.DataFrame
            arr = np.array(lst)
            reshaped = arr.reshape(int(len(lst) / 16), 16)
            new_df = pd.DataFrame(reshaped)
            frames = [old_df, new_df]
            old_df = pd.concat(frames)
            rows_nb = old_df.shape[0]

            # Increment loop counter
            if rows_nb > old_rows_nb:
                loop += 1
                old_rows_nb = rows_nb
            elif rows_nb == old_rows_nb:
                print('Problem while catching data.\n## You must try again. ##')
                pass
            else:  # Case where rows have been deleted
                # which shall never occur
                print('Failure!\n## You must try again. ##')
                pass

        # Name the column 'Strike'
        old_df.rename(columns={old_df.columns[8]: 'Strike'}, inplace=True)

        ## Split into 2 dataframes (1 for calls and 1 for puts)
        calls = old_df.ix[:, 0:7]
        puts = old_df.ix[:, 9:16]  # Slicing is not incluse of the last column

        # Set 'Strike' column as dataframe index
        calls = calls.set_index(old_df['Strike'])
        puts = puts.set_index(old_df['Strike'])

        ## Headers names
        headers = ['Day', 'Last', 'Chg', 'Bid', 'Ask', 'Vol', 'OI']
        calls.columns = headers
        puts.columns = headers

        return calls, puts


if __name__ == '__main__':
    options = NasdaqOptions('VXX')
    for i in range(7):
        calls, puts = options.get_options_table(i)
        call.to_csv('2017')
        # Write on the screen
        print('\n######\nCalls:\n######\n', calls, '\n\n######\nPuts:\n######\n', puts)
