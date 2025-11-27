"""
Test configuration
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return """
    This is a sample document for testing purposes.
    It contains multiple paragraphs and sentences.
    
    The document is used to test chunking, embedding, and retrieval.
    It should be long enough to create multiple chunks.
    
    Testing is an important part of software development.
    It helps ensure code quality and reliability.
    """


@pytest.fixture
def temp_document(tmp_path, sample_text):
    """Create temporary document file"""
    doc_path = tmp_path / "test_document.txt"
    doc_path.write_text(sample_text)
    return doc_path
