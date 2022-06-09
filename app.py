import os
import slack
import slack_sdk
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, abort
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

client = slack_sdk.WebClient(token=os.environ['SLACK_TOKEN'])

#DB_USER, DB_PASSWORD, DB_NAME = os.environ['DBUSER'], os.environ['DBPASSWORD'], os.environ['DBNAME']

BOT_ID = client.api_call("auth.test")['user_id']

#ALPACA_API_KEY = os.environ['ALPACA_API_KEY']
#ALPACA_SECRET_KEY = os.environ['ALPACA_SECRET_KEY']
#BASE_APP_URL = os.environ['BASE_APP_URL']

# Initializes your app with your bot token and signing secret

@app.route('/alpaca', methods=['GET', 'POST'])
def alpaca():
    data = request.form
    if data['text'] == 'connect':
        return Response("Go to this link to connect your Alpaca account: https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=0c76f3a44caa688859359cab598c9969&redirect_uri=https://a6a6-152-44-181-213.ngrok.io/alpaca&scope=account:write%20trading%20data"), 200 
    elif data['text'] == 'lol':
        return Response("ok"), 200
    else:
        return Response(""), 200
# Start your app
if __name__ == "__main__":
    app.run(debug=True)