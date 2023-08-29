from main import dp, my_bot
from sql import db_start, add_message, extract_sql_data
from additional_functions import file_reader, save_to_txt
from buttons import get_cancel, get_start
#from GPT_connect import sending_pattern, extracting_reply
# функции связанные с gpt пока что закомменчены до первых тестов gpt API

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

class Question_Processing(StatesGroup): # создаем класс состояний для перехода
    question = State()
    reply = State() 

async def on_startup(_):
    await db_start()
    # инициализируется база данных при старте бота 
    BOLTUN_PATTERN = file_reader("boltun.txt")
    GPT_PATTERN = file_reader("tips.txt")
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
    await Question_Processing.question.set() # переход на состояние question

@dp.message_handler(state=Question_Processing.question)
async def recieving_message(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text) 
    # под ключ question помещается сообщение пользователя
    data = await state.get_data() # сохраненные данные извлекаются и присваиваются data
    await add_message(message_text=data, user_id=message.from_user.id)
    # информация сохраняется в бд
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!", reply_markup=get_cancel())
    await state.set_state("reply")
    #reply_text = extracting_reply(role="assistant", message_text=message.text)
    reply_text = await extract_sql_data()
    # тут будет обработка через отправку сообщения GPT (или на первых этапах будет достаточно boltun-а). Затем ответ возвращается,
    # сохраняется и передается в переменную answer. Пока что за reply_text 
    # закреплен текст вопроса пользователя.
    await my_bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{reply_text}")

@dp.message_handler(content_types=['text'])
# данный хендлер принимает или сообщение "Завершить процесс", что приводит к выходу из состояний,
# он так же обрабатывает любые сообщения отличные от заданных кнопками и командами.
async def on_reply_processing(message: types.Message, state: FSMContext):
    if message.text == "Завершить процесс":
        await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=get_start())
        await state.finish()
    else:
        answer =  'Для уточнения функциональности бота, нажмите на кнопку "Помощь".'
        await message.reply(message.chat.id, answer)
    # до тех пор, пока пользователь не получил ответ, любое его сообщение будет игнорироваться 
    # необходимо поставить антифлуд на данный хендлер через MiddleWare





