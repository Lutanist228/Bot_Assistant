from main import dp, bot, db
from aiogram import types
from keyboards import user_keyboard, moder_start_keyboard, moder_owner_start_keyboard, glavnoe_menu_keyboard
from additional_functions import file_reader, fuzzy_handler
from keyboards import Boltun_Step_Back, Boltun_Keys
from user_message_handlers import Global_Data_Storage, cache
from keyboards import glavnoe_menu_keyboard, Boltun_Step_Back, check_programm_keyboard
from states import User_Panel

import json
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

@dp.callback_query_handler(Text('glavnoe_menu'), state='*')
async def process_glavnoe_menu(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возврата в главное меню для всех
    user_id = callback.from_user.id
    moder_ids = await db.get_moder()
    await state.finish()
    for id in moder_ids:
        if user_id == id[0]:
            if id[1] == 'Owner':
                await callback.message.edit_text('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
            else:
                await callback.message.edit_text('Можем приступить к работе', reply_markup=moder_start_keyboard)
            return
    await callback.message.edit_text('Выберите дальнейшее действие', reply_markup=user_keyboard)

@dp.callback_query_handler(Boltun_Keys.cd.filter(), state = "*") 
async def boltun_keyboard(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data["action"]:
        global BOLTUN_PATTERN
        BOLTUN_PATTERN = file_reader("boltun.txt")
        cb_data = callback_data["action"].split("_") ; cb_data = int(cb_data[len(cb_data) - 1])
        data = callback.message.reply_markup.inline_keyboard
        key = f'{callback_data["@"]}:{callback_data["action"]}'

        menu_data = await cache.get(Global_Data_Storage.menu_temp_inf)
        if menu_data:
            keyboard_data = json.loads(menu_data)

        try:
            message_id = await db.add_question(data_base_type="fuzzy_db", 
                                    question=keyboard_data[cb_data], 
                                    user_id=callback.from_user.id,
                                    user_name=callback.from_user.full_name,
                                    message_id=callback.id,
                                    chat_type=callback.chat_instance)
            reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=keyboard_data[cb_data])
            await bot.send_message(chat_id=callback.from_user.id, 
                                    text=f"Ответ:\n{reply_text}", 
                                    reply_markup=Boltun_Step_Back.kb_choosing_questions)
            await db.update_fuzzy_data(
                primary_key_value=message_id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=similarity_rate
                )
            await Answer.boltun_reply.set()
        except UnboundLocalError:
            await callback.answer(text="Ошибка. Просим перезапустить бота...")

@dp.callback_query_handler(state=User_Panel.check_programm)
async def program_checking(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'check_fio':
        await callback.message.edit_text('Введите свое ФИО строго через пробел и ожидайте ответа', 
                                         reply_markup=glavnoe_menu_keyboard)
        await User_Panel.check_fio.set()
    elif callback.data == 'check_snils':
        await callback.message.edit_text('Введите свой СНИЛС строго в формате 000-000-000 00',
                                         reply_markup=glavnoe_menu_keyboard)
        await User_Panel.check_snils.set()

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'make_question':
        # Обработка нажатия пользователя, чтобы задать вопрос и переход в это состояние
        await callback.message.edit_text('Задайте свой вопрос. Главное меню отменит ваше действие', reply_markup=glavnoe_menu_keyboard)
        await User_Panel.boltun_question.set()
    elif callback.data == 'check_programm':
        await User_Panel.check_programm.set()
        await callback.message.edit_text('Выберите поиск по ФИО или СНИЛС, чтобы проверить вашу программу на зачисление', 
                                         reply_markup=check_programm_keyboard)






