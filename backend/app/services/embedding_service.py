"""Embedding service for vector generation."""
from openai import AsyncOpenAI


class EmbeddingService:
    """Generate embeddings using OpenAI or other providers."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = AsyncOpenAI()

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
