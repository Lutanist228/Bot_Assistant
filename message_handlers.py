from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text
import json

from db_actions import Database
from main import dp, bot, MODER_CHAT_ID
from keyboards import user_keyboard, moder_start_keyboard, moder_choose_question_keyboard
from additional_functions import create_inline_keyboard, file_reader, save_to_txt, fuzzy_handler
from Chat_gpt_module import answer_information
from keyboards import Boltun_Step_Back
from config_file import BOLTUN_PATTERN
from cache_container import cache
from keyboards import Boltun_Keys

db = Database()
class Answer(StatesGroup):
    waiting_for_answer = State()
    making_question = State()
    choosing_answer = State()

class Global_Data_Storage():
    menu_temp_inf = 0

class Boltun_Question_Processing(StatesGroup):
    boltun_question = State()
    boltun_reply = State()
    boltun_back_to_menu = State() 
    gpt_question = State()

@dp.message_handler(commands=['start'])
async def process_start_message(message: types.Message):
    if str(message.from_user.id) == MODER_CHAT_ID:
        await message.answer('Можем приступить к работе', reply_markup=moder_start_keyboard)
    else:
        await message.delete()
        answer =  'Вас приветствует тестовый Бот "Кафедры информационных и интернет-технологий"'
        await bot.send_message(message.chat.id, answer)
        answer =  'Я могу отвечать на простые вопросы, связанные с процессом обучения на программах ЦК Сеченовского университета.\nНапишите свой вопрос.'
        await bot.send_message(message.chat.id, answer)
        await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)
        await answer_information()

@dp.message_handler(state=Boltun_Question_Processing.boltun_question)
async def fuzzy_handling(message: types.Message, state: FSMContext):
    global BOLTUN_PATTERN
    await state.update_data(question=message.text) 
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!")
    await state.set_state("boltun_reply")
    reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=message.text)
    if reply_text != "Not Found":
        if 50 <= similarity_rate <= 90: 
            serialized_question_menu_data = json.dumps(list_of_questions)
            await cache.set(message.message_id, serialized_question_menu_data)
            Global_Data_Storage.menu_temp_inf = message.message_id
            gen_text = [f"""Вопрос №{num + 1}: {value}\n""" for num, value in enumerate(list_of_questions)] ; gen_text = ''.join(gen_text)
            await bot.send_message(chat_id=message.from_user.id, 
                                      text=f"Возможно вы имели в виду:\n\n{gen_text}",
                                      reply_markup=Boltun_Keys.get_keyboard(list_of_names=list_of_questions, user_id=message.from_user.id))
        else:
            await bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{reply_text}", reply_markup=Boltun_Step_Back.kb_1)
            message_id = await db.add_question(data_base_type="fuzzy_db", 
                                               question=data, 
                                               user_id=message.from_user.id, 
                                               user_name=message.from_user.full_name)
            await db.update_fuzzy_data(
                primary_key_value=message_id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=similarity_rate
                )
            await Boltun_Question_Processing.boltun_reply.set()
    else:
        await Answer.making_question.set()


@dp.message_handler(state=Answer.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    question_id = await db.add_question(message.from_user.id, message.from_user.full_name, message.text)
    answer = await answer_information(message.text)
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await bot.send_message(MODER_CHAT_ID, 'Добавлен новый вопрос')
    await message.reply('Вопрос был передан')

@dp.message_handler(text = "Вернуться к выбору", state=Boltun_Question_Processing.boltun_reply)
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

@dp.message_handler(text = "Завершить процесс", state=Boltun_Question_Processing.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=user_keyboard)
    await state.finish()

@dp.message_handler(text = "Меня не устроил ответ", state=Boltun_Question_Processing.boltun_reply)
async def quitting(message: types.Message, state: FSMContext):
    question_id_extract = await db.get_fuzzy_id() ; question_id_extract = question_id_extract[0]
    question_extract = await db.get_question(question_id=question_id_extract, data_base_type="fuzzy_db")
    answer = await answer_information(question_extract.get("question"))
    await db.update_gpt_answer(question_id=question_id_extract, answer=answer)
    await bot.send_message(MODER_CHAT_ID, 'Добавлен новый вопрос')
    await message.reply('Вопрос был передан')

@dp.message_handler(commands=['question'])
async def process_question_command(message: types.Message):
    if len(message.text) > 10:
        question = message.text.split('/question')[-1]
        await db.add_question(message.from_user.id, message.text)
        await bot.send_message(MODER_CHAT_ID,
                               f'Вопрос от {message.from_user.full_name}: {question}')
        await message.reply('Вопрос был передан')
    else:
        await message.answer('Неверный формат')

@dp.message_handler(commands=['answer'], user_id=MODER_CHAT_ID, state='*')
async def process_answer_command(message: types.Message, state: FSMContext):
    questions = await db.get_unaswered_questions()
    if len(questions) > 0:
        question = questions[0]
        await message.answer(f'Вопрос: {question[1]}:\n\n{question[2]}')
        await Answer.waiting_for_answer.set()
        await state.update_data(question_id=question[0], user_id=question[1])
    else:
        await message.answer('Нет вопросов')

@dp.message_handler(state=Answer.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    moder_id = message.from_user.id
    moder_name = message.from_user.full_name
    data = await state.get_data()
    question_id = data.get('question_id')
    user_id = await db.get_user_id(question_id)
    await db.update_question_id(question_id, message.text, moder_id, moder_name)
    await message.reply('Ответ отправлен')
    await bot.send_message(chat_id=user_id, text=f'Ответ: \n{message.text}')
    await state.finish()
