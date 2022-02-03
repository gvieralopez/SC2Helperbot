import data.db_access as db
from commands.cmds import *

commands_dict = {
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
    },
    '/auth': {
        'function': process_auth,
        'desc': "Let the user authorize the bot to use Blizzard API",
        'help': "This is not implemented yet"
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


def execute_command(command, user):
    command, args = _split_command(command)
    print(command, args)
    if command in commands_dict.keys():
        return commands_dict[command]['function'](user, args)
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
    
    return execute_command(command, user)