from aiogram import Dispatcher, Bot, executor
from config_file import OLD_API_TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage

my_storage = MemoryStorage()
my_bot = Bot(OLD_API_TOKEN)
dp = Dispatcher(bot=my_bot, storage=my_storage)

if __name__ == "__main__":
    from message_handlers import dp, on_startup
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True) # запуск бота
