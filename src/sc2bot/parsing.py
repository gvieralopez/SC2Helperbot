def extract_command(text: str, bot_username: str | None = None) -> list[str]:
    """Split "/name arg1 arg2" into [name, arg1, arg2].

    Like the old bot, "/help_fetch" means "/help fetch" (handy as a tappable link), and
    "/name@OtherBot" in a group is meant for another bot, so it gives [].
    """
    # Telegram adds "@bot" right after the command, so before the "_" arguments of a link.
    head, _, rest = text[1:].partition(" ")
    if "@" in head:
        head, addressee = head.split("@", 1)
        if bot_username is not None and addressee.lower() != bot_username.lower():
            return []
    raw_without_slash = f"{head} {rest}" if rest else head
    separator = " " if " " in raw_without_slash else "_"
    parts = [part for part in raw_without_slash.split(separator) if part]
    if not parts:
        return []
    command_name, *arguments = parts
    return [command_name.lower(), *arguments]
