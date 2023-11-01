from cache_container import cache
from keyboards import glavnoe_menu_button
from keyboards import user_keyboard, moder_owner_start_keyboard, common_moder_start_keyboard
from aiogram import Bot
from db_actions import Database

from fuzzywuzzy import fuzz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import json
import re
import pandas as pd
import gspread
from functools import wraps
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
import asyncio

def file_reader(file_path: str):
    with open(file=file_path, mode='r', buffering=-1, encoding="utf-8") as file:
        pattern_text = file.readlines()
        return pattern_text
        
def save_to_txt(file_path: str = "", print_as_finished = True, save_mode: str = "a", **kwargs):
        
        r"""Функция save_to_txt принимает в себя:
        1) file_path - путь к файлу в формате: C:\Users\user\*file_dir*\. в случае, если нет необходимости 
        сохранять файл в конкретную директорию, то файл сохраняется в директорию скрипта с save_to_txt;
        2) print_as_finished - флаг, который контролирует вывод надписи The information has been added to the {file_name}.txt file.;
        3) save_mode - формат работы с .txt файлом, по умолчанию - 'a';
        4) **kwargs - основа функции, где key - название файла, а value - содержимое файла;
        """
        for key, value in kwargs.items():
            file_name = key
            with open(rf"{file_path}{file_name}.txt", mode=save_mode, buffering=-1, encoding="utf-8") as file:
                if isinstance(value, (tuple, list)):
                    [file.write(val) for val in value]
                else:
                    file.write(str(value))
            if print_as_finished == True:
                print("\n")
                print(f"The information has been added to the {file_name}.txt file.")
        
def fuzzy_handler(boltun_text: list, user_question: str):
    boltun_text_orig = boltun_text.copy()
    boltun_text = list(map(lambda x: x.lower(), boltun_text))

    user_question = user_question.lower().strip()
    current_similarity_rate = 0
    index = 0
    max_similarity_rate = 0
    inline_questions = []
    for number, phrase in enumerate(boltun_text):
        if('u: ' in phrase):
            phrase = phrase.replace('u: ','')
            current_similarity_rate = (fuzz.token_sort_ratio(phrase, user_question))

            if 50 <= current_similarity_rate <= 85:
                inline_questions.append(phrase) 
            elif current_similarity_rate > 85:
                inline_questions.clear()

            if(max_similarity_rate < current_similarity_rate and max_similarity_rate != current_similarity_rate):
                max_similarity_rate = current_similarity_rate
                index = number
    sample = boltun_text_orig[index + 1]

    if max_similarity_rate < 50:
        sample = "Not Found"
    if max_similarity_rate == 100:
        text = "" ; num = 0 ; sample = []
        while "u:" not in text:
            num += 1
            text = boltun_text_orig[index + num]
            sample.append(text)
        sample.pop()
        sample = ''.join(sample)
    return sample, max_similarity_rate, inline_questions     

async def create_inline_keyboard(rows):
    questions_keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []

    for row in rows:
        question_id = str(row[0])
        username = row[2]
        question = row[4]
        data = {'username': username,
                'question': question}
        if row[14] is not None:
            data['picture'] = row[14]
        # Переводим данные в json формат
        serialized_data = json.dumps(data)
        # Сохраняем в кэш память
        await cache.set(question_id, serialized_data)
        button = InlineKeyboardButton(text=f'Вопрос {question_id}', callback_data=f'question:{question_id}')
        
        buttons.append(button)
    # Разбиваем на столбцы
    button_lists = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]

    for button_list in button_lists:
        questions_keyboard.add(*button_list)
    questions_keyboard.add(glavnoe_menu_button)
    return questions_keyboard

async def check_program(name: str, method_check: str):
    enrolled_programs = await cache.get('enrolled_data')
    consortium_options = ['Да', 'Соглашение', 'СУ', 'Да?', 'да', 'ДА', 'да?', 'ДА?']
    status_options = ['Добавлена в телеграм', 'Проверена', 'Включена в список на зачисление', 
                      'Сеченовский Университет (регистрация через личный кабинет)']
    admission_options = ['Специалист по анализу медицинских данных', 'Разработчик VR/AR решений', 'DevOps в медицине', 
                         'Разработчик цифровых медицинских сервисов']
    admission = {'VR Разработчик решений виртуальной и дополненной реальности в медицине': 'VR',
                 'Специалист по анализу медицинских данных': 'Анализ', 'Разработчик цифровых медицинских сервисов': 'Разработка',
                 'DevOps в медицине': 'DevOps'}
    if method_check == 'enroll_fio':
        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['ФИО'].str.lower() == name.lower()]['ФИО'].tolist()
            if len(data) == 0:
                continue
            else:
                data.append(sheet_name)
                found_data = data
    elif method_check == 'enroll_snils':
        snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')
        if not snils_pattern.match(str(name)):
            cleaned_snils = re.sub(r'\D', '', str(name))
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            name = formatted_snils

        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['СНИЛС'].str.lower() == name.lower()]['ФИО'].tolist()
            if len(data) == 0:
                continue
            else:
                data.append(sheet_name)
                found_data = data
    elif method_check == 'link_fio':
        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['ФИО'].str.lower() == name.lower()]['ДПП'].tolist()
            if len(data) == 0:
                continue
            else:
                found_data = data

    elif method_check == 'link_snils':
        snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')
        if not snils_pattern.match(str(name)):
            cleaned_snils = re.sub(r'\D', '', str(name))
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            name = formatted_snils

        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['СНИЛС'].str.lower() == name.lower()]['ДПП'].tolist()
            if len(data) == 0:
                continue
            else:
                found_data = data

    elif method_check == 'tutor_fio':
        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['ФИО'].str.lower() == name.lower()]['Тьютор'].tolist()
            if len(data) == 0:
                continue
            else:
                found_data = data

    elif method_check == 'tutor_snils':
        snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')
        if not snils_pattern.match(str(name)):
            cleaned_snils = re.sub(r'\D', '', str(name))
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            name = formatted_snils

        for sheet_name in enrolled_programs:
            sheet = enrolled_programs[sheet_name]
            data = sheet.loc[sheet['СНИЛС'].str.lower() == name.lower()]['Тьютор'].tolist()
            if len(data) == 0:
                continue
            else:
                found_data = data
    
    elif method_check == 'registration_fio':
        found_data = await process_connection_to_excel(status='ФИО', data_to_find=name)
        if found_data:
            return found_data
        
    elif method_check == 'registration_snils':
        snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')
        if not snils_pattern.match(str(name)):
            cleaned_snils = re.sub(r'\D', '', str(name))
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            name = formatted_snils

        found_data = await process_connection_to_excel(status='СНИЛС', data_to_find=name)
        if found_data:
            return found_data

    try:
        if found_data is None:
            return 'Нет в зачислении'
        elif pd.isna(found_data[0]):
            return 'Нет в зачислении'
        else:
            return found_data
    except (IndexError, UnboundLocalError):
        return 'Нет в зачислении'
    
async def process_connection_to_excel(status: str, row: int = None, worksheet_name: str = None, data: list = None, role:str = None, data_to_find = None):

    def online_table_process():
        for index in range(4):
            worksheet = sheet.worksheet(worksheet_list[index].title)
            cell = worksheet.find(data_to_find, case_sensitive=False)
            if cell:
                result = ['found', cell.row, worksheet_list[index].title]
                return result

    from config_file import SERVICE_ACCOUNT_PATH, EXCEL_TABLE_PATH

    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_PATH)
    except FileNotFoundError:
        gc = gspread.service_account(filename=r"C:\Users\user\Desktop\IT-Project\Bots\Bot_Assistant\other_file\files_for_server\google_key.json")
    sheet = gc.open_by_url(EXCEL_TABLE_PATH)
    # Берем все названия листов таблицы
    worksheet_list = sheet.worksheets()
    if status == 'ФИО':
        online_table_process()
    elif status == 'СНИЛС':
        online_table_process()
    elif status == 'edit':
        # worksheet_for_team = sheet.worksheet('Проекты')
        # cell = worksheet_for_team.find(data[0][2])
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.update_cell(row=row, col=17, value=data[0][2])
        worksheet.update_cell(row=row, col=18, value=data[0][1])
        worksheet.update_cell(row=row, col=19, value=role)
    elif status == 'start':
        # Получаем три столбца для сохранения в бд при запуске
        worksheet = sheet.worksheet('Проекты')
        team = worksheet.col_values(1)
        project = worksheet.col_values(2)
        tags = worksheet.col_values(3)
        acception = worksheet.col_values(6)
        return team, project, tags, acception
    
def execution_count_decorator(func):
    """
    Как работает этот декоратор:
    1. Декоратор отсчитывает вызов той или иной функции при аварийном режиме,
    т.е. тогда, когда срабатывает то или иное исключение.
    2. Он меняет изменяет аргемент до тех пор, пока алгоритм не выйдет из
    аварийной ситуации
    """
    async_wrapper_counter = 0
    async def async_wrapper(*args, **kwargs):
        nonlocal async_wrapper_counter
        if kwargs["exeption_raised"] == True:
            async_wrapper_counter += 1
            kwargs["iter_num"] -= async_wrapper_counter
        return await func(*args, **kwargs)
    return async_wrapper

def quarry_definition_decorator(func):
    """
        Как работает этот декоратор:
        1. С помощью оберточной функции и именованных аргументов, заключенных в **kwargs,
        декоратор вычленяет значение переменных, что представляют собой изменяемые объекты 
        в з-ти от типа запроса: переменная вычисления message_id, переменная вычисления user_id,
        и другие;
        2. Внутри декоратора выполняется проверка на тип запроса и только затем 
        вышеуказанные переменные меняются на те, что требует тот или иной тип запроса;
        3. После перезаписи возвращается принимаемая функция, но уже с перезаписанными 
        переменными;
    """
    @wraps(func) 
    async def async_wrapper(quarry_type, state, **kwargs):             
                if isinstance(quarry_type, types.Message) == True:
                    kwargs.update({
                        "chat_id": quarry_type.chat.id,
                        "user_id": quarry_type.from_user.id,
                        "chat_type": quarry_type.chat.type,
                        "answer_type": quarry_type,
                        "message_id": quarry_type.message_id,
                        "edit_text": None
                        })
                elif isinstance(quarry_type, types.CallbackQuery) == True:
                    kwargs.update({
                        "chat_id": quarry_type.message.chat.id,
                        "user_id": quarry_type.from_user.id,
                        "chat_type": quarry_type.message.chat.type,
                        "answer_type": quarry_type.message,
                        "message_id": quarry_type.message.message_id,
                        "edit_text": quarry_type.message.edit_text
                        })
                return await func(**kwargs) 
    return async_wrapper    

def user_registration_decorator(func):
    """
    Как работает этот декоратор:
    1. Обертка принимает именованные аргументы, такие, что ответственны за идентификацию пользователей 
    и засчет ветвления делегирует алгоритм в нужное русло - т.е. распределяет модеров и юзеров по уровню доступа;
    2. Принимаемая функция при этом НЕ меняется, а лишь выступает в качестве источника информации,
    а этот декоратор как бы - совокупность замков, ключи к которому - аргументы принимаемой функции;
    """
    async def async_wrapper(quarry_type, state, *args):
        @quarry_definition_decorator
        async def registration(chat_id, user_id, chat_type, answer_type, message_id, edit_text):
            from config_file import OLD_API_TOKEN

            async def back_to_menu(key_type):
                if isinstance(quarry_type, types.Message) == True:
                    await answer_type.answer("Возврат в меню бота...", reply_markup=ReplyKeyboardRemove())
                    return await Bot(OLD_API_TOKEN).send_message(chat_id=chat_id, text='Можем приступить к работе', reply_markup=key_type)
                else:
                    return await edit_text(text='Можем приступить к работе', reply_markup=key_type)

            await state.finish()
            moder_ids = await Database().get_moder()

            for id in moder_ids:
                if user_id == id[0]:
                    if id[1] == 'Owner':
                        await back_to_menu(moder_owner_start_keyboard) 
                        return await func(quarry_type, state)
                    else:
                        await back_to_menu(common_moder_start_keyboard)
                        return await func(quarry_type, state)
            try:
                bot_answer = await back_to_menu(user_keyboard)
                # тут нужно проверять работу active_keyboard_status
                await active_keyboard_status(user_id=user_id, 
                                    message_id=bot_answer.message_id, 
                                    status='active')
                return await func(quarry_type, state)
            except exceptions.MessageNotModified:
                pass
        return await registration(quarry_type, state)
    return async_wrapper       

async def active_keyboard_status(user_id: int, message_id: int, status: str):
    from config_file import OLD_API_TOKEN
    # Получаем айди пользователя, айди сообщения, в котором хранится активная клавиатура. Создание пустой Inline клавиатуры
    markup = InlineKeyboardMarkup()
    # Создание кеш-хранилища под айди пользователя, где будут хранится все сообщения с клавами. Удаления этого хранилища еще
    info = await cache.get(user_id)
    await cache.delete(user_id)
    # Прохождение по словарю с сообщениями и состояниями. Перевод всех сообщений до нового в неактивное состояние и редактировние клавы
    if info:
        for key, value in info.items():
            if value == 'not active':
                continue
            elif value == 'active' and status == 'not active':
                info[key] = status
            elif value == 'active' and message_id != key:
                value = 'not active'
                info[key] = value
                try:
                    await Bot(OLD_API_TOKEN).edit_message_reply_markup(chat_id=user_id, 
                                                        message_id=key,
                                                        reply_markup=markup)
                except (exceptions.MessageToEditNotFound, exceptions.MessageNotModified):
                    pass
        # Добавление нового сообщения со статусом
        info[message_id] = status
        await cache.set(user_id, info)
    else:
        info = {}
        info[message_id] = status
        await cache.set(user_id, info)
        # Очистка кеш хранилища через час, чтобы не нагружать сервак. По идее должно все работать
        # await asyncio.sleep(3600)
        # await cache.delete(user_id)

async def process_timeout(time_for_sleep: int, chat_id: int, chat_type: str, message_id: int = None, state: FSMContext = None):
    from config_file import OLD_API_TOKEN
    if chat_type == 'private':
        # Таймаут на задачу вопроса и возврат пользователя если он так и не задал вопрос (проверяет по измению состояния)
        await asyncio.sleep(time_for_sleep)
        if await state.get_state() == 'User_Panel:boltun_question':
            await state.finish()
            bot_answer = await Bot(OLD_API_TOKEN).send_message(chat_id=chat_id, 
                                text='Вы превысили время на вопрос. Возвращаю вас обратно в меню',
                                reply_markup=user_keyboard)
            await active_keyboard_status(user_id=chat_id, 
                message_id=bot_answer.message_id, 
                status='active')
        else:
            return
    elif chat_type == 'supergroup':
        await asyncio.sleep(time_for_sleep)
        await Bot(OLD_API_TOKEN).delete_message(chat_id=chat_id,
                                 message_id=message_id)
