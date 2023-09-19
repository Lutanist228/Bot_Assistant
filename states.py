from aiogram.dispatcher.filters.state import StatesGroup, State

class User_Panel(StatesGroup):
    making_question = State()
    gpt_question = State()
    check_programm = State()
    check_fio = State()
    check_snils = State()
    boltun_question = State()
    boltun_reply = State()
    boltun_back_to_menu = State() 

class Moder_Panel(StatesGroup):
    add_moder = State()
    delete_moder = State()
    adding_to_base = State()
    choosing_answer = State()
    waiting_for_answer = State()
    make_announcement = State()

