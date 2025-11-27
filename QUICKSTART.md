# Quick Start Guide

Get up and running with AnalysisChain in 5 minutes!

## Step 1: Installation (2 minutes)

```powershell
# Clone the repository
git clone https://github.com/yourusername/AnalysisChain.git
cd AnalysisChain

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration (1 minute)

```powershell
# Copy example config
cp .env.example .env

# Edit .env and add your API key
# For Claude: ANTHROPIC_API_KEY=sk-ant-xxx...
# For Gemini: GOOGLE_API_KEY=AIzaSxxx...
```

Get API keys:
- **Claude**: https://console.anthropic.com/
- **Gemini**: https://ai.google.dev/

## Step 3: First Run (2 minutes)

### Using CLI

```powershell
# 1. Create a session
python -m src.cli new-session --provider claude
# Output: Session ID: abc-123-def-456

# 2. Load a document
python -m src.cli load-documents abc-123-def-456 your_file.pdf

# 3. Ask a question
python -m src.cli query abc-123-def-456 "What is this document about?"
```

### Using Python

```python
from pathlib import Path
from src.agent import AnalysisChainAgent

# Initialize
agent = AnalysisChainAgent(provider="claude")

# Load document
agent.load_source_documents([Path("your_file.pdf")])

# Ask question
response, metadata = agent.process_query(
    query="What is this document about?",
    use_rag=True,
    use_cache=True
)

print(response)
```

## Common Use Cases

### 1. Research Paper Analysis

```powershell
# Create session
python -m src.cli new-session --provider claude

# Load papers
python -m src.cli load-documents SESSION_ID paper1.pdf paper2.pdf

# Ask questions with instruction
python -m src.cli query SESSION_ID "Compare the methodologies" \
    --instruction examples/instruction_research.txt
```

### 2. Code Documentation

```powershell
# Load source code
python -m src.cli load-documents SESSION_ID src/*.py

# Generate documentation
python -m src.cli query SESSION_ID "Document the main classes" \
    --instruction examples/instruction_code_doc.txt \
    --output documentation.md
```

### 3. Batch Processing

```powershell
# Create queries file (queries.txt)
# Line 1: What are the main findings?
# Line 2: Explain the methodology
# Line 3: What are the conclusions?

# Process all queries
python -m src.cli batch-query SESSION_ID queries.txt \
    --instruction instruction.txt \
    --output-dir ./results
```

## Tips for Success

### ✅ Do's
- **Keep sessions alive** for follow-up questions (saves tokens!)
- **Use instruction files** for consistent behavior
- **Enable RAG** for large documents (faster, cheaper)
- **Batch related queries** together

### ❌ Don'ts
- Don't create new sessions for every question
- Don't load the same documents multiple times
- Don't disable caching (unless testing)
- Don't process 100+ page PDFs without chunking

## Understanding Token Costs

### Example: Research Paper Analysis

**Scenario:** 50-page research paper, 5 follow-up questions

**Without AnalysisChain:**
```
Each query: ~40,000 tokens (full paper)
Total: 40,000 × 5 = 200,000 tokens
Cost: ~$0.60 (Claude)
```

**With AnalysisChain:**
```
Query 1: 40,000 tokens (cached)
Query 2-5: 4,000 tokens each (90% from cache)
Total: 40,000 + (4,000 × 4) = 56,000 effective tokens
Cost: ~$0.13 (Claude)
Savings: 72%! 💰
```

## Next Steps

1. **Read the full README** for detailed features
2. **Check CONFIGURATION.md** for advanced settings
3. **Explore examples/** for more use cases
4. **Join the community** (coming soon)

## Troubleshooting

### "Module not found" error
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### "Invalid API key" error
```powershell
# Check .env file exists and has correct format
# ANTHROPIC_API_KEY=sk-ant-xxx...  (no quotes, no spaces)
```

### "Session not found" error
```powershell
# List all sessions
python -m src.cli info

# Use correct session ID
python -m src.cli info YOUR_SESSION_ID
```

## Getting Help

- Check `README.md` for full documentation
- Review `examples/usage_examples.py`
- Open an issue on GitHub
- Read `CONFIGURATION.md` for settings

---

**You're ready to go! 🚀**

Start with a simple query and watch the token savings add up!
