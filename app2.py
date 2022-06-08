import os
from slack_sdk import WebClient
from flask import Flask, request
from dotenv import load_dotenv

# Initializing .env path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_SCOPES"]

app = Flask(__name__)
