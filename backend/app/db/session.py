from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis.asyncio import Redis
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
