import time
import asyncio
from functools import wraps
from aiogram.utils import exceptions
import random as rm

class Callback_Querry():
    callback_id = 1210
    user_id = 1050

class Message_Querry():
    message_id = 1210
    user_id = 1050

def saving_info(chat, user):
    return [chat, user]

async def chat_add(chat_id):
    chats = range(rm.randrange(1_000, 1_100), rm.randrange(1_100, 1_200))
    for chat in chats:
        if chat == chat_id:
            await asyncio.sleep(2)
            print("Chat found")
            return True
        else:
            await asyncio.sleep(2)
            print("Chat not found")
            return False

async def active_keyboard_status(status:str, user_id:int):
    if user_id == 1854:
        await asyncio.sleep(2)
        print("User_id = 1854")
    elif user_id == 556:
        await asyncio.sleep(4)
        print("User_id = 556")
    return saving_info(chat=status, user=user_id)
    
def quarry_definition_decorator(func):
    """
        Как работает этот декоратор:
        1. С помощью оберточной функции и именованных аргументов, заключенных в **kwargs,
        декоратор вычленяет значение переменных, что представляют собой изменяемые объекты 
        в з-ти от типа запроса: переменная вычисления message_id, переменная вычисления user_id,
        и другие
        2. Внутри декоратора выполняется проверка на тип запроса и только затем 
        вышеуказанные переменные меняются на те, что требует тот или иной тип запроса
        3. После перезаписи возвращается принимаемая функция, но уже с перезаписанными 
        переменными

    """
    @wraps(func) 
    async def async_wrapper(**kwargs):
                if kwargs["query_type"] == Message_Querry:
                    kwargs["chat_id"] = Message_Querry.message_id
                    kwargs["user_id"] = Message_Querry.user_id
                    # kwargs["chat_type"] = Message_Querry.chat.type
                elif kwargs["query_type"] == Callback_Querry:
                    kwargs["chat_id"] = Callback_Querry.callback_id
                    kwargs["user_id"] = Callback_Querry.user_id
                    # kwargs["chat_type"] = Callback_Querry.chat.type

                return await func(**kwargs)  
    return async_wrapper

def user_registration_decorator(func):
    """
    Как работает этот декоратор:
    1. Обертка принимает именованные аргументы, такие, что ответственны за идентификацию пользователей 
    и засчет ветвления делегирует алгоритм в нужное русло.
    2. Принимаемая функция при этом НЕ меняется, а лишь выступает в качестве источника информации,
    а этот декоратор как бы - совокупность замков, ключи к которому - аргументы принимаемой функции.
    """
    async def async_wrapper(**kwargs):
        moder_ids = range(rm.randrange(1_000, 1_100), rm.randrange(1_100, 1_200))
        for id in moder_ids:
            if kwargs["user_id"] == id:
                if id in moder_ids:
                    print("Доступ приоритета Owner")
                    await chat_add(kwargs["chat_id"])
                    return await func(**kwargs)
                else:
                    print("Доступ приоритета Moder")
                    await chat_add(kwargs["chat_id"])
                    return await func(**kwargs)
        try:
            print("Доступ приоритета User")
            bot_answer = chat_add(kwargs["chat_id"])
            await active_keyboard_status(user_id=kwargs["user_id"], 
                                status='active')
            return await func(**kwargs)
        except exceptions.MessageNotModified:
            pass
    return async_wrapper
    
@quarry_definition_decorator # первым идет декоратор заменяющий переменные в з-ти от запроса
@user_registration_decorator # за ним идет декоратор, идентифицирующий пользователя по переменным
async def start(query_type, user_id, chat_id):
    print(query_type, user_id, chat_id, sep="\n\n")
    await asyncio.sleep(2)
    # 1. Должно - поменяться значения переменных 
    # 2. Принимаются новые значения переменных в декоратор регистрации 
    # и только потом производится вход
    print("Start menu")
    k = input()

async def main():
    await start(query_type=Message_Querry, user_id=99999, chat_id=10000)
    
asyncio.run(main())
