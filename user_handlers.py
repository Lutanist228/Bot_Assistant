from aiogram import types
from aiogram.dispatcher import FSMContext
import json
from aiogram.dispatcher.filters import Text

from db_actions import Database
from main import dp, bot, db
from keyboards import user_keyboard, moder_start_keyboard, moder_owner_start_keyboard
from additional_functions import fuzzy_handler, check_program, file_reader
from chat_gpt_module import answer_information
from keyboards import Boltun_Step_Back, glavnoe_menu_keyboard, check_programm_keyboard
from cache_container import cache
from config_file import BOLTUN_PATTERN
from keyboards import Boltun_Keys
from states import User_Panel

class Global_Data_Storage():
    menu_temp_inf = 0
    question_temp_inf = ""

#____________________________MESSAGE__HANDLERS_______________________________________________________________________________

@dp.message_handler(commands=['start'])
async def process_start_message(message: types.Message):
    if message.chat.type == 'private':
    # Достаем айдишники модеров, чтобы проверить пользователя кем он является
        moder_ids = await db.get_moder()
        for id in moder_ids:
            if message.from_user.id == id[0]:
                # Проверка на админа, чтобы добавлять модеров и т д. А то они намудряд и добавят всякой фигни
                if id[1] == 'Owner':
                    await message.answer('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
                else:
                    await message.answer('Можем приступить к работе', reply_markup=moder_start_keyboard)
                return
        await message.delete()
        await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)
    else:
        await message.reply('Данная команда доступна только в личных сообщениях с ботом.\nИспользуйте "/question ваш вопрос"')
    
@dp.message_handler(state=User_Panel.boltun_question)
async def fuzzy_handling(message: types.Message, state: FSMContext):
    global BOLTUN_PATTERN
    await state.update_data(question=message.text) 
    Global_Data_Storage.question_temp_inf = message.text
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await User_Panel.boltun_reply.set()
    reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=message.text)
    if reply_text != "Not Found":
        if 50 <= similarity_rate <= 90:
            await message.answer(text="Отлично, а теперь дождитесь ответа бота!", reply_markup=Boltun_Step_Back.kb_failed_to_find)
            serialized_question_menu_data = json.dumps(list_of_questions)
            await cache.set(message.message_id, serialized_question_menu_data)
            Global_Data_Storage.menu_temp_inf = message.message_id
            gen_text = [f"""Вопрос №{num + 1}: {value}\n""" for num, value in enumerate(list_of_questions)] ; gen_text = ''.join(gen_text)
            await bot.send_message(chat_id=message.from_user.id, 
                                    text=f"Возможно вы имели в виду:\n\n{gen_text}",
                                    reply_markup=Boltun_Keys.get_keyboard(list_of_names=list_of_questions, user_id=message.from_user.id))
        else:
            await message.answer(text="Отлично, а теперь дождитесь ответа бота!")
            await bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{reply_text}", reply_markup=Boltun_Step_Back.kb_got_answer)
            question = data.get('question')
            message_id = await db.add_question(data_base_type="fuzzy_db", 
                                            question=question, 
                                            user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name,
                                            message_id=message.message_id,
                                            chat_type=message.chat.type)
            await db.update_fuzzy_data(
                primary_key_value=message_id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=similarity_rate
                )
            await User_Panel.boltun_reply.set()
    else:
        # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
        await db.add_question(user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name, 
                                            message_id=message.message_id, 
                                            question=message.text,
                                            chat_type=message.chat.type)
        # Отправляем модерам, что пришел новый вопрос. Нужно придумать, что через определенный тайминг отправляло количество неотвеченных вопросов в чат тьюторов
        await state.finish()
        await message.reply('Вопрос был передан', reply_markup=user_keyboard)

@dp.message_handler(text = "Не нашел подходящего вопроса", state=User_Panel.boltun_reply)
async def redirect_question(message: types.Message, state: FSMContext):
    await User_Panel.making_question.set()
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    question_id = await db.add_question(user_id=message.from_user.id, 
                                        user_name=message.from_user.full_name, 
                                        message_id=message.message_id, 
                                        question=Global_Data_Storage.question_temp_inf,
                                        chat_type=message.chat.type)
    # Отправляем модерам, что пришел новый вопрос. Нужно придумать, что через определенный тайминг отправляло количество неотвеченных вопросов в чат тьюторов
    # Активация блока Chat gpt
    answer = await answer_information(Global_Data_Storage.question_temp_inf)
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await state.finish()
    await message.reply('Вопрос был передан', reply_markup=user_keyboard)

@dp.message_handler(text = "Вернуться к выбору", state=User_Panel.boltun_reply)
# данный хендлер принимает или сообщение "Завершить процесс", что приводит к выходу из состояний,
# он так же обрабатывает любые сообщения отличные от заданных кнопками и командами.
async def on_reply_processing(message: types.Message):
    data = await cache.get(Global_Data_Storage.menu_temp_inf)
    if data:
            keyboard_data = json.loads(data)
    serialized_question_menu_data = json.dumps(keyboard_data)
    await cache.set(message.message_id, serialized_question_menu_data)
    Global_Data_Storage.menu_temp_inf = message.message_id

    gen_text = [f"""Вопрос №{num + 1}: {value}\n""" for num, value in enumerate(keyboard_data)] ; gen_text = ''.join(gen_text)  
    await bot.send_message(chat_id=message.from_user.id, text=gen_text, reply_markup=Boltun_Keys.get_keyboard(list_of_names=keyboard_data, user_id=message.from_user.id))
    # до тех пор, пока пользователь не получил ответ, любое его сообщение будет игнорироваться 
    # необходимо поставить антифлуд на данный хендлер через MiddleWare

@dp.message_handler(text = "Завершить процесс", state=User_Panel.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=user_keyboard)
    await state.finish()

@dp.message_handler(text = "Меня не устроил ответ", state=User_Panel.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question = await db.get_fuzzy_id(user_id=user_id)
    # В это строке нет смысла, как и в переделке функции get_question. Так как ты ее только здесь используешь
    # И можешь сразу ловить вопрос
    # question_extract = await db.get_question(question_id=question_id_extract, data_base_type="fuzzy_db")
# Поменял здесь блок кода
    user_name = message.from_user.full_name
    await db.add_question(user_id=user_id, 
                                        user_name=user_name, 
                                        question=question[0], 
                                        chat_type=message.chat.type, 
                                        message_id=message.message_id)
    await message.reply('Вопрос был передан')

@dp.message_handler(commands=['question'])
async def process_question_command(message: types.Message):
    # Обработка в чате вопроса через команду /question
    if len(message.text) > 10:
        chat_type = message.chat.type
        supergroup_id = message.chat.id
        question = message.text.split('/question')[-1]
        await db.add_question(user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name, 
                                            message_id=message.message_id,
                                            question=question,
                                            chat_type=chat_type,
                                            supergroup_id=supergroup_id)
        await message.reply('Вопрос был передан')
    else:
        await message.answer('Неверный формат')

@dp.message_handler(state=User_Panel.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    question_id = await db.add_question(message.from_user.id, 
                                        message.from_user.full_name, 
                                        message.text, chat_type=message.chat.type, 
                                        message_id=message.message_id)
    # Отправляем модерам, что пришел новый вопрос. Нужно придумать, что через определенный тайминг отправляло количество неотвеченных вопросов в чат тьюторов
    # Активация блока Chat gpt
    answer = await answer_information(message.text)
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await state.finish()
    await message.reply('Вопрос был передан', reply_markup=user_keyboard)

@dp.message_handler(text = "Вернуться в главное меню", state=None)
async def back_to_start(message: types.Message, state: FSMContext):
    await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)

@dp.message_handler(state=User_Panel.check_fio)
async def checking_fio(message: types.Message, state: FSMContext):
    video_path = '/home/admin2/Рабочий стол/Bot for CK/registration.mp4'
    await message.answer('Ожидайте ответа')
    name = message.text.strip()
    result = await check_program(name, method_check='fio')
    if result == 'Нет в зачислении':
        await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
    else:
        await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе',  reply_markup=user_keyboard)
        await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
Пройдите, пожалуйста, регистрацию на сайте
https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru\n\nНиже видео с регистрацией''')
        with open(video_path, 'rb') as video_file:
            video = types.InputFile(video_file)
            await bot.send_video(chat_id=message.from_user.id, video=video)
    await state.finish()

@dp.message_handler(state=User_Panel.check_snils)
async def process_check_programm(message: types.Message, state: FSMContext):
    video_path = '/home/admin2/Рабочий стол/Bot for CK/registration.mp4'
    await message.answer('Ожидайте ответа')
    name = message.text.strip()
    result = await check_program(name, method_check='snils')
    if result == 'Нет в зачислении':
        await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
    else:
        await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе',  reply_markup=user_keyboard)
        await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
Пройдите, пожалуйста, регистрацию на сайте
https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru\n\nНиже видое с регистрацией''')
        with open(video_path, 'rb') as video_file:
            video = types.InputFile(video_file)
            await bot.send_video(chat_id=message.from_user.id, video=video)
    await state.finish()

#____________________________MESSAGE__HANDLERS_______________________________________________________________________________

#____________________________CALLBACK_HANDLERS__________________________________________________________________________________

@dp.callback_query_handler(Text('glavnoe_menu'), state='*')
async def process_glavnoe_menu(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возврата в главное меню для всех    
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
            await User_Panel.boltun_reply.set()
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

#____________________________CALLBACK_HANDLERS__________________________________________________________________________________
