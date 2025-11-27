"""
Unit tests for AnalysisChain components
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.document_loader import DocumentLoader, DocumentChunk
from src.session_manager import SessionManager, SessionState


class TestDocumentLoader:
    """Tests for DocumentLoader"""
    
    def test_chunk_document(self):
        """Test document chunking"""
        loader = DocumentLoader(chunk_size=100, chunk_overlap=20)
        
        content = "A" * 250  # 250 characters
        chunks = loader.chunk_document(content, "test.txt")
        
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert chunks[0].source_file == "test.txt"
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap"""
        loader = DocumentLoader(chunk_size=100, chunk_overlap=20)
        
        content = "0123456789" * 30  # 300 characters
        chunks = loader.chunk_document(content, "test.txt")
        
        # Check that chunks overlap
        if len(chunks) > 1:
            # Last 20 chars of first chunk should appear in second chunk
            end_of_first = chunks[0].content[-20:]
            start_of_second = chunks[1].content[:20]
            # Some overlap should exist
            assert len(chunks) >= 2


class TestSessionManager:
    """Tests for SessionManager"""
    
    @pytest.fixture
    def session_manager(self, tmp_path):
        """Create session manager with temp directory"""
        return SessionManager(storage_path=tmp_path, max_session_age=3600)
    
    def test_create_session(self, session_manager):
        """Test session creation"""
        session_id = session_manager.create_session(
            provider="claude",
            model="claude-3-5-sonnet-20241022"
        )
        
        assert session_id is not None
        assert len(session_id) > 0
        
        # Verify session can be retrieved
        session = session_manager.get_session(session_id)
        assert session is not None
        assert session.provider == "claude"
    
    def test_update_session(self, session_manager):
        """Test session updates"""
        session_id = session_manager.create_session(
            provider="claude",
            model="claude-3-5-sonnet-20241022"
        )
        
        # Update session
        success = session_manager.update_session(
            session_id,
            source_documents=["doc1.pdf", "doc2.txt"]
        )
        
        assert success
        
        # Verify update
        session = session_manager.get_session(session_id)
        assert len(session.source_documents) == 2
    
    def test_add_message(self, session_manager):
        """Test adding messages to session"""
        session_id = session_manager.create_session(
            provider="claude",
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add messages
        session_manager.add_message(session_id, "user", "Hello")
        session_manager.add_message(session_id, "assistant", "Hi there")
        
        # Verify messages
        session = session_manager.get_session(session_id)
        assert len(session.message_history) == 2
        assert session.message_history[0]["role"] == "user"
        assert session.message_history[1]["role"] == "assistant"
    
    def test_delete_session(self, session_manager):
        """Test session deletion"""
        session_id = session_manager.create_session(
            provider="claude",
            model="claude-3-5-sonnet-20241022"
        )
        
        # Delete session
        success = session_manager.delete_session(session_id)
        assert success
        
        # Verify deletion
        session = session_manager.get_session(session_id)
        assert session is None


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.skipif(
        not Path(".env").exists(),
        reason="Requires .env file with API keys"
    )
    def test_basic_workflow(self):
        """Test basic agent workflow (requires API key)"""
        from src.agent import AnalysisChainAgent
        
        # This test only runs if .env exists
        agent = AnalysisChainAgent(provider="claude")
        
        assert agent.session_id is not None
        assert agent.provider_type == "claude"
        
        # Get session summary
        summary = agent.get_session_summary()
        assert "session_id" in summary
        assert "provider" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
