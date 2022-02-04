import datetime
import data.db_access as db
import APIs.blizzard as blizzardAPI
import APIs.sc2ladder as ladderAPI
from commands.utils import check_btag, timedelta2string, remove_teams_ladders
from commands.templates import *
from consts import race_emojis, league_emojis, region_emojis

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



def fetch_region_ladders(pid, rid):
    ladders = []
    if pid is not None:
        region_ladders = blizzardAPI.get_ladder_summary(pid, regionId=rid)
        sp_region_ladders = remove_teams_ladders(region_ladders)
        for ladder in sp_region_ladders:
            ladder['regionId'] = rid
            ladder['profileId'] = pid
            ladders.append(ladder)
    return ladders


def process_fetch(u, args=None):
    if u.battle_tag is None:
        return TEMPLATE_MORE_DATA.format(u)
    
    ladders = []
    profile_ids = [u.US_id, u.EU_id, u.KR_id, u.TW_id]

    for i, pid in enumerate(profile_ids):
        ladders += fetch_region_ladders(pid, i+1)

    if len(ladders):
        for l in ladders:
            race = None            
            l_info = blizzardAPI.get_ladder_info(l['profileId'], l['ladderId'], l['regionId'])
            for team in l_info['ladderTeams']:
                for member in team['teamMembers']:
                    if int(member['id']) == l['profileId']:
                        if 'clanTag' in member.keys():
                            clan = member['clanTag'] 
                        else:
                            clan = ''
                        race = member['favoriteRace']
                        wins = team['wins']
                        losses = team['losses']
                        break
            region = l['regionId']
            if race:            
                ldb = db.get_user_ladder(u, region, race)
                ldb.ladder_id = int(l['ladderId'])
                ldb.wins =  wins
                ldb.losses =  losses
                ldb.clan = clan
                ldb.mmr = l_info['ranksAndPools'][0]['mmr']
                ldb.league = l_info['league']
                db.update_user_ladder(ldb)
            else:
                print(f"Something wrong with ladder {[l['ladderId']]}")
                
        return "Your game data was updated"

    return TEMPLATE_MORE_DATA.format(u)

def process_profile(u, args=None):
    if u.battle_tag is None:
        return TEMPLATE_MORE_DATA.format(u)
    
    ladders = db.get_all_ladders(u)
    if ladders is None:
        return TEMPLATE_MORE_DATA.format(u)

    ladders.sort(key=lambda x: x.mmr, reverse=True)
    ret = '<b>User ladders found (1v1)</b>\n\n'
    for l in ladders:
        win_rate = int(100 * l.wins/(l.wins+l.losses))
        clan = '' if l.clan == '' else f'&lt;{l.clan}&gt;'
        ret += f'{region_emojis[l.region]}{league_emojis[l.league]}{race_emojis[l.race]} <code>{l.mmr}</code> <i>{win_rate}%</i> {clan}<b>{u.display_name}</b>\n'
    return ret

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


def process_users(u, args=None):
    all_users = db.get_all_users()
    ret = '<b>List of bot users:</b>\n\n'
    for us in all_users:
        ret += f'{us.arroba} <code>{us.battle_tag}</code>\n'
    return ret

def process_rank(u, args=None):
    ladders = db.get_all_ladders()
    if ladders is None:
        return TEMPLATE_MORE_DATA.format(u)

    ladders.sort(key=lambda x: x.mmr, reverse=True)
    ret = '<b>🤖Bot Ranking</b>\n\n'
    for i, l in enumerate(ladders):
        win_rate = int(100 * l.wins/(l.wins+l.losses))
        clan = '' if l.clan == '' else f'&lt;{l.clan}&gt;'
        ret += f'<code>#{i+1}</code>{region_emojis[l.region]}{league_emojis[l.league]}{race_emojis[l.race]} <code>{l.mmr}</code> <i>{win_rate}%</i> {clan}<b>{u.display_name}</b>\n'
    return ret

async def fetch_all(bot):
    users = db.get_all_users()
    for u in users:
        process_fetch(u) # TODO: Log here
    print('Auto updating data')
    # TODO: Output updated ranking