import logging
from aiogram import Bot, Dispatcher, executor, types
from commands import process_command
from config import BOT_NAME, BOT_API_TOKEN

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('broadcast')

# Configure Bot and Dispatcher
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(bot)

 

@dp.message_handler(state='*')
async def router(message: types.Message):

    # user = ctr.get_sender(message)

    if message.is_command():
        reply = process_command(message)
        await message.answer(reply, parse_mode="html")
    else:
        await message.answer("Type /help for available commands.", parse_mode="html")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
