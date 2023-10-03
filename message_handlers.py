from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.utils import exceptions
from aiogram.types import InlineKeyboardMarkup
import json
import asyncio

from db_actions import Database
from main import dp, bot
from keyboards import user_keyboard, moder_owner_start_keyboard, question_base_keyboard, glavnoe_menu_keyboard, common_moder_start_keyboard
from keyboards import announcement_keyboard
from additional_functions import fuzzy_handler, check_program
from keyboards import Boltun_Step_Back
from cache_container import cache
from config_file import BOLTUN_PATTERN
from keyboards import Boltun_Keys
from states import User_Panel, Moder_Panel

db = Database()

class Global_Data_Storage():
    menu_temp_inf = 0   
    question_temp_inf = ""

#------------------------------------------GENERAL HANDLERS---------------------------------------------

@dp.message_handler(commands=['start'], state='*')
async def process_start_message(message: types.Message, state: FSMContext):
    """ 
    Process 'Start' command and check if user is moder or not
    After it sends keyboards

    :param message: 'Start' command
    """
    await state.finish()
    if message.chat.type == 'private':
    # Достаем айдишники модеров, чтобы проверить пользователя кем он является
        moder_ids = await db.get_moder()
        for id in moder_ids:
            if message.from_user.id == id[0]:
                # Проверка на админа, чтобы добавлять модеров и т д. А то они намудряд и добавят всякой фигни
                if id[1] == 'Owner':
                    await message.answer('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
                else:
                    await message.answer('Можем приступить к работе', reply_markup=common_moder_start_keyboard)
                return
        await message.delete()
        bot_answer = await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)
        await active_keyboard_status(user_id=message.from_user.id, 
                                     message_id=bot_answer.message_id, 
                                     status='active')
    else:
        await message.reply('Данная команда доступна только в личных сообщениях с ботом.\nИспользуйте "/question ваш вопрос"')

#------------------------------------------USER HANDLERS------------------------------------------------

@dp.message_handler(state=User_Panel.boltun_question, content_types=[types.ContentType.TEXT, types.ContentType.PHOTO])
async def fuzzy_handling(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup()
    global BOLTUN_PATTERN
    if message.photo:
        if message.caption:
            await state.update_data(question=message.caption)
            Global_Data_Storage.question_temp_inf = message.caption
        else:
            await state.update_data(question='By system: Проблема на приложенном фото')
    else:
        await state.update_data(question=message.text) 
        Global_Data_Storage.question_temp_inf = message.text
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await User_Panel.boltun_reply.set()
    reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=data['question'])
    list_of_questions = list(set(list_of_questions))
    if reply_text != "Not Found":
        if 50 <= similarity_rate <= 90:
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
        await active_keyboard_status(user_id=message.from_user.id, 
            message_id=bot_answer_3.message_id, 
            status='active')

@dp.message_handler(text = "Не нашел подходящего вопроса", state=User_Panel.boltun_reply)
async def redirect_question(message: types.Message, state: FSMContext):
    await User_Panel.making_question.set()
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    question_id = await db.add_question(user_id=message.from_user.id, 
                                        user_name=message.from_user.full_name, 
                                        message_id=message.message_id, 
                                        question=Global_Data_Storage.question_temp_inf,
                                        chat_type=message.chat.type)
    await state.finish()
    bot_answer = await message.reply('Вопрос был передан', reply_markup=user_keyboard)
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
    bot_answer = await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=user_keyboard)
    await state.finish()
    await active_keyboard_status(user_id=message.from_user.id, 
            message_id=bot_answer.message_id, 
            status='active')

@dp.message_handler(text = "Меня не устроил ответ", state=User_Panel.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question = await db.get_fuzzy_id(user_id=user_id)
    user_name = message.from_user.full_name
    question_id = await db.add_question(user_id=user_id, 
                                        user_name=user_name, 
                                        question=question[0], 
                                        chat_type=message.chat.type, 
                                        message_id=message.message_id)
    bot_answer = await message.reply('Вопрос был передан', reply_markup=glavnoe_menu_keyboard)
    await active_keyboard_status(user_id=message.from_user.id, 
        message_id=bot_answer.message_id, 
        status='active')

@dp.message_handler(commands=['question'])
async def process_question_command(message: types.Message):
    # Обработка в чате вопроса через команду /question
    if len(message.text) > 10 and not '@SechenovCK_bot' in message.text:
        chat_type = message.chat.type
        supergroup_id = message.chat.id
        question = message.text.split('/question')[-1]
        question_id = await db.add_question(user_id=message.from_user.id, 
                                            user_name=message.from_user.full_name, 
                                            message_id=message.message_id,
                                            question=question,
                                            chat_type=chat_type,
                                            supergroup_id=supergroup_id)
    elif '@SechenovCK_bot' in message.text:
        try:
            await message.delete()
        except exceptions.MessageCantBeDeleted:
            pass
        await message.answer('После /question через пробел напишите свой вопрос без использования тега бота')
    else:
        try:
            await message.delete()
        except exceptions.MessageCantBeDeleted:
            pass
        await message.answer('После /question через пробел напишите свой вопрос')

@dp.message_handler(state=User_Panel.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    question_id = await db.add_question(message.from_user.id, 
                                        message.from_user.full_name, 
                                        message.text, chat_type=message.chat.type, 
                                        message_id=message.message_id)
    await state.finish()
    await message.reply('Вопрос был передан', reply_markup=user_keyboard)

@dp.message_handler(text = "Вернуться в главное меню", state=None)
async def back_to_start(message: types.Message, state: FSMContext):
    moder_ids = await db.get_moder()
    for id in moder_ids:
        if message.from_user.id == id[0]:
            # Проверка на админа, чтобы добавлять модеров и т д. А то они намудряд и добавят всякой фигни
            if id[1] == 'Moder':
                await message.answer('Можем приступить к работе', reply_markup=common_moder_start_keyboard)
            return
    await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)

@dp.message_handler(state=User_Panel.check_fio)
async def checking_fio(message: types.Message, state: FSMContext):
    name = message.text.strip()
    result = await check_program(name, method_check='fio')
    if result == 'Нет в зачислении':
        bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
        await active_keyboard_status(user_id=message.from_user.id, 
                    message_id=bot_answer_1.message_id, 
                    status='active')
    else:
        bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе',  reply_markup=user_keyboard)
#         await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
# Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
# Пройдите, пожалуйста, регистрацию на сайте
# https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru\n\nНиже видео с регистрацией''')
#         await bot.send_video(chat_id=message.from_user.id, video='BAACAgIAAxkBAAI0ZGUFbRF-egctzuSd6VcgBvcXpZ_bAAIjNAAC2sExSOC6b27__vhVMAQ')
        await db.add_checked_id(user_id=message.from_user.id,
                                user_name=message.from_user.full_name)
        await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_2.message_id, 
                        status='active')
    await state.finish()

@dp.message_handler(state=User_Panel.check_snils)
async def process_check_programm(message: types.Message, state: FSMContext):
    name = message.text.strip()
    result = await check_program(name, method_check='snils')
    if result == 'Нет в зачислении':
        bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
        await active_keyboard_status(user_id=message.from_user.id, 
                    message_id=bot_answer_1.message_id, 
                    status='active')
    else:
        bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await message.answer(f'Ваша программа зачисления:\n"{result}"\nЕсли вы хотите поменять, то напишите тьютору или через главное меню в вопросе',  reply_markup=user_keyboard)
#         await message.answer('''Ваша заявка была одорена для зачисления на курс цифровой кафедры. 
# Чтобы все учебные материалы стали вам доступны, нам необходимо зарегистрировать вас в Личном кабинете Сеченовского Университета. 
# Пройдите, пожалуйста, регистрацию на сайте
# https://abiturient.sechenov.ru/auth/?registration=yes&lang_ui=ru\n\nНиже видео с регистрацией''')
#         await bot.send_video(chat_id=message.from_user.id, video='BAACAgIAAxkBAAI0ZGUFbRF-egctzuSd6VcgBvcXpZ_bAAIjNAAC2sExSOC6b27__vhVMAQ')
        await db.add_checked_id(user_id=message.from_user.id,
                            user_name=message.from_user.full_name)
        await active_keyboard_status(user_id=message.from_user.id, 
                        message_id=bot_answer_2.message_id, 
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
        await bot.send_message(chat_id=chat_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id)
        await state.finish()
    else:
        await bot.send_message(chat_id=user_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id)
        await state.finish()
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

@dp.errors_handler(exception=TelegramAPIError)
async def process_errors(update: types.Update, exception: exceptions):
    if isinstance(exception, exceptions.BotBlocked):
        await update.message.answer('Пользователь заблокировал бота,\nВернитесь в главное меню', 
                                    reply_markup=glavnoe_menu_keyboard)

#------------------------------------------ADDITIONAL FUNCS----------------------------------------------

async def active_keyboard_status(user_id: int, message_id: int, status: str):
    markup = InlineKeyboardMarkup()
    info = await cache.get(user_id)
    await cache.delete(user_id)
    if info:
        for key, value in info.items():
            if value == 'not active':
                continue
            elif value == 'active' and status == 'not active':
                info[key] = status
            elif value == 'active' and message_id != key:
                value = 'not active'
                info[key] = value
                await bot.edit_message_reply_markup(chat_id=user_id, 
                                                    message_id=key,
                                                    reply_markup=markup)
        info[message_id] = status
        await cache.set(user_id, info)
    else:
        info = {}
        info[message_id] = status
        await cache.set(user_id, info)

async def process_timeout(time_for_sleep: int, state: FSMContext, chat_id: int):
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

@dp.message_handler(content_types=types.ContentType.VIDEO)
async def process_videos(message: types.Message):
    print(message.video)
