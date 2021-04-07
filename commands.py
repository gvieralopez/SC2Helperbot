import data.db_access as db


TEMPLATE_SETTINGS = """
Starcraft II Profile
Telegram User: @{0.arroba} 
Telegram id: {0.tgid}
Account ID: {0.account_id} 
Blizzard ID: {0.profile_id} 
SC II Name: {0.display_name} 
Battle Tag: {0.battle_tag} 
Last Updated: {0.modified_at}
"""

TEMPLATE_MORE_DATA = """
Dear @{0.arroba}:

You have not entered sufficient information for me to track your progress in Battle Net.

Please provide one of the following:

Blizzard ID: /blizzardId 
Battle Tag: /battletag 

If you want to know the information I store from you, check /settings
"""


"""
Profile ID: /profile {ProfileId}
Battle Tag: /battletag {BattleTag}
"""

TEMPLATE_PROFILE = "Aqui va to eso {0.arroba}"

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
    return TEMPLATE_SETTINGS.format(u)

def process_profile(u, args=None):
    if u.battle_tag is None:
        return TEMPLATE_MORE_DATA
    return TEMPLATE_PROFILE.format(u)

commands = {
    '/help': {
        'function': process_help,
        'desc': "Description of /help",
        'help': "Help for /help command"
    },
    '/settings': {
        'function': process_settings,
        'desc': "Description of /settings",
        'help': "Help for /settings command"
    },
    '/profile': {
        'function': process_profile,
        'desc': "Description of /profile",
        'help': "Help for /profile command"
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
    else:
        args = []
    return command, args


def _process_command(command, user):
    command, args = _split_command(command)
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