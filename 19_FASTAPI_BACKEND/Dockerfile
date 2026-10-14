FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY config ./config
COPY README.md ./README.md
ENV PYTHONUNBUFFERED=1
ENV MAIZE_API_HOST=0.0.0.0
ENV MAIZE_API_PORT=8000
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
