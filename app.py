import os, slack, requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort, redirect
from slackeventsapi import SlackEventAdapter
import alpaca_trade_api as alpaca
import config
import psycopg2

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

#DB_USER, DB_PASSWORD, DB_NAME = os.environ['DBUSER'], os.environ['DBPASSWORD'], os.environ['DBNAME']

BOT_ID = client.api_call("auth.test")['user_id']
BASE_TOKEN_URL = "https://api.alpaca.markets/oauth/token"
NGROK = "https://a272-152-44-181-213.ngrok.io"
BASE_ALPACA_PAPER_URL = 'https://paper-api.alpaca.markets'
# BASE_ALPACA_URL = 'https://api.alpaca.markets'
   
# Initializes your app with your bot token and signing secret


@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    cur, conn = connect_DB()
    data = request.form
    text = data['text'] 
    user_id = data['user_id']
    access_token = get_AccessToken(cur, conn, user_id)
    if text == "connect":
        return Response("https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=0c76f3a44caa688859359cab598c9969" + 
        "&redirect_uri=" + NGROK + "/auth&scope=account:write%20trading%20data&state=" + user_id), 200
    # elif text == "display":
    #     return Response(handleDisplayAccount(user_id, 0)), 200
    elif text == "account":
        return Response("NO")

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
            'client_id': os.environ['ALPACA_CLIENT_ID'],
            'client_secret': os.environ['ALPACA_CLIENT_SECRET'],
            'redirect_uri': redirect_uri
        })
        #set user's authentication status to true
    access_token = access_response.json()['access_token']
    print(access_token + ' <---- this is the access token')
    if access_token != "":
        cur.execute('insert into token (user_id, access_token) values (%s, %s)', (
            user_id, access_token))
        conn.commit()
        cur.close()
        conn.close()
    return redirect("https://app.slack.com/client")
   

@app.route('/alpaca-buy', methods=['GET', 'POST'])
def buy():
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


@app.route('/alpaca-sell', methods=['GET', 'POST'])
def sell():
    # Try to connect to DB
    cur, conn = connect_DB()

    data = request.form

    # Retrieve the user_id and text from slash command
    symbol, qty, user_id = get_params(data)

    # Get the access token from DB if the user_id exists and close the DB connection
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    # Try placing a sell order
    order = placeOrder(symbol, qty, 'sell', headers)

    if order.status_code == 200 and order.json()['status'] == 'accepted':
        return Response(f'Sold {qty} {symbol} on Alpaca!'), 200
    else:
        return Response("Error selling"), 200


@app.route('/alpaca-account', methods=['GET', 'POST'])
def AccountInfo():
    # Try to connect to DB
    cur, conn = connect_DB()

    data = request.form

    user_id = data['user_id']

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    accountInfo = requests.get(
        '{0}/v2/account'.format(BASE_ALPACA_PAPER_URL), headers=headers)

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

@app.route('/alpaca-positions', methods=['GET', 'POST'])
def get_positions():
    cur, conn = connect_DB()

    data = request.form

    user_id = data['user_id']

    # Get the access token from DB if the user_id exists
    access_token = get_AccessToken(cur, conn, user_id)

    headers = {'Authorization': 'Bearer ' + access_token}

    # Make request to get account's positions
    positions = requests.get(
        '{0}/v2/positions'.format(BASE_ALPACA_PAPER_URL), headers=headers)

    # Store the Json object and set up dictionary for display
    positions = positions.json()

    list_positions = {
        'symbols' : [], 
        'current_price' : [] 
    }
    
    # Format each position within positions
    for pos in positions:
        list_positions['symbols'].append(pos['symbol'])
        list_positions['current_price'].append(pos['current_price'])

    print(list_positions)
    return Response(list_positions), 200

## HELPER FUNCTIONS BELOW
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
            'SELECT access_token FROM token WHERE user_id = %s', (user_id,))
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
    app.run(debug=True)