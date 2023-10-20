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
    path_enrolled_table = 'C:\\Users\\derev\\OneDrive\\Рабочий стол\\proga\\Bot_Assistant-2\\enrolled.xlsx'

    enrolled_programs = pd.read_excel(path_enrolled_table, sheet_name=['Анализ', 'Разработка', 'VR', 'DevOps'], skiprows=1)

    await cache.set('enrolled_data', enrolled_programs)