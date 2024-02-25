import os
from typing import Any, Dict, List, Text

import plaid
import requests
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

load_dotenv()


class ActionCheckBalance(Action):
    def name(self) -> Text:
        return "action_check_balance"

    def exchange_public_token(self, public_token: str) -> str:
        url = "https://sandbox.plaid.com/item/public_token/exchange"
        headers = {"Content-Type": "application/json"}
        payload = {
            "client_id": os.getenv("PLAID_CLIENT_ID"),
            "secret": os.getenv("PLAID_SECRET"),
            "public_token": public_token,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            # Handle errors or invalid responses
            print(f"Failed to exchange public token: {response.text}")
            raise Exception("Failed to exchange public token.")

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Here, you'd obtain the public_token through a secure method
        # For demonstration, assuming the public_token is passed via a custom payload or a secure mechanism
        public_token = tracker.get_slot("public_token")

        if not public_token:
            dispatcher.utter_message(text="Public token not available.")
            return []

        try:
            access_token = self.exchange_public_token(public_token)
            # Assuming you want to store the access_token for future use, you could set it as a slot
            # Note: Ensure you handle and store access tokens securely
        except plaid.ApiException as e:
            dispatcher.utter_message(text="Failed to exchange public token.")
            print(e)
            return []

        # Create a Plaid client with the access token
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                "clientId": os.getenv("PLAID_CLIENT_ID"),
                "secret": os.getenv("PLAID_SECRET"),
            },
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        # Prepare the request object with the exchanged access token
        request = AccountsBalanceGetRequest(access_token=access_token)

        # Get the balance using the request object
        try:
            response = client.accounts_balance_get(request)
            balance = response["accounts"][0]["balances"]["available"]
            dispatcher.utter_message(text=f"Your balance is {balance}")
        except Exception as e:
            dispatcher.utter_message(text="Failed to retrieve balance.")
            print(e)

        return [SlotSet("access_token", access_token)] if access_token else []
