import datetime
import data.db_access as db
import APIs.blizzard as blizzardAPI
import APIs.sc2ladder as ladderAPI
from commands.utils import check_btag, timedelta2string
from commands.templates import *

def process_help(u=None, args=None):
    from commands import commands_dict, command_cats  

    def general_help():
        cats = {k:[] for k in command_cats.keys()}
        for c in commands_dict.keys():
            cat = commands_dict[c]['cat']
            desc = commands_dict[c]['desc']
            cats[cat].append((c, desc))
        ret = "<b>List of available commands</b>\n\n"
        for cat in cats.keys():
            ret += f'<i>{command_cats[cat]}</i>\n'
            for c, desc in cats[cat]:
                ret += f"<b>{c}</b> {desc}\n"
            ret += '\n'
        return ret

    def particular_help():
        c = args[0] if args[0].startswith('/') else f'/{args[0]}'
        if c in commands_dict.keys():
            return commands_dict[c]['help']

    if not len(args):
        return general_help()
    elif len(args) == 1:
        return particular_help()
    return commands_dict['/help']['help']

def process_settings(u, args=None):
    delta = datetime.datetime.now() - u.modified_at
    delta_str = timedelta2string(delta)
    return TEMPLATE_SETTINGS.format(u, delta_str)

def process_profile(u, args=None):
    if u.battle_tag is None:
        return TEMPLATE_MORE_DATA.format(u)
    
    response = ladderAPI.get_btag_info(u.battle_tag)
    return response

def process_battletag(u, args=None):
    if not len(args):
        return process_help(u, args =["battletag"])
    btag = args[0] if check_btag(args[0]) else False
    if not btag:
        return "Invalid Battle tag, check /battletag for help."
    if u.battle_tag != btag:
        u.battle_tag = btag
        db.update_user(u,True)
    
    response = ladderAPI.get_btag_info(btag)
    if not len(response):
        return "Could not fetch enough data with this Battle tag, you also need to provide /regionid "
    for dic in response:
        if dic['realm'] == '1':
            u = update_region_id(u, dic['region'], dic['profile_id'])
            db.update_user(u, modified=True)
    return process_settings(u)


def update_region_id(user, rcode, profile_id):
    if rcode == 1 or rcode == 'US':
        user.US_id = profile_id
    elif rcode == 2 or rcode == 'EU':
        user.EU_id = profile_id
    elif rcode == 3 or rcode == 'KR':
        user.KR_id = profile_id
    elif rcode == 4 or rcode == 'TW':
        user.TW_id = profile_id
    else:
        raise ValueError(f"Invalid region id for user {u.arroba}") 
    return user

def process_auth(u, args=None):
    if not len(args):
        return process_help(u, args =["auth"])

def process_regionId(u, args=None):
    if not len(args):
        return process_help(u, args =["regionid"])

    if args[0].startswith('https://starcraft2.com/'):
        profile_id = args[0].split('/')[-1]
        region_code = args[0].split('/')[-3]
    

    bid = int(profile_id) if profile_id.isdigit() else None
    rcode = int(region_code) if region_code.isdigit() else None
 
    if bid is not None:
        data = blizzardAPI.get_player_info(bid, rcode)
        if not isinstance(data, int):
            u = update_region_id(u, rcode, bid)
            u.display_name = data['summary']['displayName']
            db.update_user(u)
            return process_settings(u)
        return f"Blizzard API call Failed with error code: {data}"
    return "Invalid Starcraft2.com profile URL, check /regionid for help."