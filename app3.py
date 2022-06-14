import os
import slack
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort, redirect
from slackeventsapi import SlackEventAdapter
import alpaca_trade_api as alpaca
import config
from slack_sdk import WebClient


# Configure flask app
app = Flask(__name__)
slackeventadapter = SlackEventAdapter(
    config.SLACK_SIGNING_SECRET, "/slack/events", app)

client = WebClient(token=config.SLACK_TOKEN)


#DB_USER, DB_PASSWORD, DB_NAME = os.environ['DBUSER'], os.environ['DBPASSWORD'], os.environ['DBNAME']

BOT_ID = client.api_call("auth.test")['user_id']
BASE_TOKEN_URL = "https://api.alpaca.markets/oauth/token"
# BASE_ALPACA_URL = 'https://api.alpaca.markets'
# HEADERS = {'APCA-API-KEY-ID': os.environ['ALPACA_API_KEY'],
#            'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET_KEY']}

# Initializes your app with your bot token and signing secret


@app.route('/alpaca2', methods=['GET', 'POST'])
def alpaca():
    data = request.form
    team_id = data['team_id']
    channel_id = data['channel_id']
    text = data['text']
    user_id = data['user_id']
    print(team_id, channel_id)
    if text == "connect":
        # client.chat_postEphemeral("https://api.alpaca.markets/oauth/grant_type=authorization_code&code=67f74f5a-a2cc-4ebd-88b4-22453fe07994&client_id=fc9c55efa3924f369d6c1148e668bbe8&client_secret=5b8027074d8ab434882c0806833e76508861c366&redirect_uri=https://example.com/oauth/callback")
        return Response("https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=1d5c0276b371931fdf8077209a90e460" +
                        "&redirect_uri=https://13d5-192-159-178-211.ngrok.io/auth&scope=account:write%20trading%20data"), 200
    elif text == "display":
        return Response(handleDisplayAccount(user_id, 0)), 200
    elif text == "":
        return Response("HI"), 200


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    dictionary = {}
    auth_code = request.args.get("code")
    print(auth_code + ' <---- this is the auth code')
    if auth_code != "":
        # json_obj = {
        #     'grant_type': 'authorization_code',
        #     'code': auth_code,
        #     'client_id': config.ALPACA_CLIENT_ID,
        #     'client_secret': config.ALPACA_CLIENT_SECRET,
        #     'redirect_uri': 'https://13d5-192-159-178-211.ngrok.io/auth'
        # }
        # url = (BASE_TOKEN_URL + '?grant_type=authorization_code&code=' + auth_code + '&client_id='
        #        + os.environ['ALPACA_CLIENT_ID'] + '&client_secret=' +
        #        os.environ['ALPACA_CLIENT_SECRET'] + '&redirect_uri='
        #        + 'https://13d5-192-159-178-211.ngrok.io/auth')
        access_response = requests.post(BASE_TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': config.ALPACA_CLIENT_ID,
            'client_secret': config.ALPACA_CLIENT_SECRET,
            'redirect_uri': 'https://13d5-192-159-178-211.ngrok.io/auth'
        })
    return Response(access_response)
    #     auth_token = request.args.get("access_token")
    # if auth_token != "":
    #     print(auth_token)
    #     return Response(auth_token), 200


@app.route('/token', methods=['GET'])
def token():
    access_token = request.args.get("access_token")
    print(access_token + 'this is the accesstoken')
    if access_token != "":
        return Response(access_token)
    else:
        return Response("no")


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
    # if statement - confirm user has sufficient funds
    # then execute trade
    # else statement -
    # then error


@app.route('/alpaca-sell', methods=['GET', 'POST'])
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
