from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

class Boltun_Keys:
    cd = CallbackData("bolt_questions", "action")
    
    def get_keyboard(list_of_names, user_id):
        keyboard = InlineKeyboardMarkup(row_width=2)
        key_dict = {}

        for i, var in enumerate(list_of_names):
            key_dict.update([(var, InlineKeyboardButton(text=var,callback_data=Boltun_Keys.cd.new(f"question_{user_id}_{i}")))])

        keyboard.add(*[value for value in key_dict.values()])
        return keyboard
