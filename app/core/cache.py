import redis.asyncio as aioredis
from app.core.config import settings

redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

async def get_redis():
    return redis_client

