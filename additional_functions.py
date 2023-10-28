from cache_container import cache
from keyboards import glavnoe_menu_button
from keyboards import user_keyboard

from fuzzywuzzy import fuzz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
    programs = await cache.get('excel_data')
    enrolled_programs = await cache.get('enrolled_data')
    consortium_options = ['Да', 'Соглашение', 'СУ', 'Да?', 'да', 'ДА', 'да?', 'ДА?']
    status_options = ['Добавлена в телеграм', 'Проверена', 'Включена в список на зачисление', 
                      'Сеченовский Университет (регистрация через личный кабинет)']
    admission_options = ['Специалист по анализу медицинских данных', 'Разработчик VR/AR решений', 'DevOps в медицине', 
                         'Разработчик цифровых медицинских сервисов']
    admission = {'VR Разработчик решений виртуальной и дополненной реальности в медицине': 'VR',
                 'Специалист по анализу медицинских данных': 'Анализ', 'Разработчик цифровых медицинских сервисов': 'Разработка',
                 'DevOps в медицине': 'DevOps'}
    if method_check == 'fio':
        full_name = name.split()
        full_name = [word.capitalize() for word in full_name]
        full_name = ' '.join(full_name)

        data_to_check = programs.loc[(programs['ФИО'] == full_name) &
                                    (programs['Консорциум'].isin(consortium_options)) &
                                    (programs['Статус'].isin(status_options))]['Программа'].tolist()
    elif method_check == 'snils':
        snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')
        if not snils_pattern.match(str(name)):
            # Если ячейка не соответствует формату СНИЛСа, исправьте ее
            cleaned_snils = re.sub(r'\D', '', str(name))  # Удаление всех нецифровых символов
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            name = formatted_snils  # Установка исправленного значения

        # Собираем СНИЛС с разделителями
        data_to_check = programs.loc[(programs['СНИЛС'] == name) &
                                    (programs['Консорциум'].isin(consortium_options)) &
                                    (programs['Статус'].isin(status_options))]['Программа'].tolist()
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
            return found_data[0]
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
    worksheet_list = sheet.worksheets()
    if status == 'ФИО':
        online_table_process()
    elif status == 'СНИЛС':
        online_table_process()
    elif status == 'edit':
        worksheet_for_team = sheet.worksheet('Проекты')
        cell = worksheet_for_team.find(data[0][2])
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.update_cell(row=row, col=17, value=data[0][2])
        worksheet.update_cell(row=row, col=18, value=data[0][1])
        worksheet.update_cell(row=row, col=19, value=role)
    elif status == 'start':
        worksheet = sheet.worksheet('Проекты')
        team = worksheet.col_values(1)
        project = worksheet.col_values(2)
        tags = worksheet.col_values(3)
        return team, project, tags
    
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

