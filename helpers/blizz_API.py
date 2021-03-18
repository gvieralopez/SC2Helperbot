import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

CLIENT = os.getenv("BZ_OAUTH_CLIENT")
TOKEN = os.getenv("BZ_OAUTH_TOKEN")


def get_access_token():
    url = "https://us.battle.net/oauth/token"
    data = {"grant_type": "client_credentials"}
    r = call_api(url, data)
    if r.status_code == 200:
        response = json.loads(r.content)
        return response["access_token"]
    return False


def call_api(url, data):
    return requests.post(url, auth=(CLIENT, TOKEN), data=data)
