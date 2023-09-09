from main import dp, bot
from aiogram import types
from keyboards import Boltun_Step_Back, Boltun_Keys
from additional_functions import fuzzy_handler
from additional_functions import create_inline_keyboard, file_reader
from message_handlers import Answer, db, Global_Data_Storage, cache
from keyboards import user_keyboard, moder_start_keyboard, moder_choose_question_keyboard, moder_owner_start_keyboard, glavnoe_menu_keyboard
from Chat_gpt_module import answer_information

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
                                    user_name=callback.from_user.full_name,
                                    message_id=callback.id,
                                    chat_type=callback.chat_instance)
        
        reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=keyboard_data[cb_data])
    await bot.send_message(chat_id=callback.from_user.id, 
                              text=f"Ответ:\n{reply_text}", 
                              reply_markup=Boltun_Step_Back.kb_3)
    await db.update_fuzzy_data(
        primary_key_value=message_id,
        bot_reply=reply_text,
        reply_status='TRUE',
        similarity_rate=similarity_rate
        )
    await Answer.boltun_reply.set()

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

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'instruction':
        # Нужно будет написать инстуркцию
        await callback.message.answer('Инструкция')
    elif callback.data == 'make_question':
        # Обработка нажатия пользователя, чтобы задать вопрос и переход в это состояние
        await callback.message.edit_text('Задайте свой вопрос. Главное меню отменит ваше действие', reply_markup=glavnoe_menu_keyboard)
        await Answer.boltun_question.set()
    elif callback.data == 'number_unanswered':
        # Получение количества вопросов без ответа, мб полезная для кого то функция, просто добавил
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        # Обработка нажатия модера для показа вопросов (Вопрос номер ...). И создание на основе информации из бд клавиатуры для этих вопросов
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()
    elif callback.data == 'add_moder':
        # Добавить модера, надо сделать проверку, что именно айди и имя через пробел и т д
        await callback.message.edit_text('Введите id и имя модератора через пробел')
        await Answer.add_moder.set()
    elif callback.data == 'delete_moder':
        # Удаление модера
        await callback.message.edit_text('Введите id модера')
        await Answer.delete_moder.set()

@dp.callback_query_handler(Text('back'), state=Answer.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возвращения назад
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()

@dp.callback_query_handler(state=Answer.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    # Обработка и вывод информации по клику на определенный вопрос
    if 'question' in callback.data:
        callback_data = callback.data.split(':')[1]
        from additional_functions import cache
        # Получаем информацию по определенному вопросу и выводим
        data = await cache.get(callback_data)
        information = json.loads(data)
        result = ''
        for key, value in information.items():
            result += f'{key}: {value}\n'
        await state.update_data(question_id=callback_data)
        await callback.message.edit_text(result, reply_markup=moder_choose_question_keyboard)
    # Обработка выбора определенного вопроса
    elif callback.data == 'choose_answer':
        await callback.message.delete()
        await callback.message.answer('''Напишите свой ответ или скопируйте ответа бота, если считаете его правильным.\nКнопка "Главное меню" вернет в главное меню.''', 
                                      reply_markup=glavnoe_menu_keyboard)
        await Answer.waiting_for_answer.set()
        
