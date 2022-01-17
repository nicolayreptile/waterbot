import asyncio
import re
from typing import Any, Union

import aioredis


class Redis:
    def __init__(self, host='localhost', port=6379, db=1, password=None):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._redis = None
        self._prefix = ('storage', )
        self._loop = asyncio.get_event_loop()
        self._connection_lock = asyncio.Lock()

    async def redis(self) -> aioredis.Redis:
        async with self._connection_lock:
            if self._redis is None or self._redis.closed:
                self._redis = await aioredis.create_redis_pool((self._host, self._port), db=self._db,
                                                               password=self._password, loop=self._loop)
        return self._redis

    def get_key(self, *parts):
        return ':'.join(self._prefix + tuple(map(str, parts)))

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()

    async def set(self, user: int, chat: int, key: Union[str, int], value: Any, expire: int = 0):
        key = self.get_key(user, chat, key)
        redis = await self.redis()
        await redis.set(key, value, expire=expire)

    async def get(self, user: int, chat: int, key: Union[str, int]):
        key = self.get_key(user, chat, key)
        redis = await self.redis()
        value = await redis.get(key, encoding='utf-8')
        if isinstance(value, str) and re.match(r'-?[\d]+', value):
            return int(value)
        return value

    async def delete(self, user: int, chat: int, key: Union[str, int]):
        key = self.get_key(user, chat, key)
        redis = await self.redis()
        await redis.delete(key)
