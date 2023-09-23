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
    path = '/home/admin2/Рабочий стол/Bot for CK/programs_edit_13.xlsx'
    
    programs = pd.read_excel(path, sheet_name='Общая таблица')

    await cache.set('excel_data', programs)