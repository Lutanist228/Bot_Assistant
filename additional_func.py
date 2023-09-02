from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json

from cache_container import cache

async def create_inline_keyboard(rows):
    questions_keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []

    for row in rows:
        question_id = str(row[0])
        username = row[1]
        question = row[2]
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

    return questions_keyboard