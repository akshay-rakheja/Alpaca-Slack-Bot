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

@app.route('/alpaca-connect', methods=['GET', 'POST'])
def alpaca_connect():
    return Response("Go to this link to connect your Alpaca account: https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=0c76f3a44caa688859359cab598c9969&redirect_uri=https://3698-50-208-212-121.ngrok.io/alpaca-connect&scope=account:write%20trading%20data"), 200 

@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    #client.chat_postMessage(channel = data['channel_id'], text = "HI")
    return Response("Welcome to Alpaca for Slack!"), 200

# Start your app
if __name__ == "__main__":
    app.run(debug=True)