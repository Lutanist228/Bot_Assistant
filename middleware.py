from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram import types

def flood_count(message_count: int = None):
    def decorator(func):
         
        return anext(func) 
    return decorator

class Anti_Flood(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()

        if handler > 6:
            await message.reply("Вы превысили количество сообщений.")

            
