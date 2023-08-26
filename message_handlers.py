from main import dp, my_bot
import asyncio as asy
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from sql import db_start, add_message, extract_message
from additional_functions import file_reader, save_to_txt
from buttons import get_cancel, get_start
count = 0

def counter_func(obj: int):
    obj += 1
    yield obj

class Question_Processing(StatesGroup):
    question = State()
    reply = State()

async def on_startup(_):
    await db_start()
    # добавить функцию которая отправляет gpt паттерны боту, чтобы он потом мог отвечать на вопросы студентов 
    # данные будут содержаться в GPT_pattern.txt.
    GPT_PATTERN = file_reader()
    print("Pattern has been sent.")
    print("Data base has been created.")
    print("Bot has been turned on.")

@dp.message_handler(commands=["start"])
async def start_message(message: types.Message, state: FSMContext):
    await message.delete()
    await my_bot.send_message(chat_id=message.from_user.id, text="Напишите ваш вопрос.")
    await Question_Processing.question.set()

@dp.message_handler(state=Question_Processing.question)
async def recieving_message(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    data = await state.get_data()
    await add_message(message_text=data, user_id=message.from_user.id)
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!", reply_markup=get_cancel())
    await state.set_state("reply")
    message_text = await extract_message() 
    # тут будет обработка через отправку сообщения GPT. Затем ответ возвращается,
    # сохраняется и передается в переменную answer.
    await asy.sleep(60), my_bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{message_text}")

@dp.message_handler(lambda message: message) 
async def on_reply_processing(message: types.Message, state: FSMContext):
    if message.text == "Завершить процесс":
        await message.reply("Действие отменено.\nВозврат в меню бота...", reply_markup=get_start())
        await state.finish()
    else:
        global count
        next(counter_func(count))
        await message.reply(text="""В настоящий момент ваш вопрос обрабатывается,\n просим проявить терпение).""")
        await message.delete()
    # до тех пор, пока пользователь не получил ответ, любое его сообщение будет игнорироваться 
    # необходимо поставить антифлуд на данный хендлер через MiddleWare




