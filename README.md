# AnalysisChain 🔗

> **Intelligent AI Agent with Advanced Caching and Context Management**

AnalysisChain is a production-ready AI agent system designed to efficiently process large documents with follow-up operations while dramatically reducing token costs through intelligent caching and context management.

## 🎯 Key Features

### 1. **Intelligent Caching** 💰
- **Claude Prompt Caching**: Saves up to 90% of input token costs by caching reusable context
- **Gemini Context Caching**: Caches conversation context for up to 1 hour with 75% cost reduction
- Automatic cache management with configurable TTL

### 2. **RAG (Retrieval-Augmented Generation)** 🔍
- Vector database (ChromaDB) for semantic document search
- Efficient chunking with configurable overlap
- Retrieve only relevant context, minimizing token usage
- Persistent storage across sessions

### 3. **Multi-Format Document Support** 📄
- PDF files (with multiple extraction methods)
- Plain text files
- DOCX documents
- Intelligent chunking with sentence-boundary awareness

### 4. **Session Management** 🔄
- Persistent sessions across operations
- Conversation history tracking
- Document and output tracking
- Automatic session cleanup

### 5. **Dual LLM Provider Support** 🤖
- **Claude** (Anthropic): Claude 3.5 Sonnet with prompt caching
- **Gemini** (Google): Gemini 1.5 Pro with context caching
- Easy provider switching
- Unified interface for both

### 6. **Production-Ready Features** 🚀
- Comprehensive error handling and retries
- Structured logging with rotation
- Rich CLI with progress indicators
- Configurable via environment variables
- Token usage tracking and reporting

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AnalysisChain Agent                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Document   │  │    Vector    │  │      Session    │   │
│  │    Loader    │→ │   Database   │  │     Manager     │   │
│  └──────────────┘  │  (ChromaDB)  │  └─────────────────┘   │
│                     └──────────────┘                         │
│                            ↓                                 │
│                     ┌──────────────┐                         │
│                     │  RAG System  │                         │
│                     └──────────────┘                         │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           LLM Provider (Claude/Gemini)                │   │
│  │         with Intelligent Caching Layer                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- API keys for Claude and/or Gemini

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/AnalysisChain.git
cd AnalysisChain
```

### Step 2: Create Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# Required: Add your ANTHROPIC_API_KEY and/or GOOGLE_API_KEY
```

## ⚙️ Configuration

Edit `.env` file:

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxx...
GOOGLE_API_KEY=AIzaSxxx...

# Default Provider
DEFAULT_PROVIDER=claude  # or 'gemini'

# Claude Settings
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=8192
CLAUDE_CACHE_TTL=300

# Gemini Settings
GEMINI_MODEL=gemini-1.5-pro-002
GEMINI_MAX_TOKENS=8192
GEMINI_CACHE_TTL=3600

# Vector Database
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## 🚀 Usage

### Quick Start Example

```bash
# 1. Create a new session
python -m src.cli new-session --provider claude

# Output: Session ID: abc123-def456-ghi789

# 2. Load documents
python -m src.cli load-documents abc123-def456-ghi789 research_paper.pdf data.txt

# 3. Process a query
python -m src.cli query abc123-def456-ghi789 "What are the main findings?"

# 4. Process with instruction file
python -m src.cli query abc123-def456-ghi789 \
    "Summarize the methodology" \
    --instruction examples/instruction_research.txt \
    --output output.txt

# 5. Batch processing
python -m src.cli batch-query abc123-def456-ghi789 \
    examples/sample_queries.txt \
    --instruction examples/instruction_research.txt \
    --output-dir ./results
```

### Programmatic Usage

```python
from pathlib import Path
from src.agent import AnalysisChainAgent

# Initialize agent
agent = AnalysisChainAgent(provider="claude")

# Load instruction
instruction = agent.load_instruction_file(
    Path("examples/instruction_research.txt")
)

# Load documents
agent.load_source_documents(
    document_paths=[
        Path("research_paper.pdf"),
        Path("supplementary_data.txt")
    ],
    add_to_vector_db=True
)

# Process query with RAG and caching
response, metadata = agent.process_query(
    query="What are the main findings?",
    instruction=instruction,
    use_rag=True,
    use_cache=True
)

print(response)
print(f"Tokens used: {metadata['usage']}")
print(f"Cache hit rate: {metadata['cache_info']['cache_hit_rate']:.1f}%")

# Multi-step operation
queries = [
    "Summarize the introduction",
    "Explain the methodology",
    "What are the key results?"
]

results = agent.multi_step_operation(
    queries=queries,
    instruction=instruction,
    save_outputs=True
)
```

## 💡 Use Cases

### 1. **Research Paper Analysis**
```bash
# Analyze academic papers with follow-up questions
python -m src.cli new-session --provider claude
python -m src.cli load-documents SESSION_ID paper1.pdf paper2.pdf
python -m src.cli query SESSION_ID "Compare the methodologies" \
    --instruction examples/instruction_research.txt
```

### 2. **Code Documentation Generation**
```bash
# Generate documentation from code files
python -m src.cli load-documents SESSION_ID src/*.py
python -m src.cli query SESSION_ID "Document the main classes" \
    --instruction examples/instruction_code_doc.txt
```

### 3. **Multi-Stage Analysis**
```python
# Stage 1: Initial analysis with instruction set 1
agent.process_query(query1, instruction=instruction1)

# Stage 2: Follow-up with instruction set 2
agent.switch_instruction(Path("instruction2.txt"))
agent.process_query(query2)

# Costs are minimized through caching!
```

## 📊 CLI Commands

### Session Management
```bash
# Create new session
python -m src.cli new-session [--provider claude|gemini] [--model MODEL]

# List all sessions
python -m src.cli info

# Show session details
python -m src.cli info SESSION_ID

# Delete session
python -m src.cli delete-session SESSION_ID

# Cleanup expired sessions
python -m src.cli cleanup
```

### Document Operations
```bash
# Load documents
python -m src.cli load-documents SESSION_ID file1.pdf file2.txt [--no-vector-db]
```

### Query Processing
```bash
# Single query
python -m src.cli query SESSION_ID "Your question" \
    [--instruction FILE] \
    [--no-rag] \
    [--no-cache] \
    [--chunks N] \
    [--temperature 0.7] \
    [--output FILE]

# Batch queries
python -m src.cli batch-query SESSION_ID queries.txt \
    [--instruction FILE] \
    [--output-dir DIR]
```

## 🔧 Advanced Features

### Custom Chunking Strategy
```python
from src.document_loader import DocumentLoader

loader = DocumentLoader(
    chunk_size=1500,
    chunk_overlap=300
)
chunks = loader.load_and_chunk(Path("large_file.pdf"))
```

### Direct Vector Search
```python
from src.rag_system import VectorStore

vector_store = VectorStore(
    db_path=Path("./custom_db"),
    embedding_model="all-MiniLM-L6-v2"
)

results = vector_store.search(
    query="machine learning",
    n_results=10
)
```

### Session Metadata
```python
# Add custom metadata
agent.session_manager.update_session(
    session_id=agent.session_id,
    metadata={
        "project": "Research Analysis",
        "stage": "methodology",
        "version": "1.0"
    }
)
```

## 💰 Cost Optimization

### How Caching Saves Money

**Without Caching:**
```
Query 1: 10,000 input tokens + 500 output tokens
Query 2: 10,000 input tokens + 500 output tokens
Query 3: 10,000 input tokens + 500 output tokens
Total: 30,000 input tokens
```

**With Caching:**
```
Query 1: 10,000 input tokens (cached) + 500 output tokens
Query 2: 1,000 new tokens + 9,000 cached (90% discount) + 500 output
Query 3: 1,000 new tokens + 9,000 cached (90% discount) + 500 output
Total: ~4,800 effective input tokens (84% savings!)
```

### Best Practices
1. **Reuse sessions** for follow-up questions
2. **Enable RAG** to retrieve only relevant context
3. **Use caching** for repeated context (enabled by default)
4. **Batch similar queries** in one session
5. **Keep instruction files** reusable across queries

## 🧪 Testing

```bash
# Run tests (when available)
pytest tests/

# Test with sample data
python -m src.cli new-session
# Use the examples/ directory files
```

## 📝 Project Structure

```
AnalysisChain/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── agent.py             # Main agent orchestrator
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration management
│   ├── document_loader.py   # Document processing
│   ├── llm_provider.py      # LLM abstraction with caching
│   ├── rag_system.py        # Vector DB and RAG
│   ├── session_manager.py   # Session persistence
│   └── logging_config.py    # Logging setup
├── examples/
│   ├── instruction_research.txt
│   ├── instruction_code_doc.txt
│   └── sample_queries.txt
├── data/                    # Created automatically
│   ├── vectordb/           # Vector database storage
│   └── sessions/           # Session persistence
├── logs/                   # Log files
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔒 Security Notes

- **Never commit `.env`** file with API keys
- API keys are loaded from environment variables only
- Session files contain conversation history (store securely)
- Vector database is local (no external data transmission)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude API](https://www.anthropic.com/) - Prompt caching
- [Google Gemini API](https://ai.google.dev/) - Context caching
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review example files in `examples/`

---

**Built for efficiency. Designed for production. Ready for research.** 🚀
