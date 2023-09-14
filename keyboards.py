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
check_programm_keyboard = InlineKeyboardMarkup(row_width=2)

question_button = InlineKeyboardButton(text='Задать вопрос', callback_data='make_question')
check_programm_in_base = InlineKeyboardButton(text='Проверить зачисление', callback_data='check_programm')
instruction_button = InlineKeyboardButton(text='Инструкция по взаимодействию', callback_data='instruction')
fio_check = InlineKeyboardButton(text='Проверить по ФИО', callback_data='check_fio')
snils_check = InlineKeyboardButton(text='Проверить по СНИЛСУ', callback_data='check_snils')

check_programm_keyboard.add(fio_check, snils_check, glavnoe_menu_button)
user_keyboard.add(question_button, check_programm_in_base, instruction_button)

class Boltun_Step_Back:
    close_status = KeyboardButton("Завершить процесс")
    back_to_questions = KeyboardButton("Вернуться к выбору")
    not_satisfied = KeyboardButton("Меня не устроил ответ")
    failed_to_find = KeyboardButton("Не нашел подходящего вопроса")
    back_to_menu = KeyboardButton("Вернуться в главное меню")

    kb_choosing_questions = ReplyKeyboardMarkup(resize_keyboard=True).add(close_status, back_to_questions, not_satisfied)
    kb_got_answer = ReplyKeyboardMarkup(resize_keyboard=True).add(not_satisfied, close_status)
    kb_failed_to_find = ReplyKeyboardMarkup(resize_keyboard=True).add(failed_to_find, close_status)
    kb_return_to_start = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu)

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
generate_answer_keyboard = InlineKeyboardMarkup(row_width=2)

number_of_unanswered_questions = InlineKeyboardButton(text='Ожидают ответа', callback_data='number_unanswered')
answer_the_question = InlineKeyboardButton(text='Ответить на вопрос', callback_data='answer_question')
add_moder = InlineKeyboardButton(text='Добавить модера', callback_data='add_moder')
delete_moder = InlineKeyboardButton(text='Удалить модера', callback_data='delete_moder')
generate_answer = InlineKeyboardButton(text='Сгенерировать ответ', callback_data='generate_answer')
do_not_generate_answer = InlineKeyboardButton(text='Не генерировать', callback_data='do_not_generate_answer')
upload_database = InlineKeyboardButton(text='Выгрузить базу', callback_data='upload_base')
check_history = InlineKeyboardButton(text='Проверить историю', callback_data='check_history') # остановился здесь

moder_start_keyboard.add(number_of_unanswered_questions, answer_the_question)
moder_owner_start_keyboard.add(number_of_unanswered_questions, answer_the_question, add_moder, delete_moder, upload_database)
generate_answer_keyboard.add(generate_answer, do_not_generate_answer, check_history, glavnoe_menu_button)

#----------------------------------------------------------------------------------------------------------------
moder_choose_question_keyboard = InlineKeyboardMarkup(row_width=2)

choose_question = InlineKeyboardButton(text='Выбрать вопрос', callback_data='choose_question')
back = InlineKeyboardButton(text='Назад', callback_data='back')
close_question = InlineKeyboardButton(text='Закрыть вопрос', callback_data='close_question')

moder_choose_question_keyboard.add(choose_question, close_question, back)

question_base_keyboard = InlineKeyboardMarkup(row_width=2)

question_yes = InlineKeyboardButton(text='Да', callback_data='add_to_base')
question_no = InlineKeyboardButton(text='Нет', callback_data='do_not_add_to_base')

question_base_keyboard.add(question_yes, question_no)