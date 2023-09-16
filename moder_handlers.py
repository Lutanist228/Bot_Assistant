from aiogram import types
from aiogram.dispatcher import FSMContext
import json
from aiogram.types import InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text

from main import dp, bot, db
from keyboards import Boltun_Step_Back, moder_owner_start_keyboard, question_base_keyboard, moder_start_keyboard
from keyboards import glavnoe_menu_keyboard, generate_answer_keyboard, moder_choose_question_keyboard
from states import Moder_Panel
from additional_functions import create_inline_keyboard, file_reader, save_to_txt
from chat_gpt_module import answer_information


#____________________________MESSAGE__HANDLERS_______________________________________________________________________________

@dp.message_handler(commands=['start'])
async def process_start_message(message: types.Message):
    if message.chat.type == 'private':
    # Достаем айдишники модеров, чтобы проверить пользователя кем он является
        moder_ids = await db.get_moder()
        for id in moder_ids:
            if message.from_user.id == id[0]:
                # Проверка на админа, чтобы добавлять модеров и т д. А то они намудряд и добавят всякой фигни
                if id[1] == 'Owner':
                    await message.answer('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
                else:
                    await message.answer('Можем приступить к работе', reply_markup=moder_start_keyboard)
                return
            
@dp.message_handler(state=Moder_Panel.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    # Получаем айди и имя модера, чтобы сохранить в бд
    moder_id = message.from_user.id
    moder_name = message.from_user.full_name
    # Достаем айди вопроса, в котором должны обновить информацию/ответ
    data = await state.get_data()
    question_id = data.get('question_id')
    # Из бд получаем айди пользователя, чтобы отправить ему ответ
    user_id = await db.get_user_id(question_id)
    # Получаем айди сообщения, чтобы наглядно было видно на какое отвечаем
    message_id = await db.get_message_id(question_id)
    # Получаем вид чата и его айди, чтобы отвечать в больших чатах
    chat_type, chat_id = await db.get_chat_type_and_id(question_id)
    question = await db.get_question(question_id=question_id)
    await db.update_question_id(question_id, message.text, moder_id, moder_name)
    await message.reply('Ответ отправлен')
    if chat_type == 'supergroup':
        await bot.send_message(chat_id=chat_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id)
        await state.finish()
    else:
        await bot.send_message(chat_id=user_id, text=f'Ответ: \n{message.text}', reply_to_message_id=message_id, reply_markup=Boltun_Step_Back.kb_return_to_start)
        await state.finish()
        # Блок по добавлению в базу ответов
    await message.answer('Внести его в базу данных вопросов?', reply_markup=question_base_keyboard)
    await Moder_Panel.adding_to_base.set()
    await state.update_data(question=question.get('question'), answer=message.text)

@dp.message_handler(state=Moder_Panel.add_moder)
async def process_adding_moder(message: types.Message, state: FSMContext):
    # Обработка добавления модера, получаем айди и имя, завершаем состояние и т д
    moder_id = message.text.split()[0]
    moder_name = message.text.split()[1]
    moder_role = message.text.split()[2]
    await state.finish()
    await db.add_new_moder(moder_id=moder_id, moder_name=moder_name, role=moder_role)
    await message.answer('Модер добавлен', reply_markup=moder_owner_start_keyboard)

@dp.message_handler(state=Moder_Panel.delete_moder)
async def process_deleting_moder(message: types.Message, state: FSMContext):
    # Тоже самое, что и с добавлением
    await db.delete_moder(message.text)
    await state.finish()
    await message.answer('Модер удален', reply_markup=moder_owner_start_keyboard)

#____________________________MESSAGE__HANDLERS_______________________________________________________________________________

#____________________________CALLBACK_HANDLERS__________________________________________________________________________________

@dp.callback_query_handler()
async def callback_process(callback: types.CallbackQuery):
    if callback.data == 'instruction':
        # Нужно будет написать инстуркцию
        await callback.message.edit_text('Инструкция:\nИспользуйте кнопку "Задать вопрос", чтобы задать вопрос (пишите только текст, БЕЗ ФОТО и ДОКУМЕНТОВ)\nТакже у вас будут доступны кнопки, чтобы получить ответ от человека либо вернуться в главное меню.', reply_markup=glavnoe_menu_keyboard)
    elif callback.data == 'number_unanswered':
        # Получение количества вопросов без ответа, мб полезная для кого то функция, просто добавил
        number = await db.get_number_of_unanswered_questions()
        await callback.message.answer(f'Количество вопросов без ответа: {number}')
    elif callback.data == 'answer_question':
        # Обработка нажатия модера для показа вопросов (Вопрос номер ...). И создание на основе информации из бд клавиатуры для этих вопросов
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Moder_Panel.choosing_answer.set()
    elif callback.data == 'add_moder':
        # Добавить модера, надо сделать проверку, что именно айди и имя через пробел и т д
        await callback.message.edit_text('Введите id и имя модератора через пробел.\n Роли: Moder и Owner', reply_markup=glavnoe_menu_keyboard)
        await Moder_Panel.add_moder.set()
    elif callback.data == 'delete_moder':
        # Удаление модера
        await callback.message.edit_text('Введите id модера', reply_markup=glavnoe_menu_keyboard)
        await Moder_Panel.delete_moder.set()
    elif callback.data =='upload_base':
        pass
        
@dp.callback_query_handler(Text('back'), state=Moder_Panel.choosing_answer)
async def back_process(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возвращения назад
    if callback.data == 'back':
        await state.finish()
        result = await db.get_list_of_unaswered_questions()
        keyboard = await create_inline_keyboard(result)
        await callback.message.edit_text('Просмотрите и выберите вопрос', reply_markup=keyboard)
        await Moder_Panel.choosing_answer.set()

@dp.callback_query_handler(state=Moder_Panel.choosing_answer)
async def process_choosing_answer(callback: types.CallbackQuery, state: FSMContext):
    # Обработка и вывод информации по клику на определенный вопрос
    if 'question:' in callback.data:
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
    elif callback.data == 'choose_question':
        markup = InlineKeyboardMarkup()
        data = await state.get_data()
        question_id = data['question_id']
        moder_id = callback.from_user.id
        moder_name = callback.from_user.full_name
        result_check = await db.check_question(question_id=question_id)
        if result_check[0] == 'Вопрос взят':
            await callback.message.edit_text('Выбери другой вопрос', reply_markup=glavnoe_menu_keyboard)
        else:
            await db.update_question_id(question_id=question_id, 
                    answer='Вопрос взят', 
                    moder_id=moder_id,
                    moder_name=moder_name)
            await callback.message.edit_reply_markup(reply_markup=markup)
            await callback.message.answer('''Напишите свой ответ или скопируйте ответа бота, если считаете его правильным.\nКнопка "Главное меню" вернет в главное меню.''', 
                                            reply_markup=generate_answer_keyboard)
            await Moder_Panel.waiting_for_answer.set()
    elif callback.data == 'close_question':
        data = await state.get_data()
        question_id = data['question_id']
        moder_id = callback.from_user.id
        moder_name = callback.from_user.full_name
        await db.update_question_id(question_id=question_id, 
                                    answer='Закрытие вопроса', 
                                    moder_id=moder_id,
                                    moder_name=moder_name)
        await callback.message.edit_text('Вернитесь в главное меню', reply_markup=glavnoe_menu_keyboard)

@dp.callback_query_handler(state=Moder_Panel.waiting_for_answer)
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
    elif callback.data == 'check_history':
        data = await state.get_data()
        question_id = data['question_id']
        user_id = await db.get_user_id(question_id=question_id)
        questions = await db.check_history(user_id=user_id)
        history = ''
        for question in questions:
            if question[6] == 'Вопрос взят':
                continue
            history += f'Вопрос: {question[4]}\nОтвет: {question[6]}\n\n'
        await callback.message.edit_text(f'{history} Введите свой ответ или вернитесь в главное меню', 
                                         reply_markup=glavnoe_menu_keyboard)

@dp.callback_query_handler(state=Moder_Panel.adding_to_base)
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

@dp.callback_query_handler(Text('glavnoe_menu'), state='*')
async def process_glavnoe_menu(callback: types.CallbackQuery, state: FSMContext):
    # Обработка возврата в главное меню для всех
    user_id = callback.from_user.id
    moder_ids = await db.get_moder()
    await state.finish()
    for id in moder_ids:
        if user_id == id[0]:
            if id[1] == 'Owner':
                await callback.message.edit_text('Можем приступить к работе', reply_markup=moder_owner_start_keyboard)
            else:
                await callback.message.edit_text('Можем приступить к работе', reply_markup=moder_start_keyboard)
            return

#____________________________CALLBACK_HANDLERS__________________________________________________________________________________




