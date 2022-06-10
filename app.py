import os
import slack
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort
from slackeventsapi import SlackEventAdapter
import alpaca_trade_api as alpaca

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

#DB_USER, DB_PASSWORD, DB_NAME = os.environ['DBUSER'], os.environ['DBPASSWORD'], os.environ['DBNAME']

BOT_ID = client.api_call("auth.test")['user_id']

#ALPACA_API_KEY = os.environ['ALPACA_API_KEY']
#ALPACA_SECRET_KEY = os.environ['ALPACA_SECRET_KEY']
#BASE_APP_URL = os.environ['BASE_APP_URL']

# Initializes your app with your bot token and signing secret


@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    data = request.form
    team_id = data['team_id']
    channel_id = data['channel_id']
    text = data['text'] 
    print(team_id, channel_id)
    if data['text'] == "connect":
        return Response(f"Go to this link to connect your Alpaca account: https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=0c76f3a44caa688859359cab598c9969&redirect_uri=https://app.slack.com/client/{team_id}/{channel_id}&scope=account:write%20trading%20data"), 200 
    
    #team id then channel id
    # else:
    #     return Response("Hello"), 200

# def handleDisplayAccount(userID, token):
#     data = request.form()
#     channel_id = data['channel_id']
#     alpacaClient = alpaca.NewClient()
#     account = alpacaClient.getAccount()

#     # gather the values from account
#     commands = {
#         "an": account.Accountnumber,
#         "eq": "$" + account.Equity.String(),
#         "lmv": "$" + account.LongMarketValue.String(),
#         "smv": "$" + account.ShortMarketValue.String(), 
#         "ct": "$" + account.Equity.Sub(account.LastEquity).String(), 
#         "bp": "$" + account.BuyingPower.String() 
#     }

#     #display the account values
#     message = "Account Number: {} | Equity: {} | Long Market Value {} | Short Market Value {} | Change Today {} | Buying Power {} ".format(
#         commands["an"], commands["eq"], commands["lmv"], commands["smv"], commands["ct"], commands["bp"])

#     return client.chat_postEphemeral(text = message, userID = userID)

# Start your app
if __name__ == "__main__":
    app.run(debug=True)