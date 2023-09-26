from main import dp, bot
from aiogram import types
from keyboards import Boltun_Step_Back, Boltun_Keys
from additional_functions import fuzzy_handler
from additional_functions import create_inline_keyboard, file_reader, save_to_txt
from message_handlers import Global_Data_Storage, cache, db, active_keyboard_status
from keyboards import user_keyboard, moder_choose_question_keyboard, moder_owner_start_keyboard, glavnoe_menu_keyboard, common_moder_start_keyboard
from keyboards import generate_answer_keyboard, Boltun_Step_Back, check_programm_keyboard
from Chat_gpt_module import answer_information
from message_handlers import BOLTUN_PATTERN
from states import User_Panel, Moder_Panel

from aiogram.types import InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
import json
from aiogram.dispatcher.filters import Text
from aiogram.utils import exceptions
from aiogram.utils.exceptions import TelegramAPIError
import asyncio

#------------------------------------------GENERAL HANDLERS---------------------------------------------

@dp.callback_query_handler(Text('glavnoe_menu'), state='*')
async def process_glavnoe_menu(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'Moder_Panel:waiting_for_answer':
        data = await state.get_data()
        question_id = data['question_id']
        await db.update_question_id(question_id=question_id,
                                    answer=None,
                                    moder_id=callback.message.from_user.id,
                                    moder_name=callback.message.from_user.full_name)
    # Обработка возврата в главное меню для всех
    user_id = callback.from_user.id
    moder_ids = await db.get_moder()
    await state.finish()
    for id in moder_ids:
        if user_id == id[0]:
            if id[1] == 'Owner':
                await callback.message.edit_text('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
            else:
                await callback.message.edit_text('Можем приступить к работе', reply_markup=common_moder_start_keyboard)
            return
    bot_answer = await callback.message.edit_text('Выберите дальнейшее действие', reply_markup=user_keyboard)
    await active_keyboard_status(user_id=callback.from_user.id, 
                                message_id=bot_answer.message_id, 
                                status='active')

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'user_instruction':
        await bot.send_document(chat_id=callback.from_user.id, document='BQACAgIAAxkBAAJLPmUJ25hpDXYYU7wgNxhjRhfRIZtqAAI8PwACr8VQSFPmdcVy5dhpMAQ')
        await callback.message.answer('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)
        await state.finish()
    elif callback.data == 'moder_instruction':
        await bot.send_document(chat_id=callback.from_user.id, document='BQACAgIAAxkBAAJLPWUJ24mmC2G8ozWpjDW05PxEorRyAAI7PwACr8VQSBscvkHFAmYDMAQ')
        await callback.message.answer('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)
        await state.finish()
    elif callback.data == 'make_question':
        # Обработка нажатия пользователя, чтобы задать вопрос и переход в это состояние
        bot_answer = await callback.message.edit_text('Задайте свой вопрос. Главное меню отменит ваше действие', reply_markup=glavnoe_menu_keyboard)
        await User_Panel.boltun_question.set()
        await state.update_data(message_id=bot_answer.message_id)
    elif callback.data == 'number_unanswered':
        # Получение количества вопросов без ответа, мб полезная для кого то функция, просто добавил
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        # Обработка нажатия модера для показа вопросов (Вопрос номер ...). И создание на основе информации из бд клавиатуры для этих вопросов
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Moder_Panel.choosing_answer.set()
    elif callback.data == 'add_moder':
        # Добавить модера, надо сделать проверку, что именно айди и имя через пробел и т д
        await callback.message.edit_text('Введите id и имя модератора через пробел.\n Роли: Moder и Owner', reply_markup=glavnoe_menu_keyboard)
        await Moder_Panel.add_moder.set()
    elif callback.data == 'delete_moder':
        # Удаление модера
        await callback.message.edit_text('Введите id модера', reply_markup=glavnoe_menu_keyboard)
        await Moder_Panel.delete_moder.set()
    elif callback.data =='upload_base':
        pass
    elif callback.data == 'check_programm':
        await User_Panel.check_programm.set()
        await callback.message.edit_text('Выберите поиск по ФИО или СНИЛС, чтобы проверить вашу программу на зачисление', 
                                         reply_markup=check_programm_keyboard)
    elif callback.data == 'make_announcement':
        await Moder_Panel.make_announcement.set()
        await callback.message.edit_text('Введите сообщение, которое хотите сделать объявлением', reply_markup=glavnoe_menu_keyboard)

#------------------------------------------USER HANDLERS------------------------------------------------

@dp.callback_query_handler(Boltun_Keys.cd.filter(), state = "*") 
async def boltun_keyboard(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data["action"]:
        global BOLTUN_PATTERN
        BOLTUN_PATTERN = file_reader("boltun.txt")
        cb_data = callback_data["action"].split("_") ; cb_data = int(cb_data[len(cb_data) - 1])
        # data = callback.message.reply_markup.inline_keyboard
        # key = f'{callback_data["@"]}:{callback_data["action"]}'

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
            await User_Panel.boltun_reply.set()
        except UnboundLocalError:
            await callback.answer(text="Ошибка. Просим перезапустить бота...")

@dp.callback_query_handler(state=User_Panel.check_programm)
async def program_checking(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'check_fio':
        bot_answer = await callback.message.edit_text('Введите свое ФИО строго через пробел и ожидайте ответа', 
                                         reply_markup=glavnoe_menu_keyboard)
        await User_Panel.check_fio.set()
        await state.update_data(message_id=bot_answer.message_id)
    elif callback.data == 'check_snils':
        bot_answer = await callback.message.edit_text('Введите свой СНИЛС строго в формате 000-000-000 00',
                                         reply_markup=glavnoe_menu_keyboard)
        await User_Panel.check_snils.set()
        await state.update_data(message_id=bot_answer.message_id)

#------------------------------------------MODER HANDLERS-----------------------------------------------
        
@dp.callback_query_handler(Text('back'), state=Moder_Panel.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возвращения назад
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Moder_Panel.choosing_answer.set()

@dp.callback_query_handler(state=Moder_Panel.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    # Обработка и вывод информации по клику на определенный вопрос
    if 'question:' in callback.data:
        callback_data = callback.data.split(':')[1]
        from additional_functions import cache
        # Получаем информацию по определенному вопросу и выводим
        data = await cache.get(callback_data)
        information = json.loads(data)
        result = ''
        for key, value in information.items():
            result += f'{key}: {value}\n'
            if key == 'question':
                await state.update_data(question=value)
        await state.update_data(question_id=callback_data)
        await callback.message.edit_text(result, reply_markup=moder_choose_question_keyboard)
    # Обработка выбора определенного вопроса
    elif callback.data == 'choose_question':
        markup = InlineKeyboardMarkup()
        data = await state.get_data()
        question_id = data['question_id']
        moder_id = callback.from_user.id
        moder_name = callback.from_user.full_name
        result_check = await db.check_question(question_id=question_id)
        if result_check[0] == 'Вопрос взят':
            await callback.message.edit_text('Выбери другой вопрос', reply_markup=glavnoe_menu_keyboard)
        else:
            await db.update_question_id(question_id=question_id, 
                    answer='Вопрос взят', 
                    moder_id=moder_id,
                    moder_name=moder_name)
            await callback.message.edit_reply_markup(reply_markup=markup)
            await callback.message.answer('''Напишите свой ответ или скопируйте ответа бота, если считаете его правильным.\nКнопка "Главное меню" вернет в главное меню.''', 
                                            reply_markup=generate_answer_keyboard)
            await Moder_Panel.waiting_for_answer.set()
    elif callback.data == 'close_question':
        data = await state.get_data()
        question_id = data['question_id']
        moder_id = callback.from_user.id
        moder_name = callback.from_user.full_name
        await db.update_question_id(question_id=question_id, 
                                    answer='Закрытие вопроса', 
                                    moder_id=moder_id,
                                    moder_name=moder_name)
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)

@dp.callback_query_handler(state=Moder_Panel.waiting_for_answer)
async def generate_answer(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'generate_answer':
            await callback.message.delete()
            data = await state.get_data()
            question_id = data['question_id']
            question = data['question']
            answer = await answer_information(question=question)
            await db.update_gpt_answer(question_id=question_id, answer=answer)
            await callback.message.answer(f'Сгенерированный ответ:\n{answer}')
    elif callback.data == 'do_not_generate_answer':
        await callback.message.delete()
        await callback.message.answer('Напишите свой ответ', reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'check_history':
        data = await state.get_data()
        question_id = data['question_id']
        user_id = await db.get_user_id(question_id=question_id)
        questions = await db.check_history(user_id=user_id)
        history = ''
        for question in questions:
            if question[7] == 'Вопрос взят':
                continue
            history += f'Дата-время: {question[5]}\nВопрос: {question[4]}\nОтвет: {question[7]}\n\n'
        await callback.message.edit_text(f'{history} Введите свой ответ или вернитесь в главное меню', 
                                         reply_markup=glavnoe_menu_keyboard)

@dp.callback_query_handler(state=Moder_Panel.adding_to_base)
async def process_base_answers(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'add_to_base':
        global BOLTUN_PATTERN
        data = await state.get_data()
        question = data['question']
        answer = data['answer']
        # тут, после успешного ответа на вопрос происходит то, что вопрос и ответ сохраняюся в boltun.txt
        save_to_txt(boltun=f"""u: {question}\n{answer}\n""")
        BOLTUN_PATTERN = file_reader("boltun.txt")
        await state.finish()
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'do_not_add_to_base':
        await state.finish()
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)

@dp.callback_query_handler(state=Moder_Panel.make_announcement)
async def proccess_type_of_announcement(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    announcement = data['announcement_text']
    ids_to_send = set()
    supergroup_ids = [-1001821625858]
    if callback.data == 'private_announcement':
        ids = await db.get_ids_for_announcement() + await db.get_checked_ids()
        for id in ids:
            ids_to_send.add(id[0])
        await callback.message.edit_text('Объявление отправляется, ожидайте')
        for index, id_to_send in enumerate(ids_to_send):
            if index % 20 == 0:
                await asyncio.sleep(3)
            try:
                bot_answer = await bot.send_message(chat_id=id_to_send, text=f'Объявление:\n\n{announcement}\n\nЕсли есть какие-то проблемы, то напишите /start', reply_markup=user_keyboard)
                await active_keyboard_status(user_id=id_to_send,
                                             message_id=bot_answer.message_id,
                                             status='active')
            except (exceptions.BotBlocked, exceptions.ChatNotFound, exceptions.CantInitiateConversation):
                continue
        await callback.message.edit_text(text='Объявление отправлено, вернитесь в главное меню', 
                                         reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'supergroup_announcement':
        for supergroup in supergroup_ids:
            await bot.send_message(chat_id=supergroup, text=f'Объявление:\n\n{announcement}')
        await callback.message.edit_text(text='Объявление отправлено, вернитесь в главное меню', 
                                    reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'both_announcement':
        ids = await db.get_ids_for_announcement() + await db.get_checked_ids()
        for id in ids:
            ids_to_send.add(id[0])
        await callback.message.edit_text('Объявление отправляется, ожидайте')
        for id_to_send in ids_to_send:
            try:
                await bot.send_message(chat_id=id_to_send, text=f'Объявление:\n\n{announcement}')
            except exceptions.BotBlocked:
                continue
        
        for supergroup in supergroup_ids:
            await bot.send_message(chat_id=supergroup, text=f'Объявление:\n\n{announcement}')
            
        await callback.message.edit_text(text='Объявление отправлено, вернитесь в главное меню', 
                                reply_markup=glavnoe_menu_keyboard)

#------------------------------------------ERROR HANDLERS-----------------------------------------------

@dp.errors_handler(exception=TelegramAPIError)
async def process_errors(update: types.Update, exception: exceptions):
    if isinstance(exception, exceptions.BotBlocked):
        await update.message.answer('Пользователь заблокировал бота,\nВернитесь в главное меню', 
                                    reply_markup=glavnoe_menu_keyboard)
