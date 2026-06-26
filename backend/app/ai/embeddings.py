"""
Embedding generation service using OpenAI text-embedding-3-small.

Embeddings enable:
- Semantic search across companies and contacts (find similar leads)
- Recommendation engine ("leads similar to your best customers")
- Duplicate detection (near-duplicate company/contact records)
- Cluster analysis (group leads by semantic similarity)

We use text-embedding-3-small (1536 dims) for cost efficiency.
For higher accuracy, swap to text-embedding-3-large (3072 dims).
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from openai import AsyncOpenAI

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536
CACHE_TTL = 86400 * 7  # 7 days — embeddings are stable


def _get_openai() -> AsyncOpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=False)


def _cache_key(text: str) -> str:
    h = hashlib.sha256(text.encode()).hexdigest()
    return f"embedding:v1:{h}"


async def get_embedding(text: str) -> list[float] | None:
    """
    Get embedding vector for text. Returns None if OpenAI is not configured.
    Caches results in Redis to avoid redundant API calls.
    """
    if not text or not text.strip():
        return None

    client = _get_openai()
    if not client:
        logger.debug("OpenAI not configured, skipping embedding generation")
        return None

    # Check Redis cache first
    try:
        r = await _get_redis()
        cached = await r.get(_cache_key(text))
        if cached:
            return json.loads(cached)
        await r.aclose()
    except Exception:
        pass

    try:
        text_clean = text.strip()[:8191]  # API limit
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text_clean,
            encoding_format="float",
        )
        embedding = response.data[0].embedding

        # Cache the result
        try:
            r = await _get_redis()
            await r.setex(_cache_key(text), CACHE_TTL, json.dumps(embedding))
            await r.aclose()
        except Exception:
            pass

        return embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


async def get_embeddings_batch(texts: list[str]) -> list[list[float] | None]:
    """Batch embedding generation — more efficient than individual calls."""
    if not texts:
        return []

    client = _get_openai()
    if not client:
        return [None] * len(texts)

    # Check cache for each
    results: list[list[float] | None] = [None] * len(texts)
    uncached_indices: list[int] = []
    uncached_texts: list[str] = []

    try:
        r = await _get_redis()
        for i, text in enumerate(texts):
            if text and text.strip():
                cached = await r.get(_cache_key(text))
                if cached:
                    results[i] = json.loads(cached)
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text.strip()[:8191])
        await r.aclose()
    except Exception:
        uncached_indices = list(range(len(texts)))
        uncached_texts = [t.strip()[:8191] for t in texts if t]

    if not uncached_texts:
        return results

    try:
        # OpenAI supports up to 2048 inputs per batch
        for batch_start in range(0, len(uncached_texts), 100):
            batch = uncached_texts[batch_start:batch_start + 100]
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
                encoding_format="float",
            )
            for j, emb_data in enumerate(response.data):
                idx = uncached_indices[batch_start + j]
                results[idx] = emb_data.embedding

        # Cache new results
        try:
            r = await _get_redis()
            for i, text in zip(uncached_indices, uncached_texts):
                if results[i]:
                    await r.setex(_cache_key(text), CACHE_TTL, json.dumps(results[i]))
            await r.aclose()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")

    return results


def company_embedding_text(company: dict) -> str:
    """Build text representation of a company for embedding."""
    parts = [
        company.get("name", ""),
        company.get("industry", ""),
        company.get("description", ""),
        company.get("country", ""),
        " ".join(company.get("technologies", []) or []),
    ]
    return " | ".join(p for p in parts if p)


def contact_embedding_text(contact: dict) -> str:
    """Build text representation of a contact for embedding."""
    parts = [
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
        contact.get("designation", ""),
        contact.get("department", ""),
        contact.get("company_name", ""),
        contact.get("company_industry", ""),
        contact.get("seniority", ""),
    ]
    return " | ".join(p for p in parts if p)


def note_embedding_text(note: dict) -> str:
    """Build text for note embedding."""
    return note.get("content", "")


def search_query_embedding_text(query: str) -> str:
    """Normalize search query for embedding."""
    return query.strip().lower()
