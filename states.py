from aiogram.dispatcher.filters.state import StatesGroup, State

class User_Panel(StatesGroup):
    making_question = State()
    gpt_question = State()
    check = State()
    boltun_question = State()
    boltun_reply = State()
    boltun_back_to_menu = State()
    fio = State()
    snils = State()
    suggestion = State()

class Moder_Panel(StatesGroup):
    add_moder = State()
    delete_moder = State()
    adding_to_base = State()
    choosing_answer = State()
    waiting_for_answer = State()
    make_announcement = State()
    answer_panel = State()

class Registration(StatesGroup):
    get_tag = State()
    role = State()