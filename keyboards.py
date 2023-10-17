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
user_keyboard = InlineKeyboardMarkup(row_width=1)
check_programm_keyboard = InlineKeyboardMarkup(row_width=2)
find_link_keyboard = InlineKeyboardMarkup(row_width=2)
tutor_keyboard = InlineKeyboardMarkup(row_width=2)
registration_keyboard = InlineKeyboardMarkup(row_width=2)

question_button = InlineKeyboardButton(text='Задать вопрос', callback_data='make_question')
check_programm_in_base = InlineKeyboardButton(text='Проверить зачисление', callback_data='check_programm')
user_instruction = InlineKeyboardButton(text='Инструкция для пользователей', callback_data='user_instruction')
program_fio = InlineKeyboardButton(text='Проверить по ФИО', callback_data='program_fio')
program_snils = InlineKeyboardButton(text='Проверить по СНИЛСУ', callback_data='program_snils')
registration_button = InlineKeyboardButton(text='Как регистрироваться в лк Сеченова', callback_data='registration')
lk_using_button = InlineKeyboardButton(text='Как пользоваться лк Сеченова', callback_data='lk_using')
innopolis_button = InlineKeyboardButton(text='Как пользоваться лк Иннополиса', callback_data='innopolis_usage')
get_link = InlineKeyboardButton(text='Получить ссылку на канал', callback_data='get_link')
link_fio = InlineKeyboardButton(text='Найти по ФИО', callback_data='link_fio')
link_snils = InlineKeyboardButton(text='Найти по СНИЛСу', callback_data='link_snils')
suggestion_button = InlineKeyboardButton(text='Предложить улучшение/идею', callback_data='suggestion')
tutor_fio = InlineKeyboardButton(text='Найти по ФИО', callback_data='tutor_fio')
tutor_snils = InlineKeyboardButton(text='Найти по СНИЛСу', callback_data='tutor_snils')
find_tutor = InlineKeyboardButton(text='Найти тьютора', callback_data='find_tutor')
registration_to_project = InlineKeyboardButton(text='Записаться на проект', callback_data='registration_to_project')
registration_fio = InlineKeyboardButton(text='По ФИО', callback_data='registration_fio')
registration_snils = InlineKeyboardButton(text='По СНИЛСу', callback_data='registration_snils')

check_programm_keyboard.add(program_fio, program_snils, 
                            glavnoe_menu_button)
user_keyboard.add(question_button, 
                  get_link, 
                  find_tutor,
                  registration_to_project,
                  lk_using_button,
                  user_instruction, 
                  innopolis_button,
                  registration_button,
                  suggestion_button)
find_link_keyboard.add(link_fio, link_snils,
                       glavnoe_menu_button)
tutor_keyboard.add(tutor_fio, tutor_snils,
                   glavnoe_menu_button)
registration_keyboard.add(registration_fio, registration_snils,
                          glavnoe_menu_button)

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
moder_owner_start_keyboard = InlineKeyboardMarkup(row_width=2)
common_moder_start_keyboard = InlineKeyboardMarkup(row_width=1)
generate_answer_keyboard = InlineKeyboardMarkup(row_width=2)

number_of_unanswered_questions = InlineKeyboardButton(text='Ожидают ответа', callback_data='number_unanswered')
answer_the_question = InlineKeyboardButton(text='Ответить на вопрос', callback_data='answer_question')
add_moder = InlineKeyboardButton(text='Добавить модера', callback_data='add_moder')
delete_moder = InlineKeyboardButton(text='Удалить модера', callback_data='delete_moder')
generate_answer = InlineKeyboardButton(text='Сгенерировать ответ', callback_data='generate_answer')
do_not_generate_answer = InlineKeyboardButton(text='Не генерировать', callback_data='do_not_generate_answer')
upload_database = InlineKeyboardButton(text='Выгрузить базу', callback_data='upload_base')
check_history = InlineKeyboardButton(text='Проверить историю', callback_data='check_history') # остановился здесь
moder_instruction = InlineKeyboardButton(text='Инструкция для модераторов', callback_data='moder_instruction')
unical_users = InlineKeyboardButton(text='Количество уникальных пользователей', callback_data='unical_users')

common_moder_start_keyboard.add(number_of_unanswered_questions, answer_the_question, 
                                moder_instruction, user_instruction)
check_history = InlineKeyboardButton(text='Проверить историю', callback_data='check_history')
make_announcement = InlineKeyboardButton(text='Сделать объявление', callback_data='make_announcement')

moder_owner_start_keyboard.add(number_of_unanswered_questions, answer_the_question, 
                               add_moder, delete_moder, 
                               make_announcement, upload_database,
                               unical_users)
generate_answer_keyboard.add(generate_answer, do_not_generate_answer, 
                             check_history, glavnoe_menu_button)

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

announcement_keyboard = InlineKeyboardMarkup(row_width=2)

private_announcement = InlineKeyboardButton(text='В личные сообщения', callback_data='private_announcement')
supergroup_announcement = InlineKeyboardButton(text='В чате канала', callback_data='supergroup_announcement')
both_announcement = InlineKeyboardButton(text='В ЛС и в чат канала', callback_data='both_announcement')

announcement_keyboard.add(private_announcement, supergroup_announcement,
                          both_announcement)
