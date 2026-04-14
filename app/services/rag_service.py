"""
RAG Service — Book-Based Retrieval-Augmented Generation.

Handles:
- PDF text extraction with PyMuPDF
- Text chunking with LangChain text splitters
- Embedding generation with Google's text-embedding-004
- Vector storage & retrieval with Qdrant Cloud

Each session gets its own Qdrant collection: {prefix}_{session_id}
"""
import logging
import io
from typing import List, Dict, Any, Optional
from uuid import UUID

import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for Retrieval-Augmented Generation using Qdrant Cloud.
    
    Manages the full lifecycle:
    1. Upload: PDF → text → chunks → embeddings → Qdrant
    2. Query: user message → embedding → Qdrant search → relevant chunks
    3. Cleanup: delete collection when session is deleted
    """
    
    def __init__(self):
        """Initialize RAG service with Qdrant client and embeddings model."""
        self._client: Optional[QdrantClient] = None
        self._embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    @property
    def client(self) -> QdrantClient:
        """Lazy-initialize Qdrant client."""
        if self._client is None:
            if not settings.QDRANT_URL:
                raise RuntimeError("QDRANT_URL not configured. Set it in .env for RAG mode.")
            
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30,
            )
            logger.info(f"Connected to Qdrant Cloud: {settings.QDRANT_URL}")
        return self._client
    
    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Lazy-initialize Google embeddings model."""
        if self._embeddings is None:
            if not settings.GOOGLE_API_KEY:
                raise RuntimeError("GOOGLE_API_KEY not configured. Required for embeddings.")
            
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            logger.info(f"Initialized embedding model: {settings.EMBEDDING_MODEL}")
        return self._embeddings
    
    def _collection_name(self, session_id: str) -> str:
        """Get Qdrant collection name for a session."""
        # Clean UUID hyphens for valid collection name
        clean_id = str(session_id).replace("-", "")
        return f"{settings.QDRANT_COLLECTION_PREFIX}_{clean_id}"
    
    # =========================================================================
    # UPLOAD & PROCESSING
    # =========================================================================
    
    async def process_upload(
        self,
        session_id: str,
        file_content: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Process an uploaded PDF: extract text, chunk, embed, store in Qdrant.
        
        Args:
            session_id: Session identifier
            file_content: Raw PDF bytes
            filename: Original filename
            
        Returns:
            Dict with metadata (page_count, chunk_count, collection_name)
            
        Raises:
            ValueError: If file is too large or not a valid PDF
        """
        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.RAG_MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large ({file_size_mb:.1f} MB). "
                f"Max allowed: {settings.RAG_MAX_FILE_SIZE_MB} MB."
            )
        
        logger.info(f"Processing PDF upload: {filename} ({file_size_mb:.1f} MB)")
        
        # Step 1: Extract text from PDF
        pages = self._extract_text_from_pdf(file_content)
        total_pages = len(pages)
        
        if total_pages == 0:
            raise ValueError("Could not extract any text from the PDF. The file may be empty or image-based.")
        
        logger.info(f"Extracted text from {total_pages} pages")
        
        # Step 2: Chunk the text with page metadata
        chunks = self._chunk_pages(pages)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Step 3: Generate embeddings
        chunk_texts = [c["text"] for c in chunks]
        
        # Batch embedding to avoid rate limits
        batch_size = 50
        all_embeddings = []
        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i + batch_size]
            batch_embeddings = await self.embeddings.aembed_documents(batch)
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"Generated {len(all_embeddings)} embeddings (dim={len(all_embeddings[0])})")
        
        # Step 4: Create Qdrant collection and upsert
        collection_name = self._collection_name(session_id)
        embedding_dim = len(all_embeddings[0])
        
        # Delete existing collection if any (re-upload case)
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        
        # Create collection
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )
        
        # Upsert points
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            points.append(
                PointStruct(
                    id=idx,
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "page_number": chunk["page_number"],
                        "chunk_index": idx,
                        "source": filename,
                    },
                )
            )
        
        # Batch upsert
        upsert_batch_size = 100
        for i in range(0, len(points), upsert_batch_size):
            batch = points[i:i + upsert_batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch,
            )
        
        logger.info(f"Upserted {len(points)} vectors into collection '{collection_name}'")
        
        return {
            "filename": filename,
            "page_count": total_pages,
            "chunk_count": len(chunks),
            "collection_name": collection_name,
            "file_size_mb": round(file_size_mb, 2),
        }
    
    def _extract_text_from_pdf(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF.
        
        Returns a list of dicts: [{"page_number": 1, "text": "..."},  ...]
        """
        pages = []
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                if text:
                    pages.append({
                        "page_number": page_num + 1,
                        "text": text,
                    })
            doc.close()
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise ValueError(f"Failed to read PDF: {str(e)}")
        
        return pages
    
    def _chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk extracted pages into smaller pieces, preserving page numbers.
        
        Each chunk retains the page_number it originated from. If a page is
        split into multiple chunks, each chunk gets the same page number.
        """
        chunks = []
        for page in pages:
            page_chunks = self._text_splitter.split_text(page["text"])
            for chunk_text in page_chunks:
                chunks.append({
                    "text": chunk_text,
                    "page_number": page["page_number"],
                })
        return chunks
    
    # =========================================================================
    # SEARCH / RETRIEVAL
    # =========================================================================
    
    async def search(
        self,
        session_id: str,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search against the book's vector store.
        
        Args:
            session_id: Session identifier
            query: User's query text
            top_k: Number of results (defaults to settings.RAG_TOP_K)
            
        Returns:
            List of matched chunks with text, page_number, and score
        """
        top_k = top_k or settings.RAG_TOP_K
        collection_name = self._collection_name(session_id)
        
        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)
        
        # Search Qdrant
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
            )
        except Exception as e:
            logger.error(f"Qdrant search error for session {session_id}: {e}")
            return []
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "text": result.payload.get("text", ""),
                "page_number": result.payload.get("page_number", 0),
                "score": round(result.score, 4),
                "source": result.payload.get("source", ""),
            })
        
        logger.info(f"RAG search returned {len(formatted)} results for session {session_id}")
        return formatted
    
    # =========================================================================
    # BOOK OVERVIEW (for plan generation)
    # =========================================================================
    
    async def get_book_overview(
        self,
        session_id: str,
        sample_queries: Optional[List[str]] = None,
    ) -> str:
        """
        Get a structured overview of the book for plan generation.
        
        Searches for TOC, introduction, and chapter headings to give the
        planner LLM an understanding of the book's structure.
        
        Args:
            session_id: Session identifier
            sample_queries: Custom queries to search for
            
        Returns:
            Concatenated text overview of the book
        """
        if sample_queries is None:
            sample_queries = [
                "table of contents",
                "introduction overview",
                "chapter 1",
                "summary conclusion",
                "key concepts fundamentals",
            ]
        
        overview_chunks = []
        seen_texts = set()
        
        for query in sample_queries:
            results = await self.search(session_id, query, top_k=3)
            for result in results:
                text = result["text"]
                if text not in seen_texts:
                    seen_texts.add(text)
                    overview_chunks.append(
                        f"[Page {result['page_number']}]\n{text}"
                    )
        
        return "\n\n---\n\n".join(overview_chunks[:15])  # Cap at 15 unique chunks
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    async def delete_collection(self, session_id: str) -> bool:
        """
        Delete the Qdrant collection for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found or error
        """
        collection_name = self._collection_name(session_id)
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant collection {collection_name}: {e}")
            return False
    
    # =========================================================================
    # HEALTH CHECK
    # =========================================================================
    
    def is_configured(self) -> bool:
        """Check if Qdrant Cloud is configured."""
        return bool(settings.QDRANT_URL and settings.QDRANT_API_KEY)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant Cloud connectivity."""
        if not self.is_configured():
            return {"status": "not_configured", "message": "QDRANT_URL/API_KEY not set"}
        
        try:
            collections = self.client.get_collections()
            return {
                "status": "connected",
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Singleton instance
rag_service = RAGService()
