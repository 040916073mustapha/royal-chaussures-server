web: gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --worker-class sync --env PYTHONIOENCODING=utf-8 --env LANG=en_US.UTF-8 --env AI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo

