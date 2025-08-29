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
