import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

_CLIENT = os.getenv("BZ_OAUTH_CLIENT")
_TOKEN = os.getenv("BZ_OAUTH_SECRET")
_region_Name = os.getenv("BZ_REGION")
_REGION = {"id" : 2 if _region_Name == "eu" else 1 if _region_Name == 'us' else 3 if _region_Name == 'kr' else 4, 'name' : _region_Name}
_BASE_BNET_URL = "https://{region}.battle.net".format(region=_REGION['name'])
_BASE_API_URL = "https://{region}.api.blizzard.com".format(region=_REGION['name'])


def get_access_token():
    """Gets OAuth access TOKEN

    Returns:
        [str]: access token (expires in 24hrs)
    """
    url = _BASE_BNET_URL +  "/oauth/token"
    data = {"grant_type": "client_credentials"}
    r = post_api(url, data)
    if r.status_code == 200:
        response = json.loads(r.content)
        return response["access_token"]
    return False


def get_player_meta(regionId, realmId=1, profileId):
    """Returns metadata for an individual's profile.

    Args:
        profileId (int): SC2 profile ID (get it in starcraft2.com)

    Returns:
        [json]: player meta info
    """
    url = _BASE_API_URL + "/sc2/metadata/profile/{regionId}/{realmId}/{profileId}".format(regionId=regionId, realmId=realmId, profileId=profileId)
    r = get_api(url)
    if r.status_code == 200:
        response = json.loads(r.content)
        return response
    return r.status_code

def get_player_info(regionId=_REGION['id'], realmId=1, profileId):
    """Returns data about an individual SC2 profile.

    Args:
        profileId (int): SC2 profile ID (get it in starcraft2.com)

    Returns:
        json: player extended info
    """
    url = _BASE_API_URL + "/sc2/profile/{regionId}/{realmId}/{profileId}".format(regionId=regionId, realmId=realmId, profileId=profileId)
    return get_api(url)

def get_ladder_summary(regionId=_REGION['id'], realmId=1, profileId):
    """Returns a ladder summary for an individual SC2 profile.

    Args:
        profileId (int): SC2 profile ID (get it in starcraft2.com)

    Returns:
        [json]: player's ladders summary
    """
    url = _BASE_API_URL + "/sc2/profile/{regionId}/{realmId}/{profileId}/ladder/summary".format(regionId=regionId, realmId=realmId, profileId=profileId)
    return get_api(url)

def get_ladder_info(regionId=_REGION['id'], realmId=1, profileId, ladderid):
    """Returns data about an individual profile's ladder.

    Args:
        profileId (int): SC2 profile ID (get it in starcraft2.com)
        ladderid (int): Ladder unique ID (get it in the player' ladder summary)

    Returns:
        [json]: Specific ladder info
    """
    url = _BASE_API_URL + "/sc2/profile/{regionId}/{realmId}/{profileId}/ladder/{ladderId}".format(regionId=regionId, realmId=realmId, profileId=profileId, ladderId=ladderid)
    return get_api(url)


def post_api(url, data):
    """Send POST request to the API

    Args:
        url (str): duh!
        data (params): *args

    Returns:
        requests: full response
    """
    return requests.post(url, auth=(_CLIENT, _TOKEN), data=data)

def get_api(url):
    """Send a GET request to the API, after asking for a new oauth token.

    Args:
        url (str): -_-

    Returns:
        json: full json response
    """
    payload = {"locale" : "en_US", "access_token": get_access_token()}
    r = requests.get(url, params=payload)
    if r.status_code == 200:
        response = json.loads(r.content)
        return response
    return r.status_code
