import data.db_access as db
import APIs.blizzard as blizzardAPI
import APIs.sc2ladder as ladderAPI
import datetime


TEMPLATE_SETTINGS = """
<b>SC2 Helper Settings</b>

💬 <b>Telegram</b>
<i>User:</i> @{0.arroba} 
<i>id:</i> <code>{0.tgid}</code>

🎮 <b>StarCraft II</b>
<i>Name:</i> <code>{0.display_name}</code>
<i>Account ID:</i> <code>{0.account_id}</code> 
<i>Battle Tag:</i> <code>{0.battle_tag}</code>
<i>Region ID:</i>
    🇺🇸 <code>{0.US_id}</code>
    🇪🇺 <code>{0.EU_id}</code>
    🇰🇷 <code>{0.KR_id}</code>
    🇹🇼 <code>{0.TW_id}</code> 

<b>Last Updated:</b> {1} 
"""

TEMPLATE_MORE_DATA = """
Dear @{0.arroba}:

You have not entered sufficient information for me to track your progress in Battle Net.

<b>Please provide one of the following:</b>

<code>Region ID:</code> /regionid 
<code>Battle Tag:</code>  /battletag 

ℹ️ If you want to know the information I store from you,
You can check /settings
"""

TEMPLATE_BLIZZARD_ID = """
In order to get Blizzard Region ID, you need to send me your <i>Blizzard Profile URL:</i>

<code>/regionid [your_blizzard_URL]</code>

<b>To get your Blizzard Id:</b>

1️ Go to https://starcraft2.com/ and log in.
2️ Clic in view profile
3️ Copy the URL of your profile
4️ Send it to me using /regionid command

<b>Example</b>:

<code>/regionid https://starcraft2.com/en-us/profile/1/1/10993388</code>
"""

TEMPLATE_BATTLE_TAG = """
A Battle tag is a combination of Display name and a code that identifies a user in Blizzard games. I looks like:

<code>MyName#12345</code>

You can check your Battle tag in the Battle Net app, near the top right corner.

To send me your Battle tag you can use something:

<code>/battletag [battletag]</code>

<b>Example</b>:

<code>/battletag MyName#12345</code>
"""


TEMPLATE_PROFILE = "Aqui va to eso {0.arroba}"


def check_btag(btag):
    if "#" in btag:
        spt = btag.split("#")
        if len(spt) == 2:
            code = spt[1]
            if code.isdigit():
                return True
    return False
    

def timedelta2string(delta):
    seconds = int(delta.total_seconds())
    if seconds == 0:
        return '⏰ now'
    minutes = int(seconds/60)
    hours = int(minutes/60)
    days = int(hours/24)
    if days > 0:
        return f'⏰ {days} days ago'
    if hours > 0:
        return f'⏰ {hours} hour sago'
    if minutes > 0:
        return f'⏰ {minutes} minutes ago'
    if seconds > 0:
        return f'⏰ {seconds} seconds ago'


def process_help(u=None, args=None):
    if args == []:
        ret = "List of available commands\n\n"
        for c in commands.keys():
            ret += f"<b>{c}</b>: {commands[c]['desc']}\n"
        return ret
    elif len(args) == 1:
        c = args[0] if args[0].startswith('/') else f'/{args[0]}'
        if c in commands.keys():
            return commands[c]['help']
    return commands['/help']['help']

def process_settings(u, args=None):
    delta = datetime.datetime.now() - u.modified_at
    delta_str = timedelta2string(delta)
    return TEMPLATE_SETTINGS.format(u, delta_str)

def process_profile(u, args=None):
    if u.battle_tag is None:
        return TEMPLATE_MORE_DATA.format(u)
    return TEMPLATE_PROFILE.format(u)

def process_battletag(u, args=None):
    if args == []:
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
    if args == []:
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

commands = {
    '/help': {
        'function': process_help,
        'desc': "Show all available commands.",
        'help': "Show all available commands. If you type ```/help command``` it shows the help of that command."
    },
    '/settings': {
        'function': process_settings,
        'desc': "Show user settings",
        'help': "Just run /settings to see your settings"
    },
    '/profile': {
        'function': process_profile,
        'desc': "Show Battle Net statistics of the user",
        'help': "Just run /profile to see your stats in Battle Net"
    },
    '/regionid': {
        'function': process_regionId,
        'desc': "Let the user enter his Blizzard ID",
        'help': TEMPLATE_BLIZZARD_ID
    },
    '/battletag': {
        'function': process_battletag,
        'desc': "Let the user enter his Blizzard Battle Tag",
        'help': TEMPLATE_BATTLE_TAG
    }
}

def _split_command(command):
    if " " in command:
        command = command.split(" ")
    elif "_" in command:
        command = command.split("_")

    if isinstance(command, list):
        args = command[1:]
        command = command[0]
        args = [i for i in args if i != '']
    else:
        args = []
    return command.lower(), args


def _process_command(command, user):
    command, args = _split_command(command)
    print(command, args)
    if command in commands.keys():
        return commands[command]['function'](user, args)
    else:
        return "404 Command not found"

def get_username(message):
    tgid = message['from']['id']
    arroba = message['from']['username'] 
    if arroba is None:
        display_name = message['from']['first_name']
        arroba = f'<a href="tg://user?id={tgid}">{display_name}</a>'
    return arroba

def process_command(message):
    """
    Identify the command inside a telegram message and if it is available then execute it.

    Args:
        message (str): The message containing the command to execute

    Returns:
        str: Result of executing the command
    """
    command = message.text
    tgid = message['from']['id']
    user = db.get_user(tgid)
    arroba = get_username(message)

    if user is None:           
        db.create_user(tgid, arroba)
        user = db.get_user(tgid)
    else:
        user.arroba = arroba 
        db.update_user(user)
    
    return _process_command(command, user)