def extract_command(text: str, bot_username: str | None = None) -> list[str]:
    """Split "/name arg1 arg2" into [name, arg1, arg2].

    Like the old bot, "/help_fetch" means "/help fetch" (handy as a tappable link), and
    "/name@OtherBot" in a group is meant for another bot, so it gives [].
    """
    raw_without_slash = text[1:]
    separator = " " if " " in raw_without_slash else "_"
    parts = [part for part in raw_without_slash.split(separator) if part]
    if not parts:
        return []
    command_name, *arguments = parts
    if "@" in command_name:
        command_name, addressee = command_name.split("@", 1)
        if bot_username is not None and addressee.lower() != bot_username.lower():
            return []
    return [command_name.lower(), *arguments]
