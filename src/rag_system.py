"""
RAG (Retrieval-Augmented Generation) system with vector database
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from loguru import logger
from .document_loader import DocumentChunk


class VectorStore:
    """Vector database for document embeddings and retrieval"""
    
    def __init__(
        self,
        db_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "documents"
    ):
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Initialized vector store at {db_path}")
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to vector database
        
        Args:
            chunks: List of document chunks to add
        """
        if not chunks:
            logger.warning("No chunks to add to vector store")
            return
        
        # Prepare data
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                **chunk.metadata,
                "source_file": chunk.source_file,
                "chunk_id": chunk.chunk_id
            }
            for chunk in chunks
        ]
        ids = [f"{chunk.source_file}_{chunk.chunk_id}" for chunk in chunks]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks")
        embeddings = self.embedding_model.encode(
            documents,
            show_progress_bar=True,
            convert_to_numpy=True
        ).tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector store")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with content and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })
        
        logger.info(f"Found {len(formatted_results)} results for query")
        return formatted_results
    
    def delete_by_source(self, source_file: str) -> None:
        """
        Delete all chunks from a specific source file
        
        Args:
            source_file: Source file path
        """
        try:
            self.collection.delete(
                where={"source_file": source_file}
            )
            logger.info(f"Deleted chunks from {source_file}")
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name
        }
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")


class RAGSystem:
    """Retrieval-Augmented Generation system"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the system"""
        self.vector_store.add_documents(chunks)
    
    def retrieve_context(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Retrieve relevant context for a query
        
        Args:
            query: Query text
            n_results: Number of chunks to retrieve
            filter_metadata: Optional metadata filters
            
        Returns:
            Concatenated context from retrieved chunks
        """
        results = self.vector_store.search(query, n_results, filter_metadata)
        
        if not results:
            logger.warning("No relevant context found")
            return ""
        
        # Build context string
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"--- Context Chunk {i} (Source: {result['metadata'].get('source_file', 'unknown')}) ---\n"
                f"{result['content']}\n"
            )
        
        context = "\n".join(context_parts)
        logger.info(f"Retrieved {len(results)} context chunks ({len(context)} chars)")
        
        return context
    
    def retrieve_context_with_metadata(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context with full metadata
        
        Args:
            query: Query text
            n_results: Number of chunks to retrieve
            filter_metadata: Optional metadata filters
            
        Returns:
            List of results with content and metadata
        """
        return self.vector_store.search(query, n_results, filter_metadata)
