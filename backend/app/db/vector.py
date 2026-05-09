"""PGVector operations for RAG pipeline."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class VectorStore:
    """PGVector operations for knowledge chunk storage and retrieval."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chunk(
        self,
        knowledge_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> str:
        """Create a knowledge chunk with vector embedding."""
        import uuid
        chunk_id = f"chunk-{uuid.uuid4()}"

        await self.session.execute(
            text("""
                INSERT INTO knowledge_chunks (id, knowledge_id, content, embedding, metadata)
                VALUES (:id, :knowledge_id, :content, (:embedding)::vector, :metadata)
            """),
            {
                "id": chunk_id,
                "knowledge_id": knowledge_id,
                "content": content,
                "embedding": str(embedding),
                "metadata": str(metadata) if metadata else None,
            }
        )
        await self.session.commit()
        return chunk_id

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        org_id: str | None = None,
    ) -> list[dict]:
        """Search for similar knowledge chunks."""
        filter_clause = ""
        if org_id:
            filter_clause = "AND k.org_id = :org_id"

        result = await self.session.execute(
            text(f"""
                SELECT
                    c.id,
                    c.content,
                    c.knowledge_id,
                    c.metadata,
                    1 - (c.embedding <=> (:embedding)::vector) as similarity
                FROM knowledge_chunks c
                JOIN knowledge k ON c.knowledge_id = k.id
                WHERE k.status = 'published'
                {filter_clause}
                ORDER BY c.embedding <=> (:embedding)::vector
                LIMIT :top_k
            """),
            {
                "embedding": str(query_embedding),
                "top_k": top_k,
                "org_id": org_id,
            }
        )

        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "content": row[1],
                "knowledge_id": row[2],
                "metadata": row[3],
                "score": float(row[4]),
            }
            for row in rows
        ]
