from main import dp, my_bot
from sql import db_start, sql_add_extract_data, sql_update_data
from additional_functions import file_reader, save_to_txt, fuzzy_handler
from buttons import get_cancel, get_start
from inline_key import Boltun_Keys
#from GPT_connect import sending_pattern, extracting_reply
# функции связанные с gpt пока что закомменчены до первых тестов gpt API

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

BOLTUN_PATTERN = file_reader("boltun.txt")
GPT_PATTERN = file_reader("tips.txt")

class Question_Processing(StatesGroup): # создаем класс состояний для перехода
    boltun_question = State()
    boltun_reply = State() 
    gpt_question = State()

async def on_startup(_):
    await db_start()
    # инициализируется база данных при старте бота 
    #sending_pattern(role="assistant", gpt_pattern=GPT_PATTERN)
    # sending_pattern отправляет паттерн GPT при старте работы бота 
    print("Pattern has been sent.")
    print("Data base has been created.")
    print("Bot has been turned on.")

@dp.message_handler(commands=["start"])
async def start_message(message: types.Message, state: FSMContext):
    await message.delete()
    answer =  'Вас приветствует тестовый Бот "Кафедры информационных и интернет-технологий"'
    await my_bot.send_message(message.chat.id, answer)
    answer =  'Я могу отвечать на простые вопросы, связанные с процессом обучения на программах ЦК.\nНапишите свой вопрос.'
    await my_bot.send_message(message.chat.id, answer)
    await Question_Processing.boltun_question.set() # переход на состояние question

@dp.message_handler(state=Question_Processing.boltun_question)
async def fuzzy_handling(message: types.Message, state: FSMContext):
    global BOLTUN_PATTERN
    await state.update_data(question=message.text) 
    # под ключ question помещается сообщение пользователя
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    # информация сохраняется в бд
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!", reply_markup=get_start())
    await state.set_state("boltun_reply")
    #reply_text = extracting_reply(role="assistant", message_text=message.text)
    reply_text, similarity_rate, list_of_questions = fuzzy_handler(boltun_text=BOLTUN_PATTERN, user_question=message.text)
    # тут будет обработка через отправку сообщения GPT (или на первых этапах будет достаточно boltun-а). Затем ответ возвращается,
    # сохраняется и передается в переменную answer. Пока что за reply_text 
    # закреплен текст вопроса пользователя.
    if reply_text != "Not Found":
        if 50 <= similarity_rate <= 80: 
            await my_bot.send_message(chat_id=message.from_user.id, text=f"Возможно вы имели в виду:\n", reply_markup=Boltun_Keys.get_keyboard(list_of_names=list_of_questions, user_id=message.from_user.id))
        else:
            await my_bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{reply_text}")
            message_id = await sql_add_extract_data(data_base_type="fuzzy_db", message_text=data, user_id=message.from_user.id) ; message_id = message_id[0]
            await sql_update_data(
                data_base_type="fuzzy_db",
                primary_key_value=message_id,
                bot_reply=reply_text,
                reply_status='TRUE',
                similarity_rate=similarity_rate
                )
            await state.finish()
    else:
        await Question_Processing.gpt_question.set()

@dp.message_handler(content_types=['text'])
# данный хендлер принимает или сообщение "Завершить процесс", что приводит к выходу из состояний,
# он так же обрабатывает любые сообщения отличные от заданных кнопками и командами.
async def on_reply_processing(message: types.Message, state: FSMContext):
    if message.text == "Завершить процесс":
        await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=get_start())
        await state.finish()
    else:
        answer =  'Для уточнения функциональности бота, нажмите на кнопку "Помощь".'
        await message.reply(text=answer)
    # до тех пор, пока пользователь не получил ответ, любое его сообщение будет игнорироваться 
    # необходимо поставить антифлуд на данный хендлер через MiddleWare





