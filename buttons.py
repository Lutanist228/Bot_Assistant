from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove 

def get_start() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))

def get_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Завершить процесс"))

def get_back() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Вернуться к выбору"))
