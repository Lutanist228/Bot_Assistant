from aiocache import caches, SimpleMemoryCache
import pandas as pd

# Создаем кэш хранилище
cache = SimpleMemoryCache()

# Настройки хранилища
caches.set_config({
    'default':  {
        'cache': 'aiocache.SimpleMemoryCache',
        'serializer': {
            'class': 'aiocache.serializers.PickleSerializer'
        }
    }
})

async def excel_data():
    path = 'C:\\Users\\derev\\OneDrive\\Рабочий стол\\proga\\Bot_Assistant-1\\programs_edit_13.xlsx'
    
    programs = pd.read_excel(path, sheet_name='Общая таблица')

    await cache.set('excel_data', programs)