# 🎯 Getting Started with AnalysisChain

Welcome! This guide will get you up and running with AnalysisChain in just a few minutes.

## ⚡ Prerequisites

- Windows 10/11 (or Linux/Mac)
- Python 3.8 or higher
- API key for Claude OR Gemini (or both)

## 📋 Step-by-Step Setup

### Step 1: Install Python Dependencies (2 minutes)

```powershell
# Navigate to project directory
cd d:\AnalysisChain

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed anthropic-X.X.X google-generativeai-X.X.X ...
```

### Step 2: Get Your API Keys (3 minutes)

#### For Claude (Anthropic):
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy your key (starts with `sk-ant-`)

#### For Gemini (Google):
1. Go to https://ai.google.dev/
2. Click "Get API key in Google AI Studio"
3. Sign in with Google account
4. Click "Create API Key"
5. Copy your key (starts with `AIza`)

### Step 3: Configure Environment (1 minute)

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env file with your API key
notepad .env
```

**Edit the .env file:**
```env
# Add your API key (remove 'your_' prefix!)
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# OR if using Gemini
GOOGLE_API_KEY=AIzaSyYour-actual-key-here

# Choose default provider
DEFAULT_PROVIDER=claude
```

Save and close the file.

### Step 4: Verify Installation (1 minute)

```powershell
# Test the CLI
python -m src.cli --help
```

**Expected Output:**
```
Usage: __main__.py [OPTIONS] COMMAND [ARGS]...

  AnalysisChain - AI Agent with Intelligent Caching and Context Management
  ...
```

## 🚀 Your First Query

### Create a Session

```powershell
python -m src.cli new-session --provider claude
```

**Output:**
```
╭──────────── Session Created ────────────╮
│ Session ID: abc-123-def-456            │
│ Provider: claude                        │
│ Model: claude-3-5-sonnet-20241022      │
╰─────────────────────────────────────────╯

💡 Use this session ID for follow-up operations: abc-123-def-456
```

**Copy your Session ID!** You'll need it for the next steps.

### Load a Document

```powershell
# Replace SESSION_ID with your actual session ID
# Replace document.pdf with your actual file
python -m src.cli load-documents abc-123-def-456 document.pdf
```

**Output:**
```
Loading 1 document(s)...

╭──────────── Load Complete ──────────────╮
│ Documents: 1                            │
│ Total chunks: 45                        │
│ Vector DB: Enabled                      │
╰─────────────────────────────────────────╯
```

### Ask Your First Question

```powershell
python -m src.cli query abc-123-def-456 "What is this document about?"
```

**Output:**
```
Processing query...

================================================================================
This document discusses [AI will provide answer here]...
================================================================================

Token Usage:
  Input: 12500
  Output: 250
  Cache Read: 0
```

### Ask a Follow-Up Question

```powershell
python -m src.cli query abc-123-def-456 "Can you elaborate on that?"
```

**Notice the cache in action!**
```
Token Usage:
  Input: 1200
  Output: 300
  Cache Read: 11300  ← 90% of context came from cache!
  Cache Hit Rate: 90.4%
```

**You just saved ~11,000 tokens! 💰**

## 📝 Working with Instruction Files

### Use a Pre-made Instruction

```powershell
python -m src.cli query abc-123-def-456 ^
    "Analyze the methodology" ^
    --instruction examples\instruction_research.txt
```

### Create Your Own Instruction File

Create `my_instruction.txt`:
```
You are a technical analyst. Analyze documents with focus on:
1. Key technical concepts
2. Implementation details
3. Best practices
4. Potential improvements

Be concise and technical in your responses.
```

Use it:
```powershell
python -m src.cli query abc-123-def-456 ^
    "Analyze the code structure" ^
    --instruction my_instruction.txt
```

## 🔄 Working with Multiple Documents

```powershell
# Load multiple documents at once
python -m src.cli load-documents abc-123-def-456 ^
    paper1.pdf ^
    paper2.pdf ^
    notes.txt ^
    data.docx

# Query across all documents
python -m src.cli query abc-123-def-456 ^
    "Compare the findings in paper1 and paper2"
```

## 📊 Batch Processing

Create `queries.txt`:
```
What is the main topic?
What methodology is used?
What are the key findings?
What are the limitations?
What future work is suggested?
```

Process all queries:
```powershell
python -m src.cli batch-query abc-123-def-456 queries.txt ^
    --instruction examples\instruction_research.txt ^
    --output-dir results
```

Check your results:
```powershell
ls results
```

Output:
```
output_1.txt
output_2.txt
output_3.txt
output_4.txt
output_5.txt
```

## 🔍 Managing Sessions

### View All Sessions

```powershell
python -m src.cli info
```

### View Specific Session

```powershell
python -m src.cli info abc-123-def-456
```

### Resume Previous Session

```powershell
# Just use the session ID - conversation history is preserved!
python -m src.cli query abc-123-def-456 "What did we discuss before?"
```

### Delete Old Session

```powershell
python -m src.cli delete-session old-session-id
```

## 🐍 Using Python API

Create `my_analysis.py`:

```python
from pathlib import Path
from src.agent import AnalysisChainAgent

# Initialize agent
agent = AnalysisChainAgent(provider="claude")
print(f"Session: {agent.session_id}")

# Load instruction
instruction = agent.load_instruction_file(
    Path("examples/instruction_research.txt")
)

# Load documents
agent.load_source_documents(
    document_paths=[Path("research_paper.pdf")],
    add_to_vector_db=True
)

# Process query
response, metadata = agent.process_query(
    query="What are the main contributions?",
    instruction=instruction,
    use_rag=True,
    use_cache=True
)

print(response)
print(f"\nTokens used: {metadata['usage']}")
print(f"Cache hit rate: {metadata['cache_info']['cache_hit_rate']:.1f}%")

# Save output
agent.generate_output_file(
    content=response,
    output_path=Path("output.txt")
)
```

Run it:
```powershell
python my_analysis.py
```

## 💡 Pro Tips

### 1. Keep Sessions Alive
```powershell
# Good: Reuse session for related queries
python -m src.cli query SESSION_ID "Question 1"
python -m src.cli query SESSION_ID "Question 2"
python -m src.cli query SESSION_ID "Question 3"

# Bad: New session each time (no cache benefit)
python -m src.cli new-session  # Creates session 1
python -m src.cli new-session  # Creates session 2
python -m src.cli new-session  # Creates session 3
```

### 2. Use RAG for Large Documents
```powershell
# Automatically retrieves only relevant sections
python -m src.cli query SESSION_ID "Find mentions of machine learning" ^
    --chunks 5
```

### 3. Save Important Outputs
```powershell
python -m src.cli query SESSION_ID "Generate summary" ^
    --output summary.txt
```

### 4. Monitor Token Usage
```powershell
# After each query, check:
# - Cache hit rate (higher is better)
# - Tokens saved
# - Total cost
```

## 🐛 Common Issues

### "No module named 'anthropic'"
**Solution:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "Invalid API key"
**Solution:**
```powershell
# Check .env file
notepad .env

# Make sure key has no quotes or spaces:
# Good: ANTHROPIC_API_KEY=sk-ant-xxx
# Bad:  ANTHROPIC_API_KEY="sk-ant-xxx"
# Bad:  ANTHROPIC_API_KEY = sk-ant-xxx
```

### "Session not found"
**Solution:**
```powershell
# List all sessions
python -m src.cli info

# Create new session
python -m src.cli new-session
```

### "File not found"
**Solution:**
```powershell
# Use absolute path
python -m src.cli load-documents SESSION_ID "d:\Documents\paper.pdf"

# Or navigate to file directory
cd d:\Documents
python -m src.cli load-documents SESSION_ID paper.pdf
```

## 📖 What's Next?

### Learn More:
- 📚 **README.md** - Complete feature documentation
- ⚙️ **CONFIGURATION.md** - Advanced configuration options
- 🚀 **DEPLOYMENT.md** - Production deployment guide
- 📝 **examples/usage_examples.py** - More Python examples

### Try These:
1. Load a real research paper
2. Create custom instruction files
3. Process batch queries
4. Switch between Claude and Gemini
5. Track token savings over time

## 🎓 Real-World Example

Let's analyze a research paper end-to-end:

```powershell
# 1. Create session
python -m src.cli new-session --provider claude
# Output: Session ID: xyz-789

# 2. Load paper
python -m src.cli load-documents xyz-789 "machine_learning_paper.pdf"

# 3. Initial analysis
python -m src.cli query xyz-789 ^
    "Summarize the paper in 200 words" ^
    --instruction examples\instruction_research.txt ^
    --output summary.txt

# 4. Deep dive
python -m src.cli query xyz-789 ^
    "Explain the neural network architecture" ^
    --output architecture.txt

# 5. Critical analysis
python -m src.cli query xyz-789 ^
    "What are the limitations and potential improvements?" ^
    --output analysis.txt

# Check token savings
python -m src.cli info xyz-789
```

## 🎉 You're Ready!

You now know how to:
- ✅ Set up AnalysisChain
- ✅ Create and manage sessions
- ✅ Load documents
- ✅ Process queries with caching
- ✅ Use instruction files
- ✅ Save outputs
- ✅ Monitor token usage

**Start analyzing and watch the token savings add up!** 💰

---

**Need help?** Check the documentation or open an issue on GitHub.
