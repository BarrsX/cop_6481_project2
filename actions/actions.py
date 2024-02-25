# actions.py
import os
from dotenv import load_dotenv
from plaid import Client
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import List, Text
from typing import Dict, Any

load_dotenv()


class ActionCheckBalance(Action):
    def name(self) -> Text:
        return "action_check_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Create a Plaid client
        client = Client(
            client_id=os.getenv("PLAID_CLIENT_ID"),
            secret=os.getenv("PLAID_SECRET"),
            environment="sandbox",
        )

        # Get the access token for the user's bank account
        # You'll need to replace "user-access-token" with the actual access token
        access_token = "user-access-token"

        # Get the balance
        response = client.Accounts.balance.get(access_token)
        balance = response["accounts"][0]["balances"]["available"]

        # Send the balance to the user
        dispatcher.utter_message(text=f"Your balance is {balance}")
