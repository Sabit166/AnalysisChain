"""
Main AnalysisChain Agent - Orchestrates all components for intelligent document processing
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from .config import settings
from .document_loader import DocumentLoader
from .llm_provider import (
    LLMProviderFactory,
    BaseLLMProvider,
    Message,
    LLMResponse
)
from .rag_system import VectorStore, RAGSystem
from .session_manager import SessionManager, SessionState


class AnalysisChainAgent:
    """
    Main AI Agent for document analysis with intelligent caching and context management
    
    Features:
    - Multi-format document loading (PDF, TXT, DOCX)
    - Intelligent chunking and vector storage
    - RAG (Retrieval-Augmented Generation)
    - Prompt/Context caching for Claude and Gemini
    - Session persistence across operations
    - Token cost optimization
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize the agent
        
        Args:
            provider: LLM provider ('claude' or 'gemini')
            model: Model name (uses defaults if not specified)
            session_id: Existing session ID to resume
        """
        # Initialize components
        self.document_loader = DocumentLoader(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        self.vector_store = VectorStore(
            db_path=settings.vector_db_path,
            embedding_model=settings.embedding_model
        )
        
        self.rag_system = RAGSystem(self.vector_store)
        
        self.session_manager = SessionManager(
            storage_path=settings.session_storage_path,
            max_session_age=settings.max_session_age
        )
        
        # Session management - load session first to get provider info
        self.session_id = session_id
        self.session: Optional[SessionState] = None
        
        if session_id:
            self.session = self.session_manager.get_session(session_id)
            if not self.session:
                logger.warning(f"Session {session_id} not found, creating new session")
                self.session_id = None
        
        # Determine provider and model from session or parameters
        if self.session:
            # Use session's provider and model
            self.provider_type = self.session.provider
            self.model = self.session.model
        else:
            # Use provided parameters or defaults
            self.provider_type = provider or settings.default_provider
            self.model = model
        
        if self.provider_type == "claude":
            self.model = self.model or settings.claude_model
            api_key = settings.anthropic_api_key
            cache_ttl = settings.claude_cache_ttl
            max_tokens = settings.claude_max_tokens
            temperature = 0.7
        elif self.provider_type == "gemini":
            self.model = self.model or settings.gemini_model
            api_key = settings.google_api_key
            cache_ttl = settings.gemini_cache_ttl
            max_tokens = settings.gemini_max_tokens
            temperature = 0.7
        elif self.provider_type == "groq":
            self.model = self.model or settings.groq_model
            api_key = settings.groq_api_key
            cache_ttl = 0  # Groq doesn't use caching
            max_tokens = settings.groq_max_tokens
            temperature = settings.groq_temperature
        else:
            raise ValueError(f"Unknown provider: {self.provider_type}")
        
        # Initialize LLM provider
        self.llm_provider = LLMProviderFactory.create_provider(
            provider_type=self.provider_type,
            api_key=api_key,
            model=self.model,
            max_tokens=max_tokens,
            cache_ttl=cache_ttl,
            temperature=temperature
        )
        
        # Create new session if needed
        if not self.session:
            self.session_id = self.session_manager.create_session(
                provider=self.provider_type,
                model=self.model
            )
            self.session = self.session_manager.get_session(self.session_id)
        
        logger.info(
            f"Initialized AnalysisChain Agent - Provider: {self.provider_type}, "
            f"Model: {self.model}, Session: {self.session_id}"
        )
    
    def load_instruction_file(self, instruction_path: Path) -> str:
        """
        Load instruction/prompt file
        
        Args:
            instruction_path: Path to instruction file
            
        Returns:
            Instruction text
        """
        instruction_path = Path(instruction_path)
        
        try:
            with open(instruction_path, 'r', encoding='utf-8') as f:
                instruction = f.read()
            
            # Update session
            self.session_manager.update_session(
                str(self.session_id),
                instruction_file=str(instruction_path)
            )
            
            logger.info(f"Loaded instruction file: {instruction_path} ({len(instruction)} chars)")
            return instruction
        
        except Exception as e:
            logger.error(f"Failed to load instruction file: {e}")
            raise
    
    def load_source_documents(
        self,
        document_paths: List[Path],
        add_to_vector_db: bool = True
    ) -> Dict[str, Any]:
        """
        Load source documents and optionally add to vector database
        
        Args:
            document_paths: List of document paths
            add_to_vector_db: Whether to add to vector database for RAG
            
        Returns:
            Summary of loaded documents
        """
        total_chunks = 0
        loaded_docs = []
        
        for doc_path in document_paths:
            doc_path = Path(doc_path)
            
            try:
                # Load and chunk document
                chunks = self.document_loader.load_and_chunk(doc_path)
                
                if add_to_vector_db:
                    self.rag_system.add_documents(chunks)
                
                total_chunks += len(chunks)
                loaded_docs.append(str(doc_path))
                
                # Update session
                self.session_manager.add_source_document(str(self.session_id), str(doc_path))
                
                logger.info(f"Loaded document: {doc_path} ({len(chunks)} chunks)")
            
            except Exception as e:
                logger.error(f"Failed to load document {doc_path}: {e}")
        
        summary = {
            "documents_loaded": len(loaded_docs),
            "total_chunks": total_chunks,
            "documents": loaded_docs,
            "vector_db_enabled": add_to_vector_db
        }
        
        logger.info(f"Document loading complete: {summary}")
        return summary
    
    def process_query(
        self,
        query: str,
        instruction: Optional[str] = None,
        use_rag: bool = True,
        rag_chunks: int = 10,
        use_cache: bool = True,
        temperature: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process a query with optional RAG and caching
        
        Args:
            query: User query
            instruction: Optional instruction/system prompt
            use_rag: Whether to use RAG for context retrieval
            rag_chunks: Number of chunks to retrieve
            use_cache: Whether to use caching
            temperature: LLM temperature
            
        Returns:
            Tuple of (response_text, metadata)
        """
        # Retrieve relevant context if RAG is enabled
        context = ""
        rag_results = []
        
        if use_rag:
            context = self.rag_system.retrieve_context(query, n_results=rag_chunks)
            rag_results = self.rag_system.retrieve_context_with_metadata(
                query, n_results=rag_chunks
            )
        
        # Build messages
        messages = []
        
        # Add context as a cached message (if available and caching is enabled)
        if context and use_cache:
            # For Claude: mark context for caching
            # For Gemini: context is added to conversation history
            context_message = Message(
                role="user",
                content=f"REFERENCE CONTEXT:\n\n{context}",
                cache_control={"type": "ephemeral"} if self.provider_type == "claude" else None
            )
            messages.append(context_message)
        
        # Add conversation history from session
        if self.session and self.session.message_history:
            for msg in self.session.message_history[-10:]:  # Last 10 messages
                messages.append(Message(
                    role=msg["role"],
                    content=msg["content"]
                ))
        
        # Add current query
        if context and not use_cache:
            # If not using cache, add context inline
            query_with_context = f"{context}\n\nQUERY: {query}"
        else:
            query_with_context = query
        
        messages.append(Message(
            role="user",
            content=query_with_context
        ))
        
        # Generate response
        logger.info(f"Processing query with {len(messages)} messages")
        
        response = self.llm_provider.generate(
            messages=messages,
            system_prompt=instruction,
            temperature=temperature,
            use_cache=use_cache
        )
        
        # Update session with new messages
        self.session_manager.add_message(str(self.session_id), "user", query)
        self.session_manager.add_message(str(self.session_id), "assistant", response.content)
        
        # Build metadata
        metadata = {
            "session_id": self.session_id,
            "provider": self.provider_type,
            "model": response.model,
            "usage": response.usage,
            "cache_info": response.cache_info,
            "rag_enabled": use_rag,
            "rag_chunks_retrieved": len(rag_results),
            "temperature": temperature
        }
        
        logger.info(f"Query processed successfully - Tokens: {response.usage}")
        
        return response.content, metadata
    
    def generate_output_file(
        self,
        content: str,
        output_path: Path,
        format: str = "txt"
    ) -> Path:
        """
        Generate and save output file
        
        Args:
            content: Content to write
            output_path: Output file path
            format: Output format (txt, md)
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update session
            self.session_manager.add_generated_output(str(self.session_id), str(output_path))
            
            logger.info(f"Generated output file: {output_path} ({len(content)} chars)")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to generate output file: {e}")
            raise
    
    def multi_step_operation(
        self,
        queries: List[str],
        instruction: Optional[str] = None,
        save_outputs: bool = True,
        output_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple follow-up queries in sequence
        
        Args:
            queries: List of queries to process
            instruction: Common instruction for all queries
            save_outputs: Whether to save each output
            output_dir: Directory for saving outputs
            
        Returns:
            List of results with metadata
        """
        results = []
        
        if save_outputs and not output_dir:
            output_dir = Path("./outputs") / str(self.session_id)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Processing query {i}/{len(queries)}")
            
            # Process query
            response, metadata = self.process_query(
                query=query,
                instruction=instruction,
                use_rag=True,
                use_cache=True
            )
            
            # Save output if requested
            output_path = None
            if save_outputs:
                output_path = output_dir / f"output_{i}.txt"
                self.generate_output_file(response, output_path)
            
            results.append({
                "query": query,
                "response": response,
                "metadata": metadata,
                "output_path": str(output_path) if output_path else None
            })
        
        logger.info(f"Completed multi-step operation with {len(queries)} queries")
        return results
    
    def switch_instruction(self, new_instruction_path: Path) -> str:
        """
        Switch to a new instruction file
        
        Args:
            new_instruction_path: Path to new instruction file
            
        Returns:
            New instruction text
        """
        return self.load_instruction_file(new_instruction_path)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session
        
        Returns:
            Session summary with statistics
        """
        if not self.session:
            return {}
        
        vector_stats = self.vector_store.get_collection_stats()
        
        return {
            "session_id": self.session.session_id,
            "created_at": self.session.created_at,
            "last_accessed": self.session.last_accessed,
            "provider": self.session.provider,
            "model": self.session.model,
            "instruction_file": self.session.instruction_file,
            "source_documents": len(self.session.source_documents),
            "generated_outputs": len(self.session.generated_outputs),
            "message_count": len(self.session.message_history),
            "vector_db_chunks": vector_stats["total_chunks"],
            "metadata": self.session.metadata
        }
    
    def clear_vector_db(self) -> None:
        """Clear all documents from vector database"""
        self.vector_store.clear_collection()
        logger.info("Cleared vector database")
    
    def reset_session(self) -> str:
        """
        Reset current session and create a new one
        
        Returns:
            New session ID
        """
        old_session_id = self.session_id
        
        self.session_id = self.session_manager.create_session(
            provider=self.provider_type,
            model=self.model
        )
        self.session = self.session_manager.get_session(self.session_id)
        
        logger.info(f"Reset session from {old_session_id} to {self.session_id}")
        return self.session_id
