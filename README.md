# Inteligencia Juridica

Layered FastAPI project structure.

## Layout

```
src/
  domain/
  application/
  infrastructure/
  routes/
  main.py
```

## Quick start

1. Create & activate virtual env (example):
```
python -m venv .venv
.venv\Scripts\activate
```
2. Install deps:
```
pip install -r requirements.txt
```
3. Run API locally:
```
uvicorn src.main:app --reload
```
4. Run tests:
```
pytest
```

## Dependencies: Base vs. Optional ML

The project separates minimal runtime dependencies from heavier ML / LangChain tooling to avoid build issues (notably on Python 3.13 where some wheels are still catching up).

Base (`requirements.txt`):
- FastAPI stack, settings, HTTP clients
- google-generativeai (direct Gemini SDK)
- pypdf (lightweight PDF text extraction used in fallback mode)

Optional ML (`requirements-ml.txt`):
- langchain / langchain-google-genai (chain abstractions, experimentation)
- (Will pull in numpy and other heavier transitive deps that may require a compiler on Windows with Python 3.13)

### When to install extras
Install `requirements-ml.txt` only if you need LangChain experimentation or alternative Gemini access without the native file upload route.

### Installation commands
Base only (recommended default):
```
pip install -r requirements.txt
```

Add ML extras (prefer Python 3.12 for wider wheel availability):
```
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

### Environment variables
Set your Gemini API key (required for real model analysis):
```
set GEMINI_API_KEY=your_key_here  # Windows PowerShell: $Env:GEMINI_API_KEY="your_key_here"
```
Optional debug mode to include internal diagnostics in /extract responses:
```
set INTJ_DEBUG=1
```

### Fallback behavior
- If the native `google-generativeai` SDK (with file upload) is unavailable, the service attempts a LangChain fallback (if installed) using extracted PDF text.
- If neither is available, a stub resume is returned so the endpoint stays responsive.

### Troubleshooting
- Source build of numpy / tiktoken failing: use only base requirements or switch to Python 3.12 for ML extras.
- Missing `google-generativeai`: reinstall base requirements.
- Large PDF: only first ~25 pages are sampled in fallback mode to control token usage.

