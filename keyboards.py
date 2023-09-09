from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove 
from aiogram.utils.callback_data import CallbackData

#                                             GLOBAL
#----------------------------------------------------------------------------------------------------------------
glavnoe_menu_keyboard = InlineKeyboardMarkup()

glavnoe_menu_button = InlineKeyboardButton(text='В главное меню', callback_data='glavnoe_menu')

glavnoe_menu_keyboard.add(glavnoe_menu_button)

#                                             USER
#----------------------------------------------------------------------------------------------------------------
user_keyboard = InlineKeyboardMarkup(row_width=2)

question_button = InlineKeyboardButton(text='Задать вопрос', callback_data='make_question')
instruction_button = InlineKeyboardButton(text='Инструкция по взаимодействию', callback_data='instruction')

user_keyboard.add(question_button, instruction_button)

class Boltun_Step_Back:
    close_status = KeyboardButton("Завершить процесс")
    back_to_menu = KeyboardButton("Вернуться к выбору")
    not_satisfied = KeyboardButton("Меня не устроил ответ")
    failed_to_find = KeyboardButton("Не нашел подходящего вопроса")
    kb_3 = ReplyKeyboardMarkup(resize_keyboard=True).add(close_status, back_to_menu, not_satisfied)
    kb_2 = ReplyKeyboardMarkup(resize_keyboard=True).add(not_satisfied, close_status)
    kb_1 = ReplyKeyboardMarkup(resize_keyboard=True).add(failed_to_find)

class Boltun_Keys:
    cd = CallbackData("bolt_questions", "action")
    
    def get_keyboard(list_of_names, user_id):
        keyboard = InlineKeyboardMarkup(row_width=2)
        key_dict = {}

        for i, var in enumerate(list_of_names):
            key_dict.update([(var, InlineKeyboardButton(text=f"Вопрос №{i + 1}",callback_data=Boltun_Keys.cd.new(f"question_{user_id}_{i}")))])

        keyboard.add(*[value for value in key_dict.values()])

        return keyboard

#                                             MODER
#----------------------------------------------------------------------------------------------------------------
moder_start_keyboard = InlineKeyboardMarkup(row_width=2)
moder_owner_start_keyboard = InlineKeyboardMarkup(row_width=2)

number_of_unanswered_questions = InlineKeyboardButton(text='Ожидают ответа', callback_data='number_unanswered')
answer_the_question = InlineKeyboardButton(text='Ответить на вопрос', callback_data='answer_question')
add_moder = InlineKeyboardButton(text='Добавить модера', callback_data='add_moder')
delete_moder = InlineKeyboardButton(text='Удалить модера', callback_data='delete_moder')

moder_start_keyboard.add(number_of_unanswered_questions, answer_the_question)
moder_owner_start_keyboard.add(number_of_unanswered_questions, answer_the_question, add_moder, delete_moder)

#----------------------------------------------------------------------------------------------------------------
moder_choose_question_keyboard = InlineKeyboardMarkup(row_width=2)

choose_question = InlineKeyboardButton(text='Выбрать вопрос', callback_data='choose_answer')
back = InlineKeyboardButton(text='Назад', callback_data='back')

moder_choose_question_keyboard.add(choose_question, back)