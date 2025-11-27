# Configuration Guide

## Environment Variables

AnalysisChain uses environment variables for configuration. Create a `.env` file in the project root.

### API Keys (Required)

```env
# At least one of these is required
ANTHROPIC_API_KEY=sk-ant-xxx...
GOOGLE_API_KEY=AIzaSxxx...
```

**Getting API Keys:**
- **Claude**: https://console.anthropic.com/
- **Gemini**: https://ai.google.dev/

### Provider Settings

```env
# Default LLM provider
DEFAULT_PROVIDER=claude  # Options: 'claude' or 'gemini'
```

### Claude Configuration

```env
# Model selection
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Available models:
# - claude-3-5-sonnet-20241022 (recommended)
# - claude-3-opus-20240229
# - claude-3-sonnet-20240229
# - claude-3-haiku-20240307

# Maximum output tokens (1-200000)
CLAUDE_MAX_TOKENS=8192

# Cache time-to-live in seconds (default: 5 minutes)
CLAUDE_CACHE_TTL=300
```

### Gemini Configuration

```env
# Model selection
GEMINI_MODEL=gemini-1.5-pro-002

# Available models:
# - gemini-1.5-pro-002 (recommended, 1M context)
# - gemini-1.5-flash-002 (faster, cheaper)
# - gemini-2.0-flash-exp (experimental)

# Maximum output tokens (1-2000000)
GEMINI_MAX_TOKENS=8192

# Cache time-to-live in seconds (default: 1 hour)
GEMINI_CACHE_TTL=3600
```

### Vector Database Settings

```env
# Storage path for vector database
VECTOR_DB_PATH=./data/vectordb

# Embedding model for semantic search
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Available embedding models:
# - all-MiniLM-L6-v2 (fast, 384 dimensions)
# - all-mpnet-base-v2 (better quality, 768 dimensions)
# - paraphrase-multilingual-MiniLM-L12-v2 (multilingual)

# Document chunking parameters
CHUNK_SIZE=1000          # Characters per chunk
CHUNK_OVERLAP=200        # Overlap between chunks
```

### Session Management

```env
# Storage path for sessions
SESSION_STORAGE_PATH=./data/sessions

# Maximum session age in seconds (default: 24 hours)
MAX_SESSION_AGE=86400
```

### Logging

```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log file path
LOG_FILE=./logs/agent.log
```

## Model Selection Guide

### When to Use Claude

**Best for:**
- Complex reasoning tasks
- Long-form content generation
- Code analysis and generation
- Tasks requiring high accuracy

**Prompt Caching:**
- Saves 90% on cached input tokens
- Cache lasts 5 minutes
- Best for repeated context

**Pricing (as of Nov 2024):**
- Input: $3 per million tokens
- Cached input: $0.30 per million tokens
- Output: $15 per million tokens

### When to Use Gemini

**Best for:**
- Extremely long contexts (up to 2M tokens)
- Real-time applications
- Cost-sensitive workloads
- Multimodal tasks (when using images)

**Context Caching:**
- Saves 75% on cached input tokens
- Cache lasts up to 1 hour
- Requires minimum 1K-4K tokens to cache

**Pricing (as of Nov 2024):**
- Input: $1.25 per million tokens
- Cached input: $0.31 per million tokens
- Output: $5 per million tokens

## Performance Tuning

### Chunk Size Optimization

```env
# For short documents (< 10 pages)
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# For medium documents (10-50 pages)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# For large documents (> 50 pages)
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
```

### RAG Configuration

```python
# Retrieve fewer chunks for focused questions
response, metadata = agent.process_query(
    query="What is X?",
    rag_chunks=3  # Default: 5
)

# Retrieve more chunks for comprehensive questions
response, metadata = agent.process_query(
    query="Summarize everything about X",
    rag_chunks=10
)
```

### Cache Optimization

**For Claude:**
- Cache TTL is fixed at 5 minutes
- Group related queries within 5-minute windows
- Reuse sessions for follow-up questions

**For Gemini:**
- Adjust `GEMINI_CACHE_TTL` based on usage pattern
- Longer TTL for interactive sessions
- Shorter TTL for batch processing

## Security Best Practices

### API Key Protection

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env  # Unix/Linux
```

### Data Privacy

```env
# Use local paths for sensitive data
VECTOR_DB_PATH=./secure_data/vectordb
SESSION_STORAGE_PATH=./secure_data/sessions
```

### Logging

```env
# Reduce logging in production
LOG_LEVEL=WARNING

# Or disable file logging
LOG_FILE=/dev/null  # Unix/Linux
```

## Troubleshooting

### Common Issues

**1. API Key Errors**
```
Error: Invalid API key
```
- Verify `.env` file exists
- Check key format and validity
- Ensure no extra spaces or quotes

**2. Import Errors**
```
ModuleNotFoundError: No module named 'anthropic'
```
- Run: `pip install -r requirements.txt`
- Activate virtual environment

**3. Memory Issues**
```
ChromaDB error: Out of memory
```
- Reduce `CHUNK_SIZE`
- Process fewer documents at once
- Increase system memory

**4. Cache Not Working**
```
Cache hit rate: 0%
```
- Ensure `use_cache=True` in queries
- Check if context is changing between queries
- Verify cache TTL hasn't expired

### Debug Mode

```env
# Enable detailed logging
LOG_LEVEL=DEBUG
```

```python
# Check session state
summary = agent.get_session_summary()
print(summary)

# Verify vector DB
stats = agent.vector_store.get_collection_stats()
print(stats)
```

## Advanced Configuration

### Custom Embedding Models

```python
from src.rag_system import VectorStore

vector_store = VectorStore(
    db_path=Path("./custom_db"),
    embedding_model="sentence-transformers/all-mpnet-base-v2"
)
```

### Custom LLM Parameters

```python
response, metadata = agent.process_query(
    query="Your question",
    temperature=0.3,  # More deterministic
    use_cache=True
)
```

### Provider Switching

```python
# Start with Claude
agent1 = AnalysisChainAgent(provider="claude")

# Switch to Gemini for long context
agent2 = AnalysisChainAgent(
    provider="gemini",
    session_id=agent1.session_id  # Reuse session
)
```

## Environment Templates

### Development
```env
DEFAULT_PROVIDER=claude
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
LOG_LEVEL=DEBUG
CHUNK_SIZE=500
```

### Production
```env
DEFAULT_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-pro-002
GEMINI_MAX_TOKENS=8192
LOG_LEVEL=WARNING
CHUNK_SIZE=1500
MAX_SESSION_AGE=3600
```

### Cost-Optimized
```env
DEFAULT_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash-002
GEMINI_MAX_TOKENS=4096
CHUNK_SIZE=2000
CHUNK_OVERLAP=100
```
