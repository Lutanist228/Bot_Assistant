from main import dp, my_bot
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from buttons import On_Start
from sql import db_start, add_message, extract_message
from additional_functions import file_reader, save_to_txt

class User_Data(StatesGroup):
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
    await User_Data.question.set()

@dp.message_handler(state=User_Data.question)
async def recieving_message(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    data = await state.get_data()
    await add_message(data)
    await message.answer(text="Отлично, а теперь дождитесь ответа бота!")
    await state.set_state("reply")

@dp.message_handler(state=User_Data.reply)
async def sending_reply(message: types.Message, state: FSMContext):
    message_text = await extract_message() 
    # тут будет обработка через отправку сообщения GPT. Затем ответ возвращается,
    # сохраняется и передается в переменную answer.
    await message.reply(text="""В настоящий момент ваш вопрос обрабатывается,\n просим проявить терпение).""")
    await message.delete()
    # д
    await my_bot.send_message(chat_id=message.from_user.id, text=f"Ответ:\n{message_text}")
    await state.finish()





