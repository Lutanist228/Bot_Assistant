from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text
import json

from db_actions import Database
from main import dp, bot
from keyboards import user_keyboard, moder_start_keyboard, moder_owner_start_keyboard
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
    add_moder = State()
    delete_moder = State()

class Global_Data_Storage():
    menu_temp_inf = 0

class Boltun_Question_Processing(StatesGroup):
    boltun_question = State()
    boltun_reply = State()
    boltun_back_to_menu = State() 
    gpt_question = State()

@dp.message_handler(commands=['start'])
async def process_start_message(message: types.Message):
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
    # Перенести в стартовое окно
        # answer =  'Вас приветствует тестовый Бот "Кафедры информационных и интернет-технологий"'
        # answer =  'Я могу отвечать на простые вопросы, связанные с процессом обучения на программах ЦК Сеченовского университета.\nНапишите свой вопрос.'

@dp.message_handler(state=Boltun_Question_Processing.boltun_question)
async def fuzzy_handling(message: types.Message, state: FSMContext):
    global BOLTUN_PATTERN
    await state.update_data(question=message.text) 
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!")
    await Boltun_Question_Processing.boltun_reply.set()
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
            question = data.get('question')
            message_id = await db.add_question(data_base_type="fuzzy_db", 
                                               question=question, 
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
    user_id = message.from_user.id
    question = await db.get_fuzzy_id(user_id=user_id)
    # В это строке нет смысла, как и в переделке функции get_question. Так как ты ее только здесь используешь
    # И можешь сразу ловить вопрос
    # question_extract = await db.get_question(question_id=question_id_extract, data_base_type="fuzzy_db")
# Поменял здесь блок кода
    user_name = message.from_user.full_name
    question_id = await db.add_question(user_id=user_id, user_name=user_name, question=question[0])
    answer = await answer_information(question[0])
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await message.reply('Вопрос был передан')

# @dp.message_handler(commands=['question'])
# async def process_question_command(message: types.Message):
#     if len(message.text) > 10:
#         question = message.text.split('/question')[-1]
#         await db.add_question(message.from_user.id, message.text)
#         # await bot.send_message(MODER_CHAT_ID,
#          #                      f'Вопрос от {message.from_user.full_name}: {question}')
#         await message.reply('Вопрос был передан')
#     else:
#         await message.answer('Неверный формат')

# @dp.message_handler(commands=['answer'], user_id=MODER_CHAT_ID, state='*')
# async def process_answer_command(message: types.Message, state: FSMContext):
#     questions = await db.get_unaswered_questions()
#     if len(questions) > 0:
#         question = questions[0]
#         await message.answer(f'Вопрос: {question[1]}:\n\n{question[2]}')
#         await Answer.waiting_for_answer.set()
#         await state.update_data(question_id=question[0], user_id=question[1])
#     else:
#         await message.answer('Нет вопросов')

@dp.message_handler(state=Answer.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    # Получаем айди и имя модера, чтобы сохранить в бд
    moder_id = message.from_user.id
    moder_name = message.from_user.full_name
    # Достаем айди вопроса, в котором должны обновить информацию/ответ
    data = await state.get_data()
    question_id = data.get('question_id')
    # Из бд получаем айди пользователя, чтобы отправить ему ответ
    user_id = await db.get_user_id(question_id)
    await db.update_question_id(question_id, message.text, moder_id, moder_name)
    await message.reply('Ответ отправлен')
    await bot.send_message(chat_id=user_id, text=f'Ответ: \n{message.text}')
    await state.finish()

@dp.message_handler(state=Answer.add_moder)
async def process_adding_moder(message: types.Message, state: FSMContext):
    # Обработка добавления модера, получаем айди и имя, завершаем состояние и т д
    moder_id = message.text.split()[0]
    moder_name = message.text.split()[1]
    await state.finish()
    await db.add_new_moder(moder_id=moder_id, moder_name=moder_name)
    await message.answer('Модер добавлен', reply_markup=moder_owner_start_keyboard)

@dp.message_handler(state=Answer.delete_moder)
async def process_deleting_moder(message: types.Message, state: FSMContext):
    # Тоже самое, что и с добавлением
    await db.delete_moder(message.text)
    await state.finish()
    await message.answer('Модер удален', reply_markup=moder_owner_start_keyboard)

@dp.message_handler(state=Answer.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    print(1)
    # Обработка вопроса пользователя. Добавляем вопрос в бд (айди пользователя, его имя и вопрос)
    question_id = await db.add_question(message.from_user.id, message.from_user.full_name, message.text)
    # Отправляем модерам, что пришел новый вопрос. Нужно придумать, что через определенный тайминг отправляло количество неотвеченных вопросов в чат тьюторов
    # Активация блока Chat gpt
    answer = await answer_information(message.text)
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await state.finish()
    await message.reply('Вопрос был передан', reply_markup=user_keyboard)