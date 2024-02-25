import os
from typing import Any, Dict, List, Text

import plaid
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

load_dotenv()


class ActionCheckBalance(Action):
    def name(self) -> Text:
        return "action_check_balance"

    def exchange_public_token(self, public_token: str) -> str:
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                "clientId": os.getenv("PLAID_CLIENT_ID"),
                "secret": os.getenv("PLAID_SECRET"),
            },
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(exchange_request)
        return response["access_token"]

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Assume you retrieve the public_token from a slot or some other means
        public_token = tracker.get_slot("public_token")

        # Check if the public_token is available
        if not public_token:
            dispatcher.utter_message(text="Public token not available.")
            return []

        # Exchange public token for access token
        try:
            access_token = self.exchange_public_token(public_token)
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

        return []
