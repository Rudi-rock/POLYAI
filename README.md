# PolyAI - Offline Multi-Agent AI Summarization System

An offline, privacy-preserving AI summarization engine that uses multi-agent debate architecture to deliver high-quality summaries without internet or cloud dependencies.

## 🌟 Key Features

- **100% Offline**: No internet required, complete privacy
- **< 10 MB Footprint**: Lightweight rule-based heuristics
- **Multi-Agent Debate**: 4 specialized agents collaborate for better results
- **Fast**: < 2 second latency on typical hardware
- **Privacy-First**: All processing happens locally

## 🏗️ Architecture

```
[ Frontend (Web UI) ]
        ↓
[ Local API (FastAPI) ]
        ↓
[ PolyAI Core Engine ]
        ↓
[ Multi-Agent Debate System ]
        ↓
[ Final Refined Summary ]
```

### The Four Agents

1. **Reasoning Agent** 🧠 - Extracts key ideas and builds logical flow
2. **Verification Agent** ✓ - Validates claims against source text
3. **Simplification Agent** 📝 - Improves readability and clarity
4. **Critique Agent** 🔍 - Finds gaps and quality issues

## 🚀 Quick Start

### Backend Setup

```powershell
cd polyai/backend

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

Simply open `polyai/frontend/index.html` in your browser.

The frontend can work:
- **With backend**: Full multi-agent processing via API
- **Standalone**: Uses built-in JavaScript fallback processing

## 📁 Project Structure

```
polyai/
├── frontend/
│   ├── index.html      # Web interface
│   ├── styles.css      # Modern dark theme
│   └── app.js          # UI logic + fallback processing
│
├── backend/
│   ├── main.py         # FastAPI server
│   ├── requirements.txt
│   └── core/
│       ├── input_processor.py    # Text normalization
│       ├── shared_encoder.py     # TF-IDF encoding
│       ├── debate_engine.py      # Agent orchestration
│       ├── scoring_engine.py     # Quality metrics
│       ├── output_refiner.py     # Final polish
│       └── agents/
│           ├── reasoning_agent.py
│           ├── verification_agent.py
│           ├── simplification_agent.py
│           └── critique_agent.py
│
└── README.md
```

## 🔧 API Reference

### POST /summarize

```json
Request:
{
  "text": "Your long text to summarize...",
  "debug": false,
  "max_length": 500
}

Response:
{
  "summary": "The condensed summary...",
  "stats": {
    "original_words": 500,
    "summary_words": 100,
    "compression_percent": 80,
    "latency_ms": 450
  },
  "agents": { ... }  // Only if debug=true
}
```

### GET /health

Returns service health status and component readiness.

## 🎨 UI Features

- **Dark Mode**: Modern glassmorphism design
- **Debug Mode**: View individual agent reasoning
- **Real-time Stats**: Word count, compression ratio, latency
- **Paste & Copy**: Quick clipboard integration

## 💡 How It Works

1. **Input Processing**: Text is normalized, cleaned, and tokenized
2. **Shared Encoding**: TF-IDF vectorization creates text representation
3. **Agent Execution**: All 4 agents analyze the text independently
4. **Debate & Scoring**: Outputs are scored on coverage, clarity, brevity
5. **Output Refinement**: Best elements are merged and polished

The key insight: **Collective reasoning > model size**

Instead of one large model, multiple small specialized "experts" collaborate to produce better results than any single agent alone.

## 📊 Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| Total Size | < 10 MB | ✓ Pure Python/JS |
| Latency | < 2 sec | ~500ms typical |
| RAM Usage | < 2 GB | ~50MB |
| CPU Cores | 2 | Works on single core |

## 🔒 Privacy

- **Zero data collection**: No telemetry or analytics
- **No external calls**: Works completely offline
- **Local storage only**: All processing on-device
- **Open source**: Fully auditable code

## 📝 License

MIT License - Use freely for personal and commercial projects.
