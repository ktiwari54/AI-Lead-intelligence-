"""Embedding generation via OpenAI."""
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import CacheService

logger = get_logger(__name__)
_cache = CacheService(prefix="emb", ttl=86400)


class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        import hashlib
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached = await _cache.get(cache_key)
        if cached:
            return cached
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding
        await _cache.set(cache_key, embedding)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        return [r.embedding for r in sorted(response.data, key=lambda x: x.index)]
