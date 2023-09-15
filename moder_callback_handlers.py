from main import dp, bot
from aiogram import types
from additional_functions import fuzzy_handler
from additional_functions import create_inline_keyboard, file_reader, save_to_txt
from user_message_handlers import Answer, db, Global_Data_Storage, cache
from keyboards import user_keyboard, moder_start_keyboard, moder_choose_question_keyboard, moder_owner_start_keyboard, glavnoe_menu_keyboard
from keyboards import generate_answer_keyboard, Boltun_Step_Back
from chat_gpt_module import answer_information
from user_message_handlers import BOLTUN_PATTERN

from aiogram.types import InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
import json 
from aiogram.dispatcher.filters import Text

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'instruction':
        # Нужно будет написать инстуркцию
        await callback.message.edit_text('Инструкция:\nИспользуйте кнопку "Задать вопрос", чтобы задать вопрос (пишите только текст, БЕЗ ФОТО и ДОКУМЕНТОВ)\nТакже у вас будут доступны кнопки, чтобы получить ответ от человека либо вернуться в главное меню.', reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'make_question':
        # Обработка нажатия пользователя, чтобы задать вопрос и переход в это состояние
        await callback.message.edit_text('Задайте свой вопрос. Главное меню отменит ваше действие', reply_markup=glavnoe_menu_keyboard)
        await Answer.boltun_question.set()
    elif callback.data == 'number_unanswered':
        # Получение количества вопросов без ответа, мб полезная для кого то функция, просто добавил
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        # Обработка нажатия модера для показа вопросов (Вопрос номер ...). И создание на основе информации из бд клавиатуры для этих вопросов
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()
    elif callback.data == 'add_moder':
        # Добавить модера, надо сделать проверку, что именно айди и имя через пробел и т д
        await callback.message.edit_text('Введите id и имя модератора через пробел.\n Роли: Moder и Owner', reply_markup=glavnoe_menu_keyboard)
        await Answer.add_moder.set()
    elif callback.data == 'delete_moder':
        # Удаление модера
        await callback.message.edit_text('Введите id модера', reply_markup=glavnoe_menu_keyboard)
        await Answer.delete_moder.set()
    elif callback.data =='upload_base':
        pass
    elif callback.data == 'check_programm':
        await Answer.check_programm.set()
        await callback.message.edit_text('Введите свое ФИО, чтобы проверить вашу программу на зачисление', 
                                         reply_markup=glavnoe_menu_keyboard)
        
@dp.callback_query_handler(Text('back'), state=Answer.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возвращения назад
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Answer.choosing_answer.set()

@dp.callback_query_handler(state=Answer.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    # Обработка и вывод информации по клику на определенный вопрос
    if 'question' in callback.data:
        callback_data = callback.data.split(':')[1]
        from additional_functions import cache
        # Получаем информацию по определенному вопросу и выводим
        data = await cache.get(callback_data)
        information = json.loads(data)
        result = ''
        for key, value in information.items():
            result += f'{key}: {value}\n'
            if key == 'question':
                await state.update_data(question=value)
        await state.update_data(question_id=callback_data)
        await callback.message.edit_text(result, reply_markup=moder_choose_question_keyboard)
    # Обработка выбора определенного вопроса
    elif callback.data == 'choose_answer':
        markup = InlineKeyboardMarkup()
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.message.answer('''Напишите свой ответ или скопируйте ответа бота, если считаете его правильным.\nКнопка "Главное меню" вернет в главное меню.''', 
                                      reply_markup=generate_answer_keyboard)
        await Answer.waiting_for_answer.set()

@dp.callback_query_handler(state=Answer.waiting_for_answer)
async def generate_answer(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'generate_answer':
            await callback.message.delete()
            data = await state.get_data()
            question_id = data['question_id']
            question = data['question']
            answer = await answer_information(question=question)
            await db.update_gpt_answer(question_id=question_id, answer=answer)
            await callback.message.answer(f'Сгенерированный ответ:\n{answer}')
    elif callback.data == 'do_not_generate_answer':
        await callback.message.delete()

@dp.callback_query_handler(state=Answer.adding_to_base)
async def process_base_answers(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'add_to_base':
        global BOLTUN_PATTERN
        data = await state.get_data()
        question = data['question']
        answer = data['answer']
        # тут, после успешного ответа на вопрос происходит то, что вопрос и ответ сохраняюся в boltun.txt
        save_to_txt(boltun=f"""u: {question}\n{answer}\n""")
        BOLTUN_PATTERN = file_reader("boltun.txt")
        await state.finish()
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'do_not_add_to_base':
        await state.finish()
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)








