
# КОД ДЛЯ ПРОВЕРКИ ЗАРЕГИСТРИРОВАННЫХ НА ПРОГРАММЫ ЦК 
# @dp.message_handler(state=User_Panel.check_fio)
# async def checking_fio(message: types.Message, state: FSMContext):
#     name = message.text.strip()
#     result = await check_program(name, method_check='fio')
#     if result == 'Нет в зачислении':
#         bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                     message_id=bot_answer_1.message_id, 
#                     status='active')
#     else:
#         bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await db.add_checked_id(user_id=message.from_user.id,
#                                 user_name=message.from_user.full_name)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                         message_id=bot_answer_2.message_id, 
#                         status='active')
#     await state.finish()

# @dp.message_handler(state=User_Panel.check_snils)
# async def process_check_programm(message: types.Message, state: FSMContext):
#     name = message.text.strip()
#     result = await check_program(name, method_check='snils')
#     if result == 'Нет в зачислении':
#         bot_answer_1 = await message.answer('Вас нет в списке на зачисление, если это ошибка, то сообщите тьютору или задайте вопрос в главном меню', reply_markup=user_keyboard)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                     message_id=bot_answer_1.message_id, 
#                     status='active')
#     else:
#         bot_answer_2 = await message.answer(f'Ваша программа зачисления:\n"{result}"\n', reply_markup=user_keyboard)
#         await db.add_checked_id(user_id=message.from_user.id,
#                             user_name=message.from_user.full_name)
#         await active_keyboard_status(user_id=message.from_user.id, 
#                         message_id=bot_answer_2.message_id, 
#                         status='active')
#     await state.finish()


# ОБРАБОТЧИК В СЛУЧАЕ БЛОКИРОВКИ БОТА 
# @dp.errors_handler(exception=TelegramAPIError)
# async def process_errors(update: types.Update, exception: exceptions):
#     if isinstance(exception, exceptions.BotBlocked):
#         await update.message.answer('Пользователь заблокировал бота,\nВернитесь в главное меню', 
#                                     reply_markup=glavnoe_menu_keyboard)

