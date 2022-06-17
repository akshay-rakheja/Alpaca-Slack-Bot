import os
import re
import slack
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort, redirect
from slackeventsapi import SlackEventAdapter
# import alpaca_trade_api as alpaca
import config
from slack_sdk import WebClient
import psycopg2


# Configure flask app
app = Flask(__name__)
slackeventadapter = SlackEventAdapter(
    config.SLACK_SIGNING_SECRET, "/slack/events", app)

client = WebClient(token=config.SLACK_TOKEN)


BOT_ID = client.api_call("auth.test")['user_id']

# Authentication URL to retrieve access_token from Alpaca
BASE_TOKEN_URL = "https://api.alpaca.markets/oauth/token"


# Alpaca API endpoints
BASE_ALPACA_PAPER_URL = 'https://paper-api.alpaca.markets'
BASE_ALPACA_LIVE_URL = 'https://api.alpaca.markets'
ALPACA_CLIENT_ID = config.ALPACA_CLIENT_ID
ALPACA_CLIENT_SECRET = config.ALPACA_CLIENT_SECRET


NGROK = "https://6825-192-159-178-211.ngrok.io"


@app.route('/alpaca2-live', methods=['GET', 'POST'])
def alpaca():
    print("Entering LIVE!!!!!!!")
    cur, conn = connect_DB()
    data = request.form
    text = data['text']
    user_id = data['user_id']
    access_token = get_AccessToken(cur, conn, user_id)
    return Condition(text, user_id, 'live', access_token, data)


@app.route('/alpaca2-paper', methods=['GET', 'POST'])
def paper():
    print("Entering Paper!!!!!")
    cur, conn = connect_DB()
    data = request.form
    text = data['text']
    user_id = data['user_id']
    access_token = get_AccessToken(cur, conn, user_id)
    message = Condition(text, user_id, 'paper', access_token, data)
    print("ERROR!!!")
    return(message)


def Condition(text, user_id, live, access_token, data):
    if text == '':
        return Response("Please enter a command. Possible commands are: \n /alpaca connect : Connect your Alpaca account with Slack,\n /alpaca disonnect: Disconnect your Alpaca account from Slack,\n /alpaca-buy SYMBOL QTY: Place a BUY order on Alpaca for a given SYMBOL and QTY,\n  /alpaca-sell SYMBOL QTY: Place a SELL order on Alpaca for a given SYMBOL and QTY, /alpaca positions: Get your current positions on Alpaca,\n /alpaca orders: Get Open orders,\n /alpaca status: Connection status between Alpaca and Slack\n"), 200

    elif text == "connect" and access_token == None:
        print("Connecting user: ", user_id)
        return Response("Please follow the link to authorize this application to connect to your Alpaca account: https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=" + ALPACA_CLIENT_ID +
                        "&redirect_uri=" + NGROK + "/auth&scope=account:write%20trading%20data&state=" + user_id), 200

    elif text == "connect" and access_token != None:
        print("hello")
        return Response("You are already authenticated! Try out our other commands -> /alpaca-buy | /alpaca-sell | /alpaca account | /alpaca positions"), 200

    elif text == "disconnect" and access_token != None:
        disconnectUser(user_id)
        return Response("Your Alpaca account has been disconnected. Re-connect to Alpaca by typing /alpaca connect"), 200

    elif text == "account" and access_token != None:
        return AccountInfo(user_id, live)

    elif text == "positions" and access_token != None:
        return GetPositions(user_id, live)

    elif text == "orders" and access_token != None:
        return GetOrders(user_id, live)

    elif text == 'status' and access_token != None:
        print('Checking STATUS!!!!!!!!!')
        return Response("Your Alpaca account is connected!")

    elif len(text.split()) > 1 and access_token != None:
        print(access_token)
        return trade(data, live)
    elif text == 'status' and access_token == None:
        return Response("Your Alpaca account is not connected!. Please try connecting using '/alpaca connect' command.")

    else:
        return Response("Invalid Command -> try 'connect', 'account', or 'positions'")


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    cur, conn = connect_DB()
    # need to check if already authenticated, gives error right now
    auth_code = request.args.get("code")
    user_id = request.args.get("state")
    print(auth_code + 'this is the auth code')
    redirect_uri = NGROK + '/auth'
    if auth_code != "":
        access_response = requests.post(BASE_TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': config.ALPACA_CLIENT_ID,
            'client_secret': config.ALPACA_CLIENT_SECRET,
            'redirect_uri': redirect_uri
        })
        # set user's authentication status to true
    access_token = access_response.json()['access_token']
    print(access_token + ' <---- this is the access token')
    if access_token != "":
        cur.execute('insert into token_table (user_id, access_token) values (%s, %s)', (
            user_id, access_token))
        conn.commit()
        cur.close()
        conn.close()
    return redirect("https://app.slack.com/client")


def trade(data, live):
    # Try to connect to DB
    cur, conn = connect_DB()
    # Retrieve the user_id and text from slash command
    side, symbol, qty, user_id = get_params(data)

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    if access_token == None:
        return Response('You must connect your account with Alpaca by authenticating first. Use /alpaca connect to connect your Alpaca account with Slack.'), 200

    headers = {'Authorization': 'Bearer ' + access_token}

    # Try placing a buy order

    order = placeOrder(symbol, qty, side, headers, live)
    print(order.json())
    order_status = order.json()['status']
    if order.status_code == 200:
        if side == 'buy':
            return Response(f'Bought {qty} {symbol} on Alpaca. Order Status: {order_status}'), 200
        else:
            return Response(f'Sold {qty} {symbol} on Alpaca. Order Status: {order_status}. If it is pending_new, it will settle momentarily. You can check for any open order through "/alpaca orders" command'), 200
    else:
        return Response("Error buying/selling"), 200


def AccountInfo(user_id, live):
    # Try to connect to DB
    cur, conn = connect_DB()

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    if live == 'paper':
        accountInfo = requests.get(
            '{0}/v2/account'.format(BASE_ALPACA_PAPER_URL), headers=headers)
    else:
        accountInfo = requests.get(
            '{0}/v2/account'.format(BASE_ALPACA_LIVE_URL), headers=headers)

    accountInfo = accountInfo.json()
    # gather the values from account
    commands = {
        "an": accountInfo['account_number'],
        "eq": "$" + accountInfo['equity'],
        "lmv": "$" + accountInfo['long_market_value'],
        "smv": "$" + accountInfo['short_market_value'],
        "ct": "$" + str(float(accountInfo['equity'])-float(accountInfo['last_equity'])),
        "bp": "$" + accountInfo['buying_power']
    }

    # display the account values
    message = "Account Number: {} | Equity: {} | Long Market Value {} | Short Market Value {} | Change Today {} | Buying Power {} ".format(
        commands["an"], commands["eq"], commands["lmv"], commands["smv"], commands["ct"], commands["bp"])
    print("THIS IS THE MESSAGE----> " + message)
    return Response(message), 200


def GetPositions(user_id, live):
    cur, conn = connect_DB()

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    # Make request to get account's positions
    if live == 'paper':
        positions = requests.get(
            '{0}/v2/positions'.format(BASE_ALPACA_PAPER_URL), headers=headers)
    else:
        positions = requests.get(
            '{0}/v2/positions'.format(BASE_ALPACA_LIVE_URL), headers=headers)

    # Store the Json object and set up dictionary for display
    positions = positions.json()
    positions_list = {}
    for pos in positions:
        positions_list[pos['symbol']] = [pos['qty'], pos['unrealized_pl']]

    prepend = 'Positions:\n\nSymbol\t|\tQty\t|\tUnrealized P/L\n'
    positions_string = printIt(prepend, positions_list)

    return Response(positions_string), 200


def GetOrders(user_id):
    cur, conn = connect_DB()
    access_token = get_AccessToken(cur, conn, user_id)
    headers = {'Authorization': 'Bearer ' + access_token}

    # Make request to get account's positions
    orders = requests.get(
        '{0}/v2/orders'.format(BASE_ALPACA_PAPER_URL), headers=headers)
    orders = orders.json()
    print(orders)
    return Response(""), 200

# HELPER FUNCTIONS BELOW


def connect_DB():
    # Try to connect to DB
    try:
        # connect to db
        conn = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME,
                                user=config.DB_USER, password=config.DB_PASSWORD)
        # Open Cursor
        cur = conn.cursor()
    except:
        print("Error connecting to DB")

    return cur, conn


def get_AccessToken(cur, conn, user_id):
    # Get the access token from DB if the user_id exists
    try:
        cur.execute(
            'SELECT access_token FROM token_table WHERE user_id = %s', (user_id,))

        access_token = cur.fetchone()[0]
        cur.close()
        conn.close()
        return access_token
    except(Exception, psycopg2.DatabaseError) as error:
        print("Error getting access token: ", error)


def get_params(data):
    # Retrieve command args and verify user here
    # TODO: error checking for bad args
    try:
        text = data['text']
        user_id = data['user_id']
        params = text.split()
        side = params[0].lower()
        qty = params[1]
        symbol = params[2].upper()
        print(symbol + ' <---- this is the symbol')
        print(qty + ' <---- this is the qty')
        print(user_id + ' <---- this is the user id')
    except:
        print("Error getting data from slash command, perhaps missing/incorrect args")

    return side, symbol, qty, user_id


def placeOrder(symbol, qty, side, headers, live):
    # Try placing a sell order
    try:
        if live == 'paper':
            order = requests.post(
                '{0}/v2/orders'.format(BASE_ALPACA_PAPER_URL), headers=headers, json={
                    'symbol': symbol,
                    'qty': qty,
                    'side': side,
                    'type': 'market',
                    'time_in_force': 'gtc',
                })

        else:
            order = requests.post(
                '{0}/v2/orders'.format(BASE_ALPACA_LIVE_URL), headers=headers, json={
                    'symbol': symbol,
                    'qty': qty,
                    'side': side,
                    'type': 'market',
                    'time_in_force': 'gtc',
                })

        return order

    except Exception as e:
        return Response("There was an issue posting order to Alpaca: {0}".format(e))


def disconnectUser(user_id):
    cur, conn = connect_DB()
    try:
        cur.execute(
            'DELETE FROM token WHERE user_id = %s', (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print("Error removing user and access token: ", error)


def printIt(prepend, dictionary):

    stuff = ''
    stuff = stuff + prepend
    for key, value in dictionary.items():
        stuff += str(key) + '\t|\t' + \
            str(value[0]) + '\t|\t' + str(value[1]) + '\n'
    return stuff


# Start your app
if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=8080)
