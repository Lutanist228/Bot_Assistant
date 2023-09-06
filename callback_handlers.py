from main import dp, bot
from aiogram import types
from keyboards import Boltun_Step_Back, Boltun_Keys
from additional_functions import fuzzy_handler
from config_file import BOLTUN_PATTERN
from db_actions import Database
from additional_functions import create_inline_keyboard
from message_handlers import Answer, db, Boltun_Question_Processing, Global_Data_Storage, cache
from keyboards import user_keyboard, moder_start_keyboard, moder_choose_question_keyboard

from aiogram.dispatcher import FSMContext
import json
from aiogram.dispatcher.filters import Text

@dp.callback_query_handler(Boltun_Keys.cd.filter(), state = "*") 
async def boltun_keyboard(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data["action"]:
        cb_data = callback_data["action"].split("_") ; cb_data = int(cb_data[len(cb_data) - 1])
        data = callback.message.reply_markup.inline_keyboard
        key = f'{callback_data["@"]}:{callback_data["action"]}'

        menu_data = await cache.get(Global_Data_Storage.menu_temp_inf)
        if menu_data:
            keyboard_data = json.loads(menu_data)

        message_id = await db.add_question(data_base_type="fuzzy_db", 
                                    question=keyboard_data[cb_data], 
                                    user_id=callback.from_user.id,
                                    user_name=callback.from_user.full_name)
        
        reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=keyboard_data[cb_data])
    await bot.send_message(chat_id=callback.from_user.id, 
                              text=f"Ответ:\n{reply_text}", 
                              reply_markup=Boltun_Step_Back.kb)
    await db.update_fuzzy_data(
        primary_key_value=message_id,
        bot_reply=reply_text,
        reply_status='TRUE',
        similarity_rate=similarity_rate
        )
    
@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'instruction':
        await callback.message.answer('Инструкция')
    elif callback.data == 'make_question':
        await callback.message.edit_text('Задайте свой вопрос')
        await Boltun_Question_Processing.boltun_question.set()
    elif callback.data == 'number_unanswered':
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()

@dp.callback_query_handler(Text('back'), state=Answer.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()

@dp.callback_query_handler(state=Answer.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    if 'question' in callback.data:
        callback_data = callback.data.split(':')[1]
        from additional_functions import cache
        data = await cache.get(callback_data)
        information = json.loads(data)
        result = ''
        for key, value in information.items():
            result += f'{key}: {value}\n'
        await state.update_data(question_id=callback_data)
        await callback.message.edit_text(result, reply_markup=moder_choose_question_keyboard)
    elif callback.data == 'choose_answer':
        await callback.message.edit_text('Напишите свой ответ')
        await Answer.waiting_for_answer.set()
        