import data.db_access as db


TEMPLATE_SETTINGS = """
Starcraft II Profile
Telegram User: @{0.arroba} 
Telegram id: {0.tgid}
Account ID: {0.account_id} 
Profile ID: {0.profile_id} 
SC II Name: {0.display_name} 
Battle Tag: {0.battle_tag} 
Last Updated: {0.modified_at}
"""


def process_help(u=None, args=None):
    ret = "List of available commands\n\n"
    for c in commands.keys():
        ret += f"<b>{c}</b>: {commands[c]['desc']}\n"
    return ret

def process_settings(u, args=None):
    return TEMPLATE_SETTINGS.format(u)


commands = {
    '/help': {
        'function': process_help,
        'desc': "Description of /help"
    },
    '/settings': {
        'function': process_settings,
        'desc': "Description of /settings"
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

    if user is None:
        arroba = message['from']['username']     
        db.create_user(tgid, arroba)
        user = db.get_user(tgid)
    
    return _process_command(command, user)