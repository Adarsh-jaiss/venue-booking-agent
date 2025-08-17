# venue booking agent

```
uv venv venv

source venv/bin/activate

uv pip sync requirements.txt

uv pip freeze > requirements.txt

```

#### Use for running the server
```
uvicorn app:app --host 0.0.0.0 --port 8007 --timeout-keep-alive 1800 --reload
```

```
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &

cd ui && streamlit run main.py --server.port 8501 --server.address 0.0.0.0
```

