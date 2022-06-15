import os
import re
import slack
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort, redirect
from slackeventsapi import SlackEventAdapter
import alpaca_trade_api as alpaca
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


@app.route('/alpaca2', methods=['GET', 'POST'])
def alpaca():
    # Retrieve the user_id and text from slash command
    data = request.form
    text = data['text']
    user_id = data['user_id']
    print(user_id)

    url = "https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=1d5c0276b371931fdf8077209a90e460" + \
        "&redirect_uri=https://0c0a-192-159-178-211.ngrok.io/auth&scope=account:write%20trading%20data&state="+user_id
    print(url)
    # if the user mentions connect with /alpaca, redirect to alpaca login
    if text == "connect":
        return Response(url), 200
    elif text == "display":
        return Response(handleDisplayAccount(user_id, 0)), 200
    elif text == "":
        return Response("HI"), 200


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    # connect to db
    conn = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME,
                            user=config.DB_USER, password=config.DB_PASSWORD)
    # Open Cursor
    cur = conn.cursor()

    # Retrieve auth_code and user_id from request
    auth_code = request.args.get("code")
    user_id = request.args.get("state")
    print(request.args)
    print(auth_code + ' <---- this is the auth code')

    # If the auth code is not empty, then we can make the request to get the access token
    if auth_code != "":
        try:
            access_response = requests.post(BASE_TOKEN_URL, data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': config.ALPACA_CLIENT_ID,
                'client_secret': config.ALPACA_CLIENT_SECRET,
                'redirect_uri': 'https://0c0a-192-159-178-211.ngrok.io/auth'
            })
        except:
            print("Error sending request to get access token")

    # retrieve the auth token from the response
    try:
        access_token = access_response.json()['access_token']
    except:
        print("Error getting access token")

    print(access_token + ' <---- this is the access token')
    print(user_id + ' <---- this is the user id')

    # If the access token and user_id are not empty, add them to DB
    try:
        if access_token != "" and user_id != "":
            print("we hit access_token!!!!!")
            cur.execute(
                'insert into token_table (user_id, access_token) values (%s,%s)', (user_id, access_token))
            conn.commit()
        cur.close()
        conn.close()
    except:
        print("Error adding token to DB maybe because user_id already exists")
    return redirect("https://app.slack.com")


@app.route('/alpaca2-buy', methods=['GET', 'POST'])
def buy():

    # Try to connect to DB
    cur, conn = connect_DB()

    data = request.form

    # Retrieve the user_id and text from slash command
    symbol, qty, user_id = get_params(data)

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    # Try placing a buy order
    order = placeOrder(symbol, qty, 'buy', headers)

    if order.status_code == 200 and order.json()['status'] == 'accepted':
        return Response(f'Bought {qty} {symbol} on Alpaca!'), 200
    else:
        return Response("Error buying"), 200


@ app.route('/alpaca2-sell', methods=['GET', 'POST'])
def sell():
    # Try to connect to DB
    cur, conn = connect_DB()

    data = request.form

    # Retrieve the user_id and text from slash command
    symbol, qty, user_id = get_params(data)

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    # Try placing a sell order
    order = placeOrder(symbol, qty, 'sell', headers)

    if order.status_code == 200 and order.json()['status'] == 'accepted':
        return Response(f'Sold {qty} {symbol} on Alpaca!'), 200
    else:
        return Response("Error selling"), 200


@app.route('/alpaca2-accountInfo', methods=['GET', 'POST'])
def displayAccountInfo():
    data = request.form()
    user_id = data['user_id']

    accountInfo = requests.post(
        '{0}/v2/account'.format(BASE_ALPACA_PAPER_URL), headers=headers)

    # gather the values from account
    commands = {
        "an": account.Accountnumber,
        "eq": "$" + account.Equity.String(),
        "lmv": "$" + account.LongMarketValue.String(),
        "smv": "$" + account.ShortMarketValue.String(),
        "ct": "$" + account.Equity.Sub(account.LastEquity).String(),
        "bp": "$" + account.BuyingPower.String()
    }

    # display the account values
    message = "Account Number: {} | Equity: {} | Long Market Value {} | Short Market Value {} | Change Today {} | Buying Power {} ".format(
        commands["an"], commands["eq"], commands["lmv"], commands["smv"], commands["ct"], commands["bp"])

    return message


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
    # TODO: error checking for user_id not in DB then redirect them to enter /alpaca command
    try:
        cur.execute(
            'SELECT access_token FROM token_table WHERE user_id = %s', (user_id,))
        access_token = cur.fetchone()[0]

        print("Here's the access_token: ", access_token)
        cur.close()
        conn.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print("Error getting access token: ", error)

    return access_token


def get_params(data):
    # Retrieve command args and verify user here
    # TODO: error checking for bad args
    try:
        text = data['text']
        lst = []
        user_id = data['user_id']
        params = text.split()
        symbol = params[0]
        qty = params[1]
        print(symbol + ' <---- this is the symbol')
        print(qty + ' <---- this is the qty')
        print(user_id + ' <---- this is the user id')
    except:
        print("Error getting data from slash command, perhaps missing/incorrect args")

    return symbol, qty, user_id


def placeOrder(symbol, qty, side, headers):
    # Try placing a sell order
    try:
        order = requests.post(
            '{0}/v2/orders'.format(BASE_ALPACA_PAPER_URL), headers=headers, json={
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': 'market',
                'time_in_force': 'gtc',
            })

    except Exception as e:
        print("There was an issue posting order to Alpaca: {0}".format(e))

    return order


# Start your app
if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=8080)
