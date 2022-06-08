import os
from pydoc import cli
from slack_sdk import WebClient
from flask import Flask, request
from dotenv import load_dotenv
from pathlib import Path


# Initializing .env path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
# oauth_scope = os.environ["SLACK_SCOPES"]

client = WebClient(token=os.environ["SLACK_TOKEN"])
client.chat_postMessage(channel="#alpaca-slack-bot", text="Hello World!")


app = Flask(__name__)
