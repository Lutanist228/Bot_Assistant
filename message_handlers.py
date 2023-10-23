from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.utils import exceptions
from aiogram.types import InlineKeyboardMarkup
from aiogram.types.message import ContentType as CT
import json
import asyncio
from typing import Union
from functools import wraps

from db_actions import Database
from main import dp, bot
from keyboards import user_keyboard, moder_owner_start_keyboard, question_base_keyboard, glavnoe_menu_keyboard, common_moder_start_keyboard
from keyboards import announcement_keyboard
from additional_functions import fuzzy_handler, check_program, process_connection_to_excel
from keyboards import Boltun_Step_Back
from cache_container import cache
from config_file import BOLTUN_PATTERN
from keyboards import Boltun_Keys
from states import User_Panel, Moder_Panel, Registration
from aiogram.types import ReplyKeyboardRemove 

#------------------------------------------ADDITIONAL FUNCTIONS-----------------------------------------------

async def active_keyboard_status(user_id: int, message_id: int, status: str):
    # Получаем айди пользователя, айди сообщения, в котором хранится активная клавиатура. Создание пустой Inline клавиатуры
    markup = InlineKeyboardMarkup()
    # Создание кеш-хранилища под айди пользователя, где будут хранится все сообщения с клавами. Удаления этого хранилища еще
    info = await cache.get(user_id)
    await cache.delete(user_id)
    # Прохождение по словарю с сообщениями и состояниями. Перевод всех сообщений до нового в неактивное состояние и редактировние клавы
    if info:
        for key, value in info.items():
            if value == 'not active':
                continue
            elif value == 'active' and status == 'not active':
                info[key] = status
            elif value == 'active' and message_id != key:
                value = 'not active'
                info[key] = value
                try:
                    await bot.edit_message_reply_markup(chat_id=user_id, 
                                                        message_id=key,
                                                        reply_markup=markup)
                except (exceptions.MessageToEditNotFound, exceptions.MessageNotModified):
                    pass
        # Добавление нового сообщения со статусом
        info[message_id] = status
        await cache.set(user_id, info)
    else:
        info = {}
        info[message_id] = status
        await cache.set(user_id, info)
        # Очистка кеш хранилища через час, чтобы не нагружать сервак. По идее должно все работать
        # await asyncio.sleep(3600)
        # await cache.delete(user_id)

async def process_timeout(time_for_sleep: int, chat_id: int, chat_type: str, message_id: int = None, state: FSMContext = None):
    if chat_type == 'private':
        # Таймаут на задачу вопроса и возврат пользователя если он так и не задал вопрос (проверяет по измению состояния)
        await asyncio.sleep(time_for_sleep)
        if await state.get_state() == 'User_Panel:boltun_question':
            await state.finish()
            bot_answer = await bot.send_message(chat_id=chat_id, 
                                text='Вы превисили время на вопрос. Возвращаю вас обратно в меню',
                                reply_markup=user_keyboard)
            await active_keyboard_status(user_id=chat_id, 
                message_id=bot_answer.message_id, 
                status='active')
        else:
            return
    elif chat_type == 'supergroup':
        await asyncio.sleep(time_for_sleep)
        await bot.delete_message(chat_id=chat_id,
                                 message_id=message_id)

# @dp.message_handler(content_types=[types.ContentType.VIDEO, types.ContentType.DOCUMENT])
async def process_videos(message: types.Message):
    print(message.video)
    print(message.document)

def quarry_definition_decorator(func):
    """
        Как работает этот декоратор:
        1. С помощью оберточной функции и именованных аргументов, заключенных в **kwargs,
        декоратор вычленяет значение переменных, что представляют собой изменяемые объекты 
        в з-ти от типа запроса: переменная вычисления message_id, переменная вычисления user_id,
        и другие
        2. Внутри декоратора выполняется проверка на тип запроса и только затем 
        вышеуказанные переменные меняются на те, что требует тот или иной тип запроса
        3. После перезаписи возвращается принимаемая функция, но уже с перезаписанными 
        переменными
    """
    @wraps(func) 
    async def async_wrapper(quarry_type, state, **kwargs):
                # quarry_type = filter(lambda x: isinstance(x, types.Message), args) ; quarry_type = next(quarry_type)
             
                if isinstance(quarry_type, types.Message) == True:
                    # kwargs["quarry_type"] = types.Message
                    # kwargs["state"] = state
                    kwargs["chat_id"] = quarry_type.chat.id
                    kwargs["user_id"] = quarry_type.from_user.id
                    kwargs["chat_type"] = quarry_type.chat.type
                elif isinstance(quarry_type, types.CallbackQuery) == True:
                    kwargs["chat_id"] = quarry_type.message.chat.id
                    # kwargs["quarry_type"] = types.CallbackQuery
                    # kwargs["state"] = state
                    kwargs["user_id"] = quarry_type.from_user.id
                    kwargs["chat_type"] = quarry_type.message.chat.type
                return await func(**kwargs) 
    return async_wrapper    

def user_registration_decorator(func):
    """
    Как работает этот декоратор:
    1. Обертка принимает именованные аргументы, такие, что ответственны за идентификацию пользователей 
    и засчет ветвления делегирует алгоритм в нужное русло.
    2. Принимаемая функция при этом НЕ меняется, а лишь выступает в качестве источника информации,
    а этот декоратор как бы - совокупность замков, ключи к которому - аргументы принимаемой функции.
    """
    async def async_wrapper(quarry_type, state, *args):
        @quarry_definition_decorator
        async def registration(chat_id, user_id, chat_type):
            moder_ids = await db.get_moder()
            for id in moder_ids:
                if user_id == id[0]:
                    if id[1] == 'Owner':
                        await bot.send_message(chat_id=chat_id, text='Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
                        return await func(quarry_type, state)
                    else:
                        await bot.send_message(chat_id=chat_id, text='Можем приступить к работе', reply_markup=common_moder_start_keyboard)
                        return await func(quarry_type, state)
            try:
                bot_answer = bot.send_message(chat_id=chat_id, text='Выберите дальнейшее действие', reply_markup=user_keyboard)
                await active_keyboard_status(user_id=user_id, 
                                    message_id=bot_answer.message_id, 
                                    status='active')
                return await func(quarry_type, state)
            except exceptions.MessageNotModified:
                pass
        return await registration(quarry_type, state)
    return async_wrapper

#------------------------------------------INIT BLOCK---------------------------------------------

db = Database()

class Global_Data_Storage():
    menu_temp_inf = 0   
    question_temp_inf = ""

#------------------------------------------GENERAL HANDLERS---------------------------------------------

@dp.message_handler(commands=['start'], state='*')
@user_registration_decorator
async def process_start_message(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text="Вы успешно вернулись в меню", reply_markup=ReplyKeyboardRemove())

    if message.chat.type == 'private':
        pass
    else:
        # Пересылка пользователя в личную переписку с ботом
        bot_supergroup = await message.answer('Данная команда доступна только в личных сообщениях с ботом.\nИспользуйте "<b>question</b> ваш вопрос"', parse_mode=types.ParseMode.HTML)
        # Удаления сообщения, отправленного ботом
        await process_timeout(time_for_sleep=20, chat_id=message.chat.id, chat_type=message.chat.type, 
                              message_id=bot_supergroup.message_id)
        try:
            await message.delete()
        except (exceptions.MessageCantBeDeleted, exceptions.MessageToDeleteNotFound):
            pass

#------------------------------------------USER HANDLERS------------------------------------------------

@dp.message_handler(state=User_Panel.boltun_question, content_types=[types.ContentType.TEXT, types.ContentType.PHOTO])
async def fuzzy_handling(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup()
    global BOLTUN_PATTERN
    # Если есть фото в сообщении, то будет брать из него описание или будет просто грузить фото без сообщения
    if message.photo:
        if message.caption:
            await state.update_data(question=message.caption)
            Global_Data_Storage.question_temp_inf = message.caption
        else:
            # Генерация сообщения для модеров
            await state.update_data(question='By system: Проблема на приложенном фото')
    else:
        await state.update_data(question=message.text) 
        Global_Data_Storage.question_temp_inf = message.text
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await User_Panel.boltun_reply.set()
    reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=data['question'])
    list_of_questions = list(set(list_of_questions))
    if reply_text != "Not Found":
        if 50 <= similarity_rate <= 85:
            await message.answer(text="Отлично, а теперь дождитесь ответа бота!", reply_markup=Boltun_Step_Back.kb_failed_to_find)
            serialized_question_menu_data = json.dumps(list_of_questions)
            await cache.set(message.message_id, serialized_question_menu_data)
            Global_Data_Storage.menu_temp_inf = message.message_id
            gen_text = [f"""Вопрос №{num + 1}: {value}\n""" for num, value in enumerate(list_of_questions)] ; gen_text = ''.join(gen_text)
            bot_answer_1 = await bot.send_message(chat_id=message.from_user.id, 
                                    text=f"Возможно вы имели в виду:\n\n{gen_text}",
                                    reply_markup=Boltun_Keys.get_keyboard(list_of_names=list_of_questions, user_id=message.from_user.id))
            await bot.edit_message_reply_markup(chat_id=message.from_user.id,
                                                message_id=data['message_id'],
                                                reply_markup=markup)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                message_id=bot_answer_1.message_id,     
                status='not active')
        else:
            await message.answer(text="Отлично, а теперь дождитесь ответа бота!")
            bot_answer_2 = await bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{reply_text}", reply_markup=Boltun_Step_Back.kb_got_answer)
            question = data.get('question')
            message_id = await db.add_question(data_base_type="fuzzy_db", 
                                            question=question, 
                                            user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name,
                                            message_id=message.message_id,
                                            chat_type=message.chat.type)
            await bot.edit_message_reply_markup(chat_id=message.from_user.id,
                                    message_id=data['message_id'],
                                    reply_markup=markup)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                message_id=bot_answer_2.message_id, 
                status='not active')
            await db.update_fuzzy_data(
                primary_key_value=message_id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=similarity_rate
                )
            await User_Panel.boltun_reply.set()
    else:
        # Проверка есть ли фото в сообщении и далее сохраняет описание, которое было записано ранее
        if message.photo:
            await db.add_question(user_id=message.from_user.id, 
                                    user_name=message.from_user.full_name, 
                                    message_id=message.message_id, 
                                    question=data['question'],
                                    chat_type=message.chat.type,
                                    photo_id=message.photo[-1].file_id)
        else:
            # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
            await db.add_question(user_id=message.from_user.id, 
                                                user_name=message.from_user.full_name, 
                                                message_id=message.message_id, 
                                                question=data['question'],
                                                chat_type=message.chat.type)
        # Отправляем модерам, что пришел новый вопрос. Нужно придумать, что через определенный тайминг отправляло количество неотвеченных вопросов в чат тьюторов
        await state.finish()
        bot_answer_3 = await message.reply('Вопрос был передан', reply_markup=user_keyboard)
        # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
        await active_keyboard_status(user_id=message.from_user.id, 
            message_id=bot_answer_3.message_id, 
            status='active')

@dp.message_handler(content_types = [CT.ANIMATION, CT.AUDIO, CT.DOCUMENT, CT.VIDEO, CT.VOICE, CT.STICKER, CT.POLL, CT.VIDEO_NOTE], state=User_Panel.boltun_question)
async def wrong_format(message: types.Message, state: FSMContext):
    await message.reply("""К сожалению, бот не поддерживает предоставленный формат данных.\nПросим ознакомиться с <b>инструкцией</b> к боту в главном меню""", reply_markup=glavnoe_menu_keyboard, parse_mode="HTML")
    await state.finish()

@dp.message_handler(text = "Не нашел подходящего вопроса", state=User_Panel.boltun_reply)
async def redirect_question(message: types.Message, state: FSMContext):
    await User_Panel.making_question.set()
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    await db.add_question(user_id=message.from_user.id, 
                                        user_name=message.from_user.full_name, 
                                        message_id=message.message_id, 
                                        question=Global_Data_Storage.question_temp_inf,
                                        chat_type=message.chat.type)
    await state.finish()
    await message.answer("Возврат в меню бота...", reply_markup=ReplyKeyboardRemove())
    bot_answer = await message.reply('Вопрос был передан', reply_markup=user_keyboard)
    # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
    await active_keyboard_status(user_id=message.from_user.id, 
                message_id=bot_answer.message_id,     
                status='active')

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
    await message.answer("Возврат в меню бота...", reply_markup=ReplyKeyboardRemove())
    bot_answer = await message.reply("Действие отменено", reply_markup=user_keyboard)
    await state.finish()
    # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
    await active_keyboard_status(user_id=message.from_user.id, 
            message_id=bot_answer.message_id, 
            status='active')

@dp.message_handler(text = "Меня не устроил ответ", state=User_Panel.boltun_reply)
async def quitting(message: types.Message):
    user_id = message.from_user.id
    question = await db.get_fuzzy_id(user_id=user_id)
    user_name = message.from_user.full_name
    await db.add_question(user_id=user_id, 
                                        user_name=user_name, 
                                        question=question[0], 
                                        chat_type=message.chat.type, 
                                        message_id=message.message_id)
    await message.answer("Возврат в меню бота...", reply_markup=ReplyKeyboardRemove())
    bot_answer = await message.reply('Вопрос был передан', reply_markup=glavnoe_menu_keyboard)
    # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
    await active_keyboard_status(user_id=message.from_user.id, 
        message_id=bot_answer.message_id, 
        status='active')

@dp.message_handler(text_startswith='question')
async def process_question_command(message: types.Message):
    # Обработка в чате вопроса через команду "question вопрос". Проверка, чтобы был не пустой вопрос
    if len(message.text) > 10:
        # Получаем, что это сообщение из канала и сохраняем айди чата, айди сообщения куда будет отсылать сообщение
        chat_type = message.chat.type
        supergroup_id = message.chat.id
        question = message.text.split('question')[-1]
        await db.add_question(user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name, 
                                            message_id=message.message_id,
                                            question=question,
                                            chat_type=chat_type,
                                            supergroup_id=supergroup_id)
    else:
        # Пробуем удалить сообщение если не подходит по критериям, для анти спама
        try:
            await message.delete()
        except exceptions.MessageCantBeDeleted:
            pass
        bot_delete = await message.answer('После <b>question</b> через пробел напишите свой вопрос.', parse_mode=types.ParseMode.HTML)
        # Отсчет тайминга удаления предыдущего сообщения от бота, чтобы не было спама
        await process_timeout(time_for_sleep=30, chat_id=message.chat.id, chat_type=message.chat.type,
                              message_id=bot_delete.message_id)

@dp.message_handler(lambda message: message.text not in ["Вернуться к выбору", "Завершить процесс", "Меня не устроил ответ", "/start"], content_types = [CT.ANIMATION, CT.AUDIO, CT.DOCUMENT, CT.POLL, CT.STICKER, CT.VIDEO, CT.VIDEO_NOTE, CT.TEXT, CT.VOICE, CT.PHOTO], state=[User_Panel.boltun_reply, None])
async def wrong_format(message: types.Message):
    if message.chat.type == 'private':
        await message.delete()
        await message.answer("Просим не спамить сообщениями - будьте внимательны и следуйте инструкции к боту")

@dp.message_handler(lambda message: message.text not in ["Вернуться к выбору", "Завершить процесс", "Меня не устроил ответ", "/start"], content_types = [CT.ANIMATION, CT.AUDIO, CT.DOCUMENT, CT.POLL, CT.STICKER, CT.VIDEO, CT.VIDEO_NOTE, CT.TEXT, CT.VOICE, CT.PHOTO], state=[User_Panel.boltun_reply, None])
async def wrong_format(message: types.Message):
    await message.delete()
    await message.answer("Просим не спамить сообщениями - будьте внимательны и следуйте <b>инструкцией</b> к боту", parse_mode="HTML")

@dp.message_handler(state=User_Panel.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    await db.add_question(message.from_user.id, 
                                        message.from_user.full_name, 
                                        message.text, chat_type=message.chat.type, 
                                        message_id=message.message_id)
    await state.finish()
    await message.reply('Вопрос был передан', reply_markup=user_keyboard)

@dp.message_handler(text = 'Вернуться в главное меню', state=None)
async def back_to_start(message: types.Message):
    moder_ids = await db.get_moder()
    for id in moder_ids:
        if message.from_user.id == id[0]:
            # Проверка на админа, чтобы добавлять модеров и т д. А то они намудряд и добавят всякой фигни
            if id[1] == 'Moder':
                await message.answer('Можем приступить к работе', reply_markup=common_moder_start_keyboard)
            return
    await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)

@dp.message_handler(state=User_Panel.fio)
async def checking_fio(message: types.Message, state: FSMContext):
    # Удаляем не нужные пробелы в сообщении получаем информацию из состояния. А именно метод того, что хотим найти ссылка/тьютор и т.д.
    name = message.text.strip()
    data = await state.get_data()
    method = data['method']
    if method == 'link':
        # Отправляем запрос по поиску нужной информации с нужным методом
        result = await check_program(name, method_check='link_fio')
        if result == 'Нет в зачислении':
            bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_1.message_id, 
                        status='active')
        else:
            # Достаем из словаря нужное значение по ключу
            link = data['chats'][result]
            bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n{result}\nСсылка на канал:\n{link}', reply_markup=user_keyboard)
            # Добавляем в бд проверенного чела для дальнейшей рассылки
            await db.add_checked_id(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                            message_id=bot_answer_2.message_id, 
                            status='active')
        await state.finish()
    elif method == 'tutor':
        # Отправляем запрос по поиску нужной информации с нужным методом
        result = await check_program(name, method_check='tutor_fio')
        if result == 'Нет в зачислении':
            bot_answer_3 = await message.answer('За вами не закреплен тьютор, задайте новый вопрос и сообщите об этом', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_3.message_id, 
                        status='active')
        else:
            # Достаем из словаря нужное значение по ключу
            tutor = data['tutor'][result.strip()]
            bot_answer_4 = await message.answer(f'Ваш тьютор: {result}\nСсылка на него: {tutor}', reply_markup=user_keyboard)
            # Добавляем в бд проверенного чела для дальнейшей рассылки
            await db.add_checked_id(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                            message_id=bot_answer_4.message_id, 
                            status='active')
        await state.finish()
    elif method == 'registration':
        await bot.send_chat_action(chat_id=message.from_user.id,
                                   action='typing')
        # Отправляем запрос по поиску нужной информации с нужным методом
        result = await check_program(name, method_check='registration_fio')
        if result == 'Нет в зачислении':
            bot_answer_5 = await message.answer('Вас нет в данный момент в таблице', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_5.message_id, 
                        status='active')
            await state.finish()
        elif result[0] == 'found':
            bot_answer_6 = await message.answer('Введите хэштег проекта')
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_6.message_id, 
                        status='active')
            await Registration.get_tag.set()
            await state.update_data(row=result[1], worksheet=result[2])
            await db.add_to_programm(user_id=message.from_user.id, user_name=message.from_user.full_name, program=result[2])

@dp.message_handler(state=User_Panel.snils)
async def checking_snils(message: types.Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    method = data['method']
    if method == 'link':
        result = await check_program(name, method_check='link_snils')
        if result == 'Нет в зачислении':
            bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_1.message_id, 
                        status='active')
        else:
            # Достаем из словаря нужное значение по ключу
            link = data['chats'][result]
            bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n{result}\nСсылка на канал:\n{link}', reply_markup=user_keyboard)
            # Добавляем в бд проверенного чела для дальнейшей рассылки
            await db.add_checked_id(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                            message_id=bot_answer_2.message_id, 
                            status='active')
        await state.finish()
    elif method == 'tutor':
        result = await check_program(name, method_check='tutor_snils')
        if result == 'Нет в зачислении':
            bot_answer_3 = await message.answer('За вами не закреплен тьютор, задайте новый вопрос и сообщите об этом', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_3.message_id, 
                        status='active')
        else:
            # Достаем из словаря нужное значение по ключу
            tutor = data['tutor'][result.strip()]
            bot_answer_4 = await message.answer(f'Ваш тьютор: {result}\nСсылка на него: {tutor}', reply_markup=user_keyboard)
            # Добавляем в бд проверенного чела для дальнейшей рассылки
            await db.add_checked_id(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                            message_id=bot_answer_4.message_id, 
                            status='active')
        await state.finish()
    elif method == 'registration':
        await bot.send_chat_action(chat_id=message.from_user.id,
                                   action='typing')
        # Отправляем запрос по поиску нужной информации с нужным методом
        result = await check_program(name, method_check='registration_snils')
        if result == 'Нет в зачислении':
            bot_answer_5 = await message.answer('Вас нет в данный момент в таблице', reply_markup=user_keyboard)
            # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_5.message_id, 
                        status='active')
            await state.finish()
        elif result[0] == 'found':
            bot_answer_6 = await message.answer('Введите хэштег проекта')
            await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_6.message_id, 
                        status='active')
            await Registration.get_tag.set()
            await state.update_data(row=result[1], worksheet=result[2])
            await db.add_to_programm(user_id=message.from_user.id, user_name=message.from_user.full_name, program=result[2])

# Обработка предложений/улучшений
@dp.message_handler(state=User_Panel.suggestion, content_types=[CT.TEXT, CT.PHOTO])
async def process_suggestion(message: types.Message, state: FSMContext):
    # Проверка есть ли фото в сообщении
    if message.photo:
        # Проверка есть ли описания под фоткой
        if message.caption:
            await db.add_suggestion(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name,
                                    suggestion=message.caption,
                                    picture_id=message.photo[-1].file_id)
        else:
            await db.add_suggestion(user_id=message.from_user.id,
                                    user_name=message.from_user.full_name,
                                    suggestion='Предложение на фото',
                                    picture_id=message.photo[-1].file_id)
        bot_answer_1 = await message.answer('Ваше предложение отправлено', reply_markup=user_keyboard)
        # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
        await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_1.message_id, 
                        status='active')
        await state.finish()
    else:
        await db.add_suggestion(user_id=message.from_user.id,
                                user_name=message.from_user.full_name,
                                suggestion=message.text)
        bot_answer_2 = await message.answer('Ваше предложение отправлено', reply_markup=user_keyboard)
        # Показываем, что сообщение выще с Inline является на данный момент активным. Посылаем айди этого сообщения и айди чата
        await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_2.message_id, 
                        status='active')
        await state.finish()

# @dp.message_handler(state=User_Panel.check_fio)
# async def checking_fio(message: types.Message, state: FSMContext):
#     name = message.text.strip()
#     result = await check_program(name, method_check='fio')
#     if result == 'Нет в зачислении':
#         bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                     message_id=bot_answer_1.message_id, 
#                     status='active')
#     else:
#         bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await db.add_checked_id(user_id=message.from_user.id,
#                                 user_name=message.from_user.full_name)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                         message_id=bot_answer_2.message_id, 
#                         status='active')
#     await state.finish()

# @dp.message_handler(state=User_Panel.check_snils)
# async def process_check_programm(message: types.Message, state: FSMContext):
#     name = message.text.strip()
#     result = await check_program(name, method_check='snils')
#     if result == 'Нет в зачислении':
#         bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                     message_id=bot_answer_1.message_id, 
#                     status='active')
#     else:
#         bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await db.add_checked_id(user_id=message.from_user.id,
#                             user_name=message.from_user.full_name)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                         message_id=bot_answer_2.message_id, 
#                         status='active')
#     await state.finish()

@dp.message_handler(state=Registration.get_tag)
async def process_getting_tag(message: types.Message, state: FSMContext):
    data = await state.get_data()
    row_num = data['row']
    worksheet_name = data['worksheet']
    result = await db.get_project(project_tag=message.text)
    if result:
        await Registration.role.set()
        await state.update_data(row=row_num, worksheet=worksheet_name, project=result)
        await message.answer('Опишите вашу роль в команде. Навыки, опыт и т.д.')
    else:
        bot_answer = await message.answer('Такого проекта нет. Проверьте написание и введите его снова, либо вернитесь в главное меню.', reply_markup=glavnoe_menu_keyboard)
        await active_keyboard_status(user_id=message.from_user.id, 
                         message_id=bot_answer.message_id, 
                         status='active')

@dp.message_handler(state=Registration.role)
async def process_getting_role(message: types.Message, state: FSMContext):
    data = await state.get_data()
    row_num = data['row']
    worksheet_name = data['worksheet']
    result = data['project']
    await process_connection_to_excel(status='edit', row=row_num, worksheet_name=worksheet_name, data=result, role=message.text)
    bot_answer = await message.answer('Ваш проект успешно обновлен в таблице', reply_markup=user_keyboard)
    await active_keyboard_status(user_id=message.from_user.id, 
                         message_id=bot_answer.message_id, 
                         status='active')
    await state.finish()

#------------------------------------------MODER HANDLERS-----------------------------------------------

@dp.message_handler(state=Moder_Panel.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    # Получаем айди и имя модера, чтобы сохранить в бд
    moder_id = message.from_user.id
    moder_name = message.from_user.full_name
    # Достаем айди вопроса, в котором должны обновить информацию/ответ
    data = await state.get_data()
    question_id = data.get('question_id')
    # Из бд получаем айди пользователя, чтобы отправить ему ответ
    user_id = await db.get_user_id(question_id)
    # Получаем айди сообщения, чтобы наглядно было видно на какое отвечаем
    message_id = await db.get_message_id(question_id)
    # Получаем вид чата и его айди, чтобы отвечать в больших чатах
    chat_type, chat_id = await db.get_chat_type_and_id(question_id)
    question = await db.get_question(question_id=question_id)
    await db.update_question_id(question_id, message.text, moder_id, moder_name)
    await message.reply('Ответ отправлен')
    if chat_type == 'supergroup':
        await bot.send_message(chat_id=chat_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id, parse_mode=types.ParseMode.HTML)
        await state.finish()
    else:
        try:
            await bot.send_message(chat_id=user_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id, parse_mode=types.ParseMode.HTML)
            await state.finish()
        except exceptions.BotBlocked:
            await message.answer('Пользователь заблокировал бота,\nВернитесь в главное меню', 
                                    reply_markup=glavnoe_menu_keyboard)
        # Блок по добавлению в базу ответов
    await message.answer('Внести его в базу данных вопросов?', reply_markup=question_base_keyboard)
    await Moder_Panel.adding_to_base.set()
    await state.update_data(question=question.get('question'), answer=message.text)

@dp.message_handler(state=Moder_Panel.add_moder)
async def process_adding_moder(message: types.Message, state: FSMContext):
    # Обработка добавления модера, получаем айди и имя, завершаем состояние и т д
    moder_id = message.text.split()[0]
    moder_name = message.text.split()[1]
    moder_role = message.text.split()[2]
    await state.finish()
    await db.add_new_moder(moder_id=moder_id, moder_name=moder_name, role=moder_role)
    await message.answer('Модер добавлен', reply_markup=moder_owner_start_keyboard)

@dp.message_handler(state=Moder_Panel.delete_moder)
async def process_deleting_moder(message: types.Message, state: FSMContext):
    # Тоже самое, что и с добавлением
    await db.delete_moder(message.text)
    await state.finish()
    await message.answer('Модер удален', reply_markup=moder_owner_start_keyboard)

@dp.message_handler(state=Moder_Panel.make_announcement)
async def process_announcement(message: types.Message, state: FSMContext):
    announcement = message.text
    await state.update_data(announcement_text=announcement)
    await message.answer('Выберите тип публикации', reply_markup=announcement_keyboard)

#------------------------------------------ERROR HANDLERS-----------------------------------------------

# @dp.errors_handler(exception=TelegramAPIError)
# async def process_errors(update: types.Update, exception: exceptions):
#     if isinstance(exception, exceptions.BotBlocked):
#         await update.message.answer('Пользователь заблокировал бота,\nВернитесь в главное меню', 
#                                     reply_markup=glavnoe_menu_keyboard)


