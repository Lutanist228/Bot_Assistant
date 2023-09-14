import openpyxl
import re

def format_excel():
        # Откройте существующий файл Excel
    workbook = openpyxl.load_workbook('C:\\Users\\derev\\OneDrive\\Рабочий стол\\proga\\Bot_Assistant\\test.xlsx')

    # Выберите нужный лист и столбец (например, столбец A)
    worksheet = workbook.active
    column_to_format = worksheet['N']

    # Определите регулярное выражение для формата СНИЛСа
    snils_pattern = re.compile(r'^\d{3}-\d{3}-\d{3} \d{2}$')

    # Пройдитесь по всем ячейкам столбца и проверьте их на соответствие формату СНИЛСа
    for i, cell in enumerate(column_to_format):
        if i == 0:
            continue
        if not snils_pattern.match(str(cell.value)):
            # Если ячейка не соответствует формату СНИЛСа, исправьте ее
            cleaned_snils = re.sub(r'\D', '', str(cell.value))  # Удаление всех нецифровых символов
            formatted_snils = f'{cleaned_snils[:3]}-{cleaned_snils[3:6]}-{cleaned_snils[6:9]} {cleaned_snils[9:11]}'
            cell.value = formatted_snils  # Установка исправленного значения

    # Сохраните изменения в файл
    workbook.save('programs_edit_1.xlsx')

format_excel()