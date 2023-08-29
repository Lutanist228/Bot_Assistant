from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove 

def get_start() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Start"))

def get_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Завершить процесс"))