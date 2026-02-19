FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

RUN uv pip install --system dash dash-ag-grid ruff pandas requests

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8050

CMD ["python", "tests_dash.py"]
