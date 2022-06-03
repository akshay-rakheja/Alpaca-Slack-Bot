import alpaca_trade_api as alpaca
import os
import slack
import sql
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, make_response, request, Response, jsonify, abort
import alpaca_trade_api.rest as TimeFrame
from slackeventsapi import SlackEventAdapter

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

api = alpaca.REST()
account = api.get_account()

def handleAuth(userID, token):
    data = request.form()
    channel_id = data['channel_id']
    redirectURI = ""
    if token == "": 
        client.chat_postEphemeral(channel = channel_id, userID = userID, text = "Please authorize access to your Alpaca account.")
    else:
        Response("You've already authorized access to Alpaca account, but if you'd like to re-authorize, click the button.")
    
# 3 inputs are all strings
def handleHelp(userID, token, channel):
    if token == "":
        Response("Please connect your account by pressing the Authorize button")
    else:
        Response("Here are the responses")
    # finish the examples
        msgText = ""
        # msgText = fmt.Sprintf("*Here are the commands you can use to interact with the Alpaca API.* These commands will be executed with Alpaca's *%s* API.\n", apiType) +
        #     print("  - `%s account`: _Display your account information._\n", SLASH_COMMAND)
        #     fmt.Sprintf("  - `%s order`: _Submit an order._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s orders`: _Display your open orders._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s orders cancelall`: _Cancel all of your open orders._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s positions`: _Display your open positions._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s position symbol`: _Display your open position in the given symbol, if one exists._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s orders closeall`: _Close all of your open positions._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s connect`: _Refresh your authorization with Alpaca for this application._\n", SLASH_COMMAND) +
        #     fmt.Sprintf("  - `%s disconnect`: _Revoke your authorization with Alpaca for this application._\n", SLASH_COMMAND)
        client.chat_postEphemeral(text = msgText, channel = channel, userID = userID) 

def handleDisplayAccount(userID, token):
    data = request.form()
    channel_id = data=['channel_id']
    alpacaClient = alpaca.NewClient()
    account = alpacaClient.getAccount()

    # gather the values from account
    commands = {
        "an": account.Accountnumber,
        "eq": "$" + account.Equity.String(),
        "lmv": "$" + account.LongMarketValue.String(),
        "smv": "$" + account.ShortMarketValue.String(), 
        "ct": "$" + account.Equity.Sub(account.LastEquity).String(), 
        "bp": "$" + account.BuyingPower.String(), 
    }

    #display the account values
    message = "Account Number: {} | Equity: {} | Long Market Value {} | Short Market Value {} | Change Today {} | Buying Power {} ".format(
        commands["an"], commands["eq"], commands["lmv"], commands["smv"], commands["ct"], commands["bp"])

    response = client.chat_postEphemeral(text = message, userID = userID)
	

def handleListOrders(userID, token, index, messageTS, channelID):
    pass
