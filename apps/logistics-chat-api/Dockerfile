FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV FLASK_PORT=5000
EXPOSE 5000

CMD ["python", "src/server.py"]
