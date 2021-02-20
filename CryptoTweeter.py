import pandas as pd
import pandas_ta as ta
import numpy as np
import cbpro
import datetime as datetime
import matplotlib.pyplot as plt
import tweepy
import datetime as datetime


def get_products(public_client):
    products = public_client.get_products()
    product_list = []
    for i in range(len(products)):
        if products[i]["id"].split("-")[1] == "USD":
            product_list.append(products[i]["id"])
    product_list = sorted(product_list)
    return product_list

def get_MACD(df):
    MACD = ta.macd(df.close)
    crosses = np.argwhere(np.diff(np.sign(MACD["MACD_12_26_9"] - MACD["MACDs_12_26_9"]))).flatten()
    buy_signal = []
    sell_signal = []
    buy_index = []
    sell_index = []
    values = []
    values2 = []
    for i in (MACD["MACD_12_26_9"][crosses]):
        values.append(i)
    for i in (MACD["MACDs_12_26_9"][crosses]):
        values2.append(i)
    for i in range(len(values)):
        if values[i] > values2[i]:
            buy_index.append(MACD["MACD_12_26_9"][crosses].index[i])
            buy_signal.append(values[i])
        elif values[i] <= values2[i]:
            sell_index.append(MACD["MACDs_12_26_9"][crosses].index[i])
            sell_signal.append(values2[i])
    return (buy_signal, sell_signal, buy_index, sell_index)

def add_cols(new_df, period = 20):
    new_df["SMA"] = new_df["close"].rolling(window = period).mean()
    new_df["STD"] = new_df["close"].rolling(window = period).std()
    new_df["Upper"] = new_df["SMA"] + (new_df["STD"] * 2)
    new_df["Lower"] = new_df["SMA"] - (new_df["STD"] * 2)
    return new_df


def bollinger_plot(company_name, new_df, time=0):
    fig = plt.figure(figsize=(20, 20))
    ax0 = fig.add_subplot(211)
    ax1 = fig.add_subplot(212)
    x_axis = new_df.index[time:]
    MACD = ta.macd(new_df.close)
    buy_signal, sell_signal, buy_index, sell_index = get_MACD(new_df)

    ax0.fill_between(x_axis, new_df["Upper"][time:], new_df["Lower"][time:], color="grey")
    ax0.plot(x_axis, new_df["close"][time:], color="Gold", lw=2, label="Close price")
    ax0.plot(x_axis, new_df["SMA"][time:], color="Blue", lw=2, label="SMA")

    ax1.bar(MACD["MACDh_12_26_9"].index, MACD["MACDh_12_26_9"], label="bar")
    ax1.plot(MACD['MACD_12_26_9'], label="MACD")
    ax1.plot(MACD["MACDs_12_26_9"], label="MACDS")
    ax1.scatter(buy_index, buy_signal, color="red", label="sell signal", marker="v", alpha=1)
    ax1.scatter(sell_index, sell_signal, color="green", label="buy signal", marker="^", alpha=1)

    ax0.legend()
    ax1.legend()

    ax0.title.set_text(company_name)
    ax1.title.set_text(company_name)
    # fig.tight_layout()
    fig.tight_layout()
    return fig

def get_new(new_df):
    new_df["Bollinger Buy"] = get_signal(new_df)[0]
    new_df["Bollinger Sell"] = get_signal(new_df)[1]
    return new_df

def get_signal(data):
    buy_signal = []
    sell_signal = []
    for i in range(len(data["close"])):
        if data["close"][i] > data["Upper"][i]:
            buy_signal.append(np.nan)
            sell_signal.append(data["close"][i])
        elif data["close"][i] < data["Lower"][i]:
            buy_signal.append(data["close"][i])
            sell_signal.append(np.nan)
        else:
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)
    return (buy_signal, sell_signal)

def get_signals(public_client, api):
    product_list = get_products(public_client=public_client)
    for product in product_list:
        buy = False
        sell = False
        currency = product
        start = (datetime.datetime.now() - datetime.timedelta(days=75))
        end = datetime.datetime.now()
        df = public_client.get_product_historic_rates(currency, start=start.isoformat(), end=end.isoformat(),
                                                      granularity=21600)
        df.reverse()
        df = pd.DataFrame(df)
        df = df.rename(columns={0: "time", 1: "low", 2: "high", 3: "open", 4: "close", 5: "volume"})
        fig = bollinger_plot(currency, get_new(add_cols(df)), time=0)
        MACD = ta.macd(df.close)
        buy_signal, sell_signal, sell_index, buy_index = get_MACD(df)
        length = len(MACD)
        RSI = ta.rsi(df.close)
        for i in buy_index:
            if (length - 2 == i or length - 3 == i):
                buy = True
        for j in sell_index:
            if (length - 2 == j or length - 3 == j):
                sell = True
        if buy:
            index = i
            current_rsi = RSI[index]
            ids = []

            fig.savefig("Test.jpg")
            media = api.media_upload("Test.jpg")
            ids.append(media.media_id)
            message = "Buy trade signal for " + currency + " with RSI: " + str(int(current_rsi)) + " #" + \
                      currency.split("-")[0]
            api.update_status(media_ids=ids, status=message)
        elif sell:
            index = i
            current_rsi = RSI[index]
            ids = []

            fig.savefig("Test.jpg")
            media = api.media_upload("Test.jpg")
            ids.append(media.media_id
            message = "Sell trade signal for " + currency + " with RSI: " + str(int(current_rsi)) + " #" + \
                      currency.split("-")[0]
            api.update_status(media_ids=ids, status=message)


api = tweepy.API(auth)
public_client = cbpro.PublicClient()
get_signals(public_client = public_client, api = api)
