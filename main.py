from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config_file import OLD_API_TOKEN
from db_actions import Database

bot = Bot(OLD_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()
MODER_CHAT_ID = '869012176'

async def on_startup(dp):
    await db.create_connection()
    await db.create_table()
    print('Бот запущен!')

async def on_startup_wrapper(dp):
    await on_startup(dp)

def on_shutdown(_):
    print('Бот выключен!')

if __name__ == '__main__':
    from message_handlers import dp
    from callback_handlers import dp
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=lambda dp: on_startup_wrapper(dp), on_shutdown=on_shutdown)