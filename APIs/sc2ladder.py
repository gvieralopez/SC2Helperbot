import requests
import json

_BASE_URL = "https://www.sc2ladder.com/api/player?query={battle_tag}&limit={limit}"



def get_btag_info(battle_tag):
    """Send a GET request to the sc2ladder API and try to get info with battle tag.

    Args:
        url (str): -_-

    Returns:
        json: full json response
    """
    url=_BASE_URL.format(battle_tag=battle_tag, limit=1)
    r = requests.get(url)
    if r.status_code == 200:
        response = json.loads(r.content)
        return response
    return r.status_code