from aiogram.utils import exceptions
from aiogram import types
import asyncio

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


def remove_teams_ladders(ladder_summary):
    single_player_ladders = []
    for ladder in ladder_summary['allLadderMemberships']:
        if ladder["localizedGameMode"].startswith('1v1'):
            single_player_ladders.append(ladder)    
    return single_player_ladders

async def send_message(user_id: int, text: str, log, bot, disable_notification: bool = False, keyboard=None, pin_it=False) -> bool:
    """
    Safe messages sender

    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        msg = await bot.send_message(user_id, text, disable_notification=disable_notification, parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
        if pin_it:
            await bot.pin_chat_message(user_id, msg['message_id'])

    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text, log, bot)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        return True
    return False