"""
Session management for tracking conversations and state
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class SessionState:
    """Represents the state of an agent session"""
    session_id: str
    created_at: str
    last_accessed: str
    provider: str
    model: str
    instruction_file: Optional[str] = None
    source_documents: List[str] = None
    generated_outputs: List[str] = None
    message_history: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []
        if self.generated_outputs is None:
            self.generated_outputs = []
        if self.message_history is None:
            self.message_history = []
        if self.metadata is None:
            self.metadata = {}


class SessionManager:
    """Manages agent sessions with persistence"""
    
    def __init__(self, storage_path: Path, max_session_age: int = 86400):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_session_age = max_session_age  # seconds
        self.active_sessions: Dict[str, SessionState] = {}
        
        logger.info(f"Initialized session manager at {storage_path}")
    
    def create_session(
        self,
        provider: str,
        model: str,
        instruction_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session
        
        Args:
            provider: LLM provider name
            model: Model name
            instruction_file: Path to instruction file
            metadata: Additional metadata
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session = SessionState(
            session_id=session_id,
            created_at=now,
            last_accessed=now,
            provider=provider,
            model=model,
            instruction_file=instruction_file,
            metadata=metadata or {}
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionState or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.last_accessed = datetime.now().isoformat()
            self._save_session(session)
            return session
        
        # Try to load from disk
        session = self._load_session(session_id)
        if session:
            # Check if session is expired
            last_accessed = datetime.fromisoformat(session.last_accessed)
            if datetime.now() - last_accessed > timedelta(seconds=self.max_session_age):
                logger.warning(f"Session {session_id} has expired")
                self.delete_session(session_id)
                return None
            
            session.last_accessed = datetime.now().isoformat()
            self.active_sessions[session_id] = session
            self._save_session(session)
            return session
        
        logger.warning(f"Session not found: {session_id}")
        return None
    
    def update_session(
        self,
        session_id: str,
        instruction_file: Optional[str] = None,
        source_documents: Optional[List[str]] = None,
        generated_outputs: Optional[List[str]] = None,
        message_history: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session state
        
        Args:
            session_id: Session ID
            instruction_file: New instruction file
            source_documents: List of source document paths
            generated_outputs: List of generated output paths
            message_history: Updated message history
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if instruction_file is not None:
            session.instruction_file = instruction_file
        
        if source_documents is not None:
            session.source_documents = source_documents
        
        if generated_outputs is not None:
            session.generated_outputs = generated_outputs
        
        if message_history is not None:
            session.message_history = message_history
        
        if metadata is not None:
            session.metadata.update(metadata)
        
        session.last_accessed = datetime.now().isoformat()
        self._save_session(session)
        
        logger.info(f"Updated session: {session_id}")
        return True
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to session history
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant)
            content: Message content
            
        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        session.last_accessed = datetime.now().isoformat()
        self._save_session(session)
        return True
    
    def add_source_document(self, session_id: str, document_path: str) -> bool:
        """Add source document to session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        if document_path not in session.source_documents:
            session.source_documents.append(document_path)
            self._save_session(session)
        
        return True
    
    def add_generated_output(self, session_id: str, output_path: str) -> bool:
        """Add generated output to session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        if output_path not in session.generated_outputs:
            session.generated_outputs.append(output_path)
            self._save_session(session)
        
        return True
    
    def get_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata
        
        Args:
            session_id: Session ID
            
        Returns:
            Metadata dictionary or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.metadata
    
    def update_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata
        
        Args:
            session_id: Session ID
            metadata: Metadata dictionary to merge with existing metadata
            
        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.metadata.update(metadata)
        session.last_accessed = datetime.now().isoformat()
        self._save_session(session)
        
        logger.debug(f"Updated metadata for session {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Delete file
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions
        
        Returns:
            List of session summaries
        """
        sessions = []
        
        # Scan storage directory
        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    
                sessions.append({
                    "session_id": data["session_id"],
                    "created_at": data["created_at"],
                    "last_accessed": data["last_accessed"],
                    "provider": data["provider"],
                    "model": data["model"],
                    "message_count": len(data.get("message_history", []))
                })
            except Exception as e:
                logger.error(f"Failed to load session {session_file}: {e}")
        
        return sorted(sessions, key=lambda x: x["last_accessed"], reverse=True)
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions deleted
        """
        deleted_count = 0
        now = datetime.now()
        
        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                last_accessed = datetime.fromisoformat(data["last_accessed"])
                if now - last_accessed > timedelta(seconds=self.max_session_age):
                    session_file.unlink()
                    session_id = data["session_id"]
                    if session_id in self.active_sessions:
                        del self.active_sessions[session_id]
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to check session {session_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired sessions")
        
        return deleted_count
    
    def _save_session(self, session: SessionState) -> None:
        """Save session to disk"""
        session_file = self.storage_path / f"{session.session_id}.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(asdict(session), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[SessionState]:
        """Load session from disk"""
        session_file = self.storage_path / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            return SessionState(**data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
