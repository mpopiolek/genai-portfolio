FROM python:3.13-slim

WORKDIR /app

COPY src/server.py ./server.py
COPY fixtures/ ./fixtures/

ENV HUB_MOCK_PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
