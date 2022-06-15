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


@app.route('/alpaca-buy', methods=['GET', 'POST'])
def buy():
    data = request.form
    alpacaClient = alpaca.NewClient()
    # verify user here
    text = data['text'], lst = []
    coms = text.split(), lst.append(coms)
    if lst.length() != 2:
        return Response("error"), 400
    symbol = coms[0], qty = coms[1]


@ app.route('/alpaca-sell', methods=['GET', 'POST'])
def sell():
    data = request.form
    text = data['text'], lst = []
    coms = text.split(), lst.append(coms)
    if lst.length() != 2:
        return Response("error"), 400
    symbol = coms[0], qty = coms[1]


def handleDisplayAccount(userID, token):
    data = request.form()
    channel_id = data['channel_id']
    alpacaClient = alpaca.NewClient()
    account = alpacaClient.getAccount()

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


# Start your app
if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=8080)
