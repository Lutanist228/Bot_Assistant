from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text
import json

from db_actions import Database
from main import dp, bot, MODER_CHAT_ID
from keyboards import user_keyboard, moder_start_keyboard, moder_choose_question_keyboard
from additional_func import create_inline_keyboard
from Chat_gpt_module import answer_information


db = Database()
class Answer(StatesGroup):
    waiting_for_answer = State()
    making_question = State()
    choosing_answer = State()

@dp.message_handler(commands=['start'])
async def process_start_message(message: types.Message):
    if str(message.from_user.id) == MODER_CHAT_ID:
        await message.answer('Можем приступить к работе', reply_markup=moder_start_keyboard)
    else:
        await message.answer('Выберите дальнейшее действие', reply_markup=user_keyboard)
        await answer_information()


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

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'instruction':
        await callback.message.answer('Инструкция')
    elif callback.data == 'make_question':
        await callback.message.edit_text('Задайте свой вопрос')
        await Answer.making_question.set()
    elif callback.data == 'number_unanswered':
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()


@dp.callback_query_handler(Text('back'), state=Answer.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()


@dp.callback_query_handler(state=Answer.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    if 'question' in callback.data:
        callback_data = callback.data.split(':')[1]
        from additional_func import cache
        data = await cache.get(callback_data)
        information = json.loads(data)
        result = ''
        for key, value in information.items():
            result += f'{key}: {value}\n'
        await state.update_data(question_id=callback_data)
        await callback.message.edit_text(result, reply_markup=moder_choose_question_keyboard)
    elif callback.data == 'choose_answer':
        await callback.message.edit_text('Напишите свой ответ')
        await Answer.waiting_for_answer.set()
        

@dp.message_handler(state=Answer.making_question)
async def process_question_button(message: types.Message, state: FSMContext):
    question_id = await db.add_question(message.from_user.id, message.from_user.full_name, message.text)
    answer = await answer_information(message.text)
    await db.update_gpt_answer(question_id=question_id, answer=answer)
    await bot.send_message(MODER_CHAT_ID, 'Добавлен новый вопрос')
    await message.reply('Вопрос был передан')