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

