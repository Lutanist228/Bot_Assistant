from aiogram.dispatcher.filters.state import StatesGroup, State

class User_Panel(StatesGroup):
    waiting_for_answer = State()
    making_question = State()
    choosing_answer = State()
    gpt_question = State()
    check_programm = State()

class Boltun_Module(StatesGroup):
    boltun_question = State()
    boltun_reply = State()
    boltun_back_to_menu = State() 

class Moder_Panel(StatesGroup):
    add_moder = State()
    delete_moder = State()
    adding_to_base = State()
