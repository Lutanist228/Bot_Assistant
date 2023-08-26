from aiocache import caches, SimpleMemoryCache

# Создаем кэш хранилище
cache = SimpleMemoryCache()
cache_for_buttons = SimpleMemoryCache()

# Настройки хранилища
caches.set_config({
    'default':  {
        'cache': 'aiocache.SimpleMemoryCache',
        'serializer': {
            'class': 'aiocache.serializers.PickleSerializer'
        }
    }
})
