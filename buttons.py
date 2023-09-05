from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove 

def get_start() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))

class Step_Back:
    close_status = KeyboardButton("Завершить процесс")
    back_to_menu = KeyboardButton("Вернуться к выбору")
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(close_status, back_to_menu)

