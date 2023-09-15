from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
import json

from db_actions import Database
from main import dp, bot
from keyboards import user_keyboard, moder_start_keyboard, moder_owner_start_keyboard, question_base_keyboard
from additional_functions import create_inline_keyboard, fuzzy_handler, check_program
from chat_gpt_module import answer_information
from keyboards import Boltun_Step_Back
from cache_container import cache
from config_file import BOLTUN_PATTERN
from keyboards import Boltun_Keys

db = Database()

class Global_Data_Storage():
    menu_temp_inf = 0
    question_temp_inf = ""

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
    
@dp.message_handler(state=Answer.boltun_question)
async def fuzzy_handling(message: types.Message, state: FSMContext):
    global BOLTUN_PATTERN
    await state.update_data(question=message.text) 
    Global_Data_Storage.question_temp_inf = message.text
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await Answer.boltun_reply.set()
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
            await Answer.boltun_reply.set()
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

@dp.message_handler(text = "Не нашел подходящего вопроса", state=Answer.boltun_reply)
async def redirect_question(message: types.Message, state: FSMContext):
    await Answer.making_question.set()
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

@dp.message_handler(text = "Вернуться к выбору", state=Answer.boltun_reply)
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

@dp.message_handler(text = "Завершить процесс", state=Answer.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=user_keyboard)
    await state.finish()

@dp.message_handler(text = "Меня не устроил ответ", state=Answer.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question = await db.get_fuzzy_id(user_id=user_id)
    # В это строке нет смысла, как и в переделке функции get_question. Так как ты ее только здесь используешь
    # И можешь сразу ловить вопрос
    # question_extract = await db.get_question(question_id=question_id_extract, data_base_type="fuzzy_db")
# Поменял здесь блок кода
    user_name = message.from_user.full_name
    question_id = await db.add_question(user_id=user_id, 
                                        user_name=user_name, 
                                        question=question[0], 
                                        chat_type=message.chat.type, 
                                        message_id=message.message_id)
    answer = await answer_information(question[0])
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await message.reply('Вопрос был передан')

@dp.message_handler(commands=['question'])
async def process_question_command(message: types.Message):
    # Обработка в чате вопроса через команду /question
    if len(message.text) > 10:
        chat_type = message.chat.type
        supergroup_id = message.chat.id
        question = message.text.split('/question')[-1]
        question_id = await db.add_question(user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name, 
                                            message_id=message.message_id,
                                            question=question,
                                            chat_type=chat_type,
                                            supergroup_id=supergroup_id)
        await message.reply('Вопрос был передан')
    else:
        await message.answer('Неверный формат')

@dp.message_handler(state=Answer.making_question)
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

@dp.message_handler(state=Answer.check_fio)
async def checking_fio(message: types.Message, state: FSMContext):
    await message.answer('Ожидайте ответа')
    name = message.text.strip()
    result = await check_program(name, method_check='fio')
    if result == 'Нет в зачислении':
        await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
    else:
        await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе', reply_markup=user_keyboard)
        await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
Пройдите, пожалуйста, регистрацию на сайте
https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru''')
    await state.finish()

@dp.message_handler(state=Answer.check_snils)
async def process_check_programm(message: types.Message, state: FSMContext):
    await message.answer('Ожидайте ответа')
    name = message.text.strip()
    result = await check_program(name, method_check='snils')
    if result == 'Нет в зачислении':
        await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
    else:
        await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе', reply_markup=user_keyboard)
        await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
Пройдите, пожалуйста, регистрацию на сайте
https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru''')
    await state.finish()