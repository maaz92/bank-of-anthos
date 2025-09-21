import requests
import os
import streamlit as st
import logging
import utils
from datetime import datetime
import re
import uuid

class UserServiceClient:
    def __init__(self):
        self.user_service_url = f"http://{os.getenv('USERSERVICE_API_ADDR', 'userservice:8080')}"
    
    def login(self, username: str, password: str):
        response = requests.get(
            self.user_service_url + '/login',
            params={'username': username, 'password': password}
        )
        logging.debug(response.status_code)
        if response.status_code > 300 or response.status_code < 200:
            logging.debug('Incorrect Password')
            return {'is_credentials_valid': False}
        logging.debug(response.json())
        return {'is_credentials_valid': True, 'token': response.json()["token"]}

class TransactionsServiceClient:
    def __init__(self):
        self.transactions_service_url = f"http://{os.getenv('TRANSACTIONS_API_ADDR', 'ledgerwriter:8080')}"

    def add_transaction(self, *, amount: int, from_account_number: str = None, from_routing_number: str = None, to_account_number: str = None):
        if from_account_number:
            transaction = {
                "fromAccountNum": from_account_number,
                "fromRoutingNum": from_routing_number,
                "toAccountNum": utils.get_current_account_number(),
                "toRoutingNum": os.getenv("LOCAL_ROUTING_NUM", "883745000"),
                "amount": amount,
                "timestamp": datetime.now().isoformat(),
                "uuid": str(uuid.uuid1())
            }
        else:
            transaction = {
                "fromAccountNum": utils.get_current_account_number(),
                "fromRoutingNum": os.getenv("LOCAL_ROUTING_NUM", "883745000"),
                "toAccountNum": to_account_number,
                "toRoutingNum": os.getenv("LOCAL_ROUTING_NUM", "883745000"),
                "amount": amount,
                "timestamp": datetime.now().isoformat(),
                "uuid": str(uuid.uuid1())
            }
        response = requests.post(
            self.transactions_service_url + '/transactions',
            json=transaction,
            headers=utils.get_header()
        )
        logging.debug(response.status_code)
        if response.status_code > 300 or response.status_code < 200:
            return {'request_successful': False}
        return {'request_successful': True}

class BalanceServiceClient:
    def __init__(self):
        self.balance_service_url = f"http://{os.getenv('BALANCES_API_ADDR', 'balancereader:8080')}"

    def get_balance(self):
        response = requests.get(
            self.balance_service_url + '/balances/' + utils.get_current_account_number(),
            headers=utils.get_header()
        )
        if response.status_code >= 300 or response.status_code < 200:
            return {'request_successful': False}
        else:
            return {'request_successful': True, 'balance': int(response.text)}

class HistoryServiceClient:
    def __init__(self):
        self.history_service_url = f"http://{os.getenv('HISTORY_API_ADDR', 'transactionhistory:8080')}"
    
    def get_transaction_history(self):
        response = requests.get(
            self.history_service_url + '/transactions/' + utils.get_current_account_number(),
            headers=utils.get_header()
        )
        if response.status_code >= 300 or response.status_code < 200:
            return {'request_successful': False}
        else:
            return {'request_successful': True, 'history': response.json()}

class ContactsServiceClient:
    def __init__(self):
        self.contacts_service_url = f"http://{os.getenv('CONTACTS_API_ADDR', 'contacts:8080')}"

    def get_contacts(self):
        response = requests.get(
            self.contacts_service_url + '/contacts/' + utils.get_current_username(),
            headers=utils.get_header()
        )
        if response.status_code >= 300 or response.status_code < 200:
            return {'request_successful': False}
        else:
            return {'request_successful': True, 'contacts': response.json()}
    
    def add_contact(self, account_num: str, label: str, is_external: bool, routing_num: str = None):
        if not is_external:
            routing_num = os.getenv("LOCAL_ROUTING_NUM", "883745000")
        errors = []
        if account_num is None or not re.match(r"\A[0-9]{10}\Z", account_num):
            errors.append("Account Number must be exactly 10 digits (no spaces, no letters, no extra characters)")
        if routing_num is None or not re.match(r"\A[0-9]{9}\Z", routing_num):
            errors.append("Routing number must be exactly 10 digits (no spaces, no letters, no extra characters)")
        if label is None or not re.match(r"^[0-9a-zA-Z][0-9a-zA-Z ]{0,29}$", label):
            errors.append("Label must be >0 and <=30 chars, alphanumeric and spaces, can't start with space")
        if len(errors) > 0:
            return {'request_successful': False, 'errors': errors}
        request_body = {
            "account_num": account_num,
            "routing_num": routing_num,
            "label": label,
            "is_external": is_external
        }
        response = requests.post(
            self.contacts_service_url + '/contacts/' + utils.get_current_username(),
            headers=utils.get_header(),
            json=request_body
        )
        if response.status_code >= 300 or response.status_code < 200:
            return {'request_successful': False}
        else:
            return {'request_successful': True}

user_service_client = UserServiceClient()
balance_service_client = BalanceServiceClient()
history_service_client = HistoryServiceClient()
contacts_service_client = ContactsServiceClient()
transactions_service_client = TransactionsServiceClient()