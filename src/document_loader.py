"""
Document processing module for loading and preprocessing text files and PDFs
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import PyPDF2
import pdfplumber
from docx import Document
from loguru import logger


@dataclass
class DocumentChunk:
    """Represents a chunk of document content"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: int
    source_file: str


class DocumentLoader:
    """Handles loading and preprocessing of various document formats"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_document(self, file_path: Path) -> str:
        """
        Load document content from file
        
        Args:
            file_path: Path to the document
            
        Returns:
            Full document text content
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._load_pdf(file_path)
        elif suffix == '.txt':
            return self._load_text(file_path)
        elif suffix == '.docx':
            return self._load_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _load_text(self, file_path: Path) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded text file: {file_path} ({len(content)} chars)")
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.warning(f"Loaded text file with latin-1 encoding: {file_path}")
            return content
    
    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file with fallback methods"""
        text = ""
        
        # Try pdfplumber first (better for complex PDFs)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if text.strip():
                logger.info(f"Loaded PDF with pdfplumber: {file_path} ({len(text)} chars)")
                return text
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if text.strip():
                logger.info(f"Loaded PDF with PyPDF2: {file_path} ({len(text)} chars)")
                return text
        except Exception as e:
            logger.error(f"PyPDF2 also failed for {file_path}: {e}")
        
        if not text.strip():
            raise ValueError(f"Could not extract text from PDF: {file_path}")
        
        return text
    
    def _load_docx(self, file_path: Path) -> str:
        """Load DOCX file"""
        try:
            doc = Document(file_path)
            text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            logger.info(f"Loaded DOCX file: {file_path} ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Failed to load DOCX {file_path}: {e}")
            raise
    
    def chunk_document(
        self,
        content: str,
        source_file: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Split document into overlapping chunks
        
        Args:
            content: Document text content
            source_file: Source file path
            metadata: Additional metadata
            
        Returns:
            List of document chunks
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(content):
            end = start + self.chunk_size
            chunk_text = content[start:end]
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings
                for delimiter in ['. ', '.\n', '! ', '?\n']:
                    last_delim = chunk_text.rfind(delimiter)
                    if last_delim > self.chunk_size * 0.7:  # At least 70% of chunk size
                        end = start + last_delim + len(delimiter)
                        chunk_text = content[start:end]
                        break
            
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                metadata={
                    **metadata,
                    'chunk_index': chunk_id,
                    'start_pos': start,
                    'end_pos': end
                },
                chunk_id=chunk_id,
                source_file=source_file
            )
            
            chunks.append(chunk)
            chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        
        logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
    
    def load_and_chunk(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Load document and split into chunks in one operation
        
        Args:
            file_path: Path to document
            metadata: Additional metadata
            
        Returns:
            List of document chunks
        """
        content = self.load_document(file_path)
        return self.chunk_document(content, str(file_path), metadata)
