import os
import logging
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(message)s')

AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]

DESTINATION_AUTH_URL = os.environ["DESTINATION_AUTH_URL"]
DESTINATION_BASE_URL = os.environ["DESTINATION_BASE_URL"]
DESTINATION_CLIENT_ID = os.environ["DESTINATION_CLIENT_ID"]
DESTINATION_CLIENT_SECRET = os.environ["DESTINATION_CLIENT_SECRET"]


def update_deployment_destination(destination_name, deployment_id):
    """create or update a subaccount level destination for a deployment id"""
    
    logging.info(f"CREATE DESTINATION {destination_name}")
        
    auth_response = requests.post(f"{DESTINATION_AUTH_URL}/oauth/token?grant_type=client_credentials", auth=HTTPBasicAuth(DESTINATION_CLIENT_ID, DESTINATION_CLIENT_SECRET))

    # Check if the request was successful
    if auth_response.status_code != 200:
        logging.info(auth_response, auth_response.content)
        raise Exception("DESTINATION LOGIN ERROR")

        
    destination_body = {
        'Description': 'desc',
        'Type': 'HTTP',
        'clientId': AICORE_CLIENT_ID,
        'Authentication': 'OAuth2ClientCredentials',
        'Name': destination_name,
        'tokenServiceURL': f"{AICORE_AUTH_URL}/oauth/token",
        'ProxyType': 'Internet',
        'URL': f"{AICORE_BASE_URL}/inference/deployments/{deployment_id}",
        'tokenServiceURLType': 'Dedicated',
        'clientSecret': AICORE_CLIENT_SECRET
    }

    headers = {"Authorization": "Bearer " + auth_response.json()["access_token"], "Content-Type": "application/json", "Accept": "application/json" }

    create_response = requests.post(f"{DESTINATION_BASE_URL}/destination-configuration/v1/subaccountDestinations", json=destination_body, headers=headers)
    
    if create_response.status_code == 409:  # means destination with name exists
        update_response = requests.put(f"{DESTINATION_BASE_URL}/destination-configuration/v1/subaccountDestinations", json=destination_body, headers=headers)

    if create_response.status_code == 201 or update_response.status_code == 200:
        logging.info(f"DESTINATION {destination_name} SUCCESSFULLY CREATED/UPDATED")