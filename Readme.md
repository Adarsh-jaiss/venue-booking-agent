


uv venv venv

source venv/bin/activate

uv pip sync requirements.txt

uv pip freeze > requirements.txt

python3 main.py




python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &

cd ui && streamlit run main.py --server.port 8501 --server.address 0.0.0.0


uvicorn app:app --host 0.0.0.0 --port 8007 --timeout-keep-alive 1800 --reload