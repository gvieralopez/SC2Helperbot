import data.db_access as db


def process_help():
    return "List of available commands"

def process_me(u):
    template = "Starcraft II Profile\n"
    template += "Telegram User: @{}\n".format(u.arroba)
    template += "Telegram id: @{}\n".format(u.tgid)
    template += "Account ID: {}\n".format(u.account_id)
    template += "Profile ID: {}\n".format(u.profile_id)
    template += "SC II Name: {}\n".format(u.display_name)
    template += "Battle Tag: {}\n".format(u.battle_tag)
    template += "Last Updated: {}".format(u.modified_at)
    return template

def _process_command(command, user):
    if command == "/help":
        return process_help()
    if command == "/me":
        return process_me(user)
    return command

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

    if not user:
        arroba = message['from']['username']     
        db.create_user(tgid, arroba)
    
    return _process_command(command, user)