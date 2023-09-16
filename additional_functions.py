from cache_container import cache
from keyboards import glavnoe_menu_button

from fuzzywuzzy import fuzz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json
import pandas as pd
import re

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
        4) **kwargs - основа функции, где key - назавние файла, а value - содержимое файла;
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

            if 50 <= current_similarity_rate <= 90:
                inline_questions.append(phrase) 
            elif current_similarity_rate > 90:
                inline_questions.clear()

            if(max_similarity_rate < current_similarity_rate and max_similarity_rate != current_similarity_rate):
                max_similarity_rate = current_similarity_rate
                index = number
    sample = boltun_text_orig[index + 1]

    if max_similarity_rate < 50:
        sample = "Not Found"

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
    path = '/home/admin2/Рабочий стол/Bot for CK/programs_edit_10.xlsx'
    
    programs = pd.read_excel(path, sheet_name='Общая таблица')
    consortium_options = ['Да', 'Соглашение', 'СУ', 'Да?', 'да', 'ДА']
    status_options = ['Добавлена в телеграм', 'Проверена', 'Включена в список на зачисление', 'Сеченовский Университет (регистрация через личный кабинет)']
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
    try:
        return data_to_check[0]
    except IndexError:
        return 'Нет в зачислении'
