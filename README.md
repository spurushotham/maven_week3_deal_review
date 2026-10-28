# M&A Compliance Reviewer Prototype

## Run locally

1. Create an environment and install dependencies. Activation is optional on systems that restrict PowerShell scripts:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Install and start Ollama, then pull the models:

   ```powershell
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```

3. Start Streamlit:

   ```powershell
   .\.venv\Scripts\streamlit.exe run app.py
   ```

If PowerShell activation is permitted, `.\.venv\Scripts\Activate.ps1` can still be used.

The app accepts PDF uploads and includes the synthetic Markdown deals as a development-only sample selector. The default fast-local mode uses lexical policy retrieval and an immediate conservative evaluator. Enable `Use Ollama deep analysis (slower)` in the sidebar for model-generated analysis. Set `USE_SEMANTIC_RETRIEVAL=true` when you want Ollama embeddings and Chroma retrieval.

## Current architecture

`app.py` → LangGraph orchestrator → extraction → policy retrieval → LLM analysis → Streamlit HITL annotations.

The policy index uses Ollama embeddings with Chroma and falls back to lexical retrieval when the embedding service is unavailable. Review state is session-only.
