from together import Together
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional, Literal
import uuid
from app.config import get_settings

settings = get_settings()

COLLECTION_NAME = "luminaiq_documents"


class RAGService:
    def __init__(self):
        self.together_client = Together(api_key=settings.together_api_key)
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
        )
        self.embedding_model = settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists in Qdrant with proper indexes"""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            # Create payload indexes for filtering
            self.qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            self.qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="book_id",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            self.qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="chapter_id",
                field_schema=models.PayloadSchemaType.INTEGER
            )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        response = self.together_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        response = self.together_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks

    def store_document(
        self,
        user_id: int,
        book_id: int,
        chapter_id: int,
        chapter_title: str,
        content: str,
        chunk_size: int = 500
    ) -> int:
        """Store document chunks in Qdrant with metadata"""
        chunks = self.chunk_text(content, chunk_size=chunk_size)
        
        if not chunks:
            return 0

        embeddings = self.get_embeddings_batch(chunks)
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "chapter_title": chapter_title,
                    "chunk_index": i,
                    "content": chunk
                }
            ))
        
        self.qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        return len(points)

    def retrieve(
        self,
        query: str,
        user_id: int,
        book_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        retrieval_type: Literal["similarity", "mmr", "hybrid"] = "similarity",
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant documents using different techniques:
        - similarity: Standard cosine similarity search
        - mmr: Maximal Marginal Relevance for diversity
        - hybrid: Combines multiple retrieval strategies
        """
        query_embedding = self.get_embedding(query)
        
        # Build filter conditions
        filter_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            )
        ]
        
        if book_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="book_id",
                    match=models.MatchValue(value=book_id)
                )
            )
        
        if chapter_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="chapter_id",
                    match=models.MatchValue(value=chapter_id)
                )
            )
        
        query_filter = models.Filter(must=filter_conditions)
        
        if retrieval_type == "similarity":
            return self._similarity_search(query_embedding, query_filter, top_k)
        elif retrieval_type == "mmr":
            return self._mmr_search(query_embedding, query_filter, top_k)
        else:  # hybrid
            return self._hybrid_search(query, query_embedding, query_filter, top_k)

    def _similarity_search(
        self,
        query_embedding: List[float],
        query_filter: models.Filter,
        top_k: int
    ) -> List[Dict]:
        """Standard similarity search"""
        results = self.qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k
        )
        
        return [
            {
                "content": hit.payload["content"],
                "chapter_title": hit.payload["chapter_title"],
                "chapter_id": hit.payload["chapter_id"],
                "score": hit.score
            }
            for hit in results.points
        ]

    def _mmr_search(
        self,
        query_embedding: List[float],
        query_filter: models.Filter,
        top_k: int,
        diversity: float = 0.3
    ) -> List[Dict]:
        """Maximal Marginal Relevance search for diverse results"""
        # Fetch more candidates for MMR
        results = self.qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k * 3
        )
        candidates = results.points
        
        if not candidates:
            return []
        
        selected = []
        selected_embeddings = []
        remaining = list(candidates)
        
        # Select first result (most relevant)
        first = remaining.pop(0)
        selected.append(first)
        selected_embeddings.append(first.vector if hasattr(first, 'vector') else query_embedding)
        
        # Select remaining results using MMR
        while len(selected) < top_k and remaining:
            best_score = -float('inf')
            best_idx = 0
            
            for idx, candidate in enumerate(remaining):
                relevance = candidate.score
                
                # Calculate max similarity to already selected items
                max_sim = 0
                for sel_emb in selected_embeddings:
                    sim = self._cosine_similarity(
                        candidate.vector if hasattr(candidate, 'vector') else query_embedding,
                        sel_emb
                    )
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr_score = (1 - diversity) * relevance - diversity * max_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            
            best = remaining.pop(best_idx)
            selected.append(best)
            selected_embeddings.append(best.vector if hasattr(best, 'vector') else query_embedding)
        
        return [
            {
                "content": hit.payload["content"],
                "chapter_title": hit.payload["chapter_title"],
                "chapter_id": hit.payload["chapter_id"],
                "score": hit.score
            }
            for hit in selected
        ]

    def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        query_filter: models.Filter,
        top_k: int
    ) -> List[Dict]:
        """Hybrid search combining semantic and keyword matching"""
        # Semantic search results
        results = self.qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k * 2
        )
        semantic_results = results.points
        
        # Score based on keyword matching
        query_words = set(query.lower().split())
        scored_results = []
        
        for hit in semantic_results:
            content = hit.payload["content"].lower()
            content_words = set(content.split())
            
            # Calculate keyword overlap
            keyword_score = len(query_words & content_words) / max(len(query_words), 1)
            
            # Combine scores (weighted average)
            combined_score = 0.7 * hit.score + 0.3 * keyword_score
            
            scored_results.append({
                "content": hit.payload["content"],
                "chapter_title": hit.payload["chapter_title"],
                "chapter_id": hit.payload["chapter_id"],
                "score": combined_score
            })
        
        # Sort by combined score and return top_k
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def delete_user_documents(self, user_id: int):
        """Delete all documents for a user"""
        self.qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                )
            )
        )

    def delete_book_documents(self, user_id: int, book_id: int):
        """Delete all documents for a specific book"""
        self.qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        ),
                        models.FieldCondition(
                            key="book_id",
                            match=models.MatchValue(value=book_id)
                        )
                    ]
                )
            )
        )
