#Pull data
import sqlite3
from sqlite3 import Error
import os.path

#Perform manipulations
import pandas as pd
import numpy as np
import statistics
import datetime as datetime


#Connect to DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "S&P-500-Stock-Data-(2013-2018).db")
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
except Error as e:
    print(e)


def get_tickers():
    """
    Loop through all the unique tickers and gather them in a name.
    """

    c.execute('SELECT DISTINCT Name FROM "S&P-500"')
    names = c.fetchall()

    tickers = []
    for name in names:
        if name not in tickers:
            tickers.append(name[0])

    return tickers


def calculate_RSI(ticker):
    """
    Pull date, closing prices, and volume values from S&P-500 database to return a dataframe containing the
    items, as well as the calculated 14-day RSI.
    """

    #Data pull
    pull_query = (('SELECT Date, Close, Volume FROM "S&P-500" WHERE Name = "{}"').format(ticker))
    c.execute(pull_query)

    items = c.fetchall()

    ticker_dates = [date[0] for date in items] #ticker datetime
    ticker_prices = [price[1] for price in items] #ticker closing price
    ticker_volumes = [volume[2] for volume in items] #volume of trades for a given ticker

    df = pd.DataFrame(np.column_stack([ticker_dates, ticker_prices, ticker_volumes]), columns = ['Date', 'Price', 'Volume'])
    df["Date"] = pd.to_datetime(df["Date"])#, format = '%Y-%m-%d')
    #df = df.set_index('Date')
    df["Price"] = pd.to_numeric(df["Price"])
    df["Volume"] = pd.to_numeric(df["Volume"])

    #Price change
    price_change = [round(next - current, 4) for current,next in zip(ticker_prices,ticker_prices[1:])] #For each iteration, subtract the current price from the next in the list.  For each difference calculated, round the value to the 4th decimal place

    #Up & Down movement
    UpChange = []
    DownChange = []
    for movement in price_change:
        if movement > 0:
            UpChange.append(movement)
            DownChange.append(0)
        elif movement < 0:
            UpChange.append(0)
            DownChange.append(abs(movement)) #Makes sure that price drops are still represented with positive numbers
        elif movement == 0:
            UpChange.append(0)
            DownChange.append(0)

    #Average Up & Down movement 14-day
    RSI_period = 14

    AvgUpChange = []
    AvgDownChange = []

    initial_avg_up = statistics.mean(UpChange[0:(RSI_period -1)])
    initial_avg_down = statistics.mean(DownChange[0:(RSI_period -1)])

    AvgUpChange.append(initial_avg_up)
    AvgDownChange.append(initial_avg_down)

    for up_value, down_value in zip(UpChange[RSI_period:], DownChange[RSI_period:]):

        avg_up_value = ((AvgUpChange[-1] * 13) + up_value) / 14
        AvgUpChange.append(avg_up_value)

        avg_down_value = ((AvgDownChange[-1] * 13) + down_value) / 14
        AvgDownChange.append(avg_down_value)

        RSI_period += 1

    #Relative Strength Index calculation
    RSI = []
    for u,d in zip(AvgUpChange, AvgDownChange):
        RS = u / d
        final_value = 100 - (100/(RS + 1))
        RSI.append(round(final_value,4))

    """
    Use this portion of the code to ensure the RSI Series concatonates from the 14th element down, and not at the top of the column.
    """
    RSI = pd.Series(RSI)

    size_diff = df.shape[0] - RSI.shape[0]
    RSI.index = df.index[size_diff:]
    df = pd.concat((df, RSI.rename('RSI')), axis=1)

    #RSI breach indexer
    RSI_breach = []

    for score in df.RSI:
        if score > 70:
            RSI_breach.append(score - 70)
        elif score < 30:
            RSI_breach.append(score - 30)
        elif pd.isnull(score) == True:
            RSI_breach.append(None)
        else:
            RSI_breach.append(0)

    df['RSI Breach'] = pd.Series(RSI_breach)

    return df



#def load_data(): # While there are far simpler functions to load using pandas, this approach is employed for the sake of practicing SQL syntax
    #c.execute('IF NOT EXISTS(SELECT RSI, RSI_breach FROM "S&P-500")')
    #c.execute(('INSERT {} INTO "S&P-500" ORRRRR INTO RSI WHERE Name = {}').format(df['RSI'], ticker)))
    # BEGIN
    # ALTER TABLE "S&P-500"
    # ADD [column_name] FLOAT
    # END'"
