import os
from pydoc import cli
import ssl
from numpy import dot
from slack_sdk import WebClient
from flask import Flask, request, Response, jsonify, abort
from pathlib import Path
import config
import certifi
from slackeventsapi import SlackEventAdapter

# Configure flask app
app = Flask(__name__)
slackeventadapter = SlackEventAdapter(
    config.SLACK_SIGNING_SECRET, "/slack/events", app)

client = WebClient(token=config.SLACK_TOKEN)
# client.chat_postMessage(channel='#alpaca-slack-bot', text="TEST")


@app.route('/')
def index():
    return 'Hello, World!'


@app.route('/alpaca2', methods=['POST', 'GET'])
def alpaca():
    print("Hello world")
    return Response("Welcome to Alpaca for Slack!"), 200


# Start your app
if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=8080)
