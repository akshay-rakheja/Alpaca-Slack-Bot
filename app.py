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
NGROK = "https://53b3-50-208-212-121.ngrok.io"
BASE_ALPACA_URL = 'https://paper-api.alpaca.markets/v2/orders'
# BASE_ALPACA_URL = 'https://api.alpaca.markets'
# HEADERS = {'APCA-API-KEY-ID': os.environ['ALPACA_API_KEY'],
#            'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET_KEY']}

conn = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME,
                        user=config.DB_USER, password=config.DB_PASSWORD)

cur = conn.cursor()       
# Initializes your app with your bot token and signing secret


@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    data = request.form
    team_id = data['team_id']
    channel_id = data['channel_id']
    text = data['text'] 
    user_id = data['user_id']
    print(team_id, channel_id)
    if text == "connect":
        #client.chat_postEphemeral("https://api.alpaca.markets/oauth/grant_type=authorization_code&code=67f74f5a-a2cc-4ebd-88b4-22453fe07994&client_id=fc9c55efa3924f369d6c1148e668bbe8&client_secret=5b8027074d8ab434882c0806833e76508861c366&redirect_uri=https://example.com/oauth/callback")
        return Response("https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=0c76f3a44caa688859359cab598c9969" + 
        "&redirect_uri=" + NGROK + "/auth&scope=account:write%20trading%20data&state=" + user_id), 200
    # elif text == "display":
    #     return Response(handleDisplayAccount(user_id, 0)), 200
    elif text == "":
        return Response("HI"), 200

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    conn = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME,
                        user=config.DB_USER, password=config.DB_PASSWORD)
    cur = conn.cursor()       
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
    # if statement - confirm user has sufficient funds
    # then execute trade
    # else statement - 
    # then error 

     try:
        order = requests.post(
            '{0}/v2/orders'.format(BASE_ALPACA_URL), headers=HEADERS, json={
                'symbol': symbol,
                'qty': qty,
                'side': "buy",
                'type': "market",
                'time_in_force': "gtc",
            })
        print('Alpaca order reply status code: {0}'.format(
            order.status_code))
        if order.status_code != 200:
            print("Undesirable response from Alpaca! {}".format(order.json()))
            return False
    except Exception as e:
        logger.exception(
            "There was an issue posting order to Alpaca: {0}".format(e))
        return False
    return order.json()

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

    #display the account values
    message = "Account Number: {} | Equity: {} | Long Market Value {} | Short Market Value {} | Change Today {} | Buying Power {} ".format(
        commands["an"], commands["eq"], commands["lmv"], commands["smv"], commands["ct"], commands["bp"])

    return message

# Start your app
if __name__ == "__main__":
    app.run(debug=True)