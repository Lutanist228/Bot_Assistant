from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

#                                             USER
#----------------------------------------------------------------------------------------------------------------
user_keyboard = InlineKeyboardMarkup(row_width=2)

question_button = InlineKeyboardButton(text='Задать вопрос', callback_data='make_question')
instruction_button = InlineKeyboardButton(text='Инструкция по взаимодействию', callback_data='instruction')

user_keyboard.add(question_button, instruction_button)

#                                             MODER
#----------------------------------------------------------------------------------------------------------------
moder_start_keyboard = InlineKeyboardMarkup(row_width=2)

number_of_unanswered_questions = InlineKeyboardButton(text='Ожидают ответа', callback_data='number_unanswered')
answer_the_question = InlineKeyboardButton(text='Ответить на вопрос', callback_data='answer_question')

moder_start_keyboard.add(number_of_unanswered_questions, answer_the_question)

#----------------------------------------------------------------------------------------------------------------
moder_choose_question_keyboard = InlineKeyboardMarkup(row_width=2)

choose_question = InlineKeyboardButton(text='Выбрать вопрос', callback_data='choose_answer')
back = InlineKeyboardButton(text='Назад', callback_data='back')

moder_choose_question_keyboard.add(choose_question, back)