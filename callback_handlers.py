from main import dp, my_bot
from aiogram import types
from inline_key import Boltun_Keys
from additional_functions import fuzzy_handler
from config_file import BOLTUN_PATTERN
from sql import sql_update_data, sql_add_extract_data
from buttons import Step_Back
from message_handlers import Question_Processing, Menu_Storage, cache

from aiogram.dispatcher import FSMContext
import json

@dp.callback_query_handler(Boltun_Keys.cd.filter(), state = "*") 
async def boltun_keyboard(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data["action"]:
        cb_data = callback_data["action"].split("_") ; cb_data = int(cb_data[len(cb_data) - 1])
        data = callback.message.reply_markup.inline_keyboard
        key = f'{callback_data["@"]}:{callback_data["action"]}'

        menu_data = await cache.get(Menu_Storage.temp_inf)
        if menu_data:
            keyboard_data = json.loads(menu_data)

        await sql_add_extract_data(data_base_type="fuzzy_db", message_text=keyboard_data[cb_data], user_id=callback.from_user.id)
        reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=keyboard_data[cb_data])

    await my_bot.send_message(chat_id=callback.from_user.id, 
                              text=f"Ответ:\n{reply_text}", 
                              reply_markup=Step_Back.kb)
    await sql_update_data(
                data_base_type="fuzzy_db",
                primary_key_value=callback.from_user.id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=100
                )
