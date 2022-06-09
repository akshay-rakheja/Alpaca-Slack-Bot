import os
from pydoc import cli
import ssl
from numpy import dot
from slack_sdk import WebClient
from flask import Flask, request
from pathlib import Path
import config
from slack_bolt import App
import certifi

# Initializing .env path
# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

# Initializes your app with your bot token and signing secret
app = App(token=config.SLACK_TOKEN, 
          signing_secret=config.SLACK_SIGNING_SECRET,)

# Add functionality here
# @app.event("app_home_opened") etc

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",

        # body of the view
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Welcome to your _App's Home_* :tada:"
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Click me!"
                }
              }
            ]
          }
        ]
      }
    )
  
  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

# at the top where you are initializing other packages...
# (both of these should have been installed with psycopy so you shouldn't need to install anything - if you get an error about not finding the package let me know)



# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
    
    


# client_id = config.SLACK_CLIENT_ID
# client_secret = config.SLACK_CLIENT_SECRET
# # oauth_scope = os.environ["SLACK_SCOPES"]

# client = WebClient(token=os.environ["SLACK_TOKEN"])
# client.chat_postMessage(channel="#alpaca-slack-bot", text="Hello World!")


# app = Flask(__name__)
