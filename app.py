import os
import slack
import sql
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort
from slackeventsapi import SlackEventAdapter
#import alpaca_trade_api as alpaca
from slack_bolt import App

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

#DB_USER, DB_PASSWORD, DB_NAME = os.environ['DBUSER'], os.environ['DBPASSWORD'], os.environ['DBNAME']

BOT_ID = client.api_call("auth.test")['user_id']

#ALPACA_API_KEY = os.environ['ALPACA_API_KEY']
#ALPACA_SECRET_KEY = os.environ['ALPACA_SECRET_KEY']
#BASE_APP_URL = os.environ['BASE_APP_URL']

paperview = False 

# Initializes your app with your bot token and signing secret

@app.route('/alpaca-connect', methods=['POST'])
def alpaca_connect():
    data = request.form 
    client.chat_postMessage(channel = data['channel_id'], text='<https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=3587772637143.3615493290961&redirect_uri=https://slack.com/oauth/v2/authorize?scope=slash-command&client_id=3587772637143.3615493290961>')
    return Response("Hello"), 200 

@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    data = request.form
    #client.chat_postMessage(channel = data['channel_id'], text = "HI")
    return Response("Welcome to Alpaca for Slack!"), 200

# Start your app
if __name__ == "__main__":
    app.run(debug=True)