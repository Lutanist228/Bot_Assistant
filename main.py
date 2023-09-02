from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_API
from db_actions import Database
from Chat_gpt_module import start_data

bot = Bot(BOT_API)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()
MODER_CHAT_ID = '869012176'

async def on_startup(dp):
    await db.create_connection()
    await db.create_table()
    # await start_data()
    print('Бот запущен!')

async def on_startup_wrapper(dp):
    await on_startup(dp)

def on_shutdown(_):
    print('Бот выключен!')

if __name__ == '__main__':
    from handlers import dp
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=lambda dp: on_startup_wrapper(dp), on_shutdown=on_shutdown)