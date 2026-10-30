FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY bluff_lab ./bluff_lab
COPY server ./server
RUN pip install --no-cache-dir numpy fastapi uvicorn .
ENV ARENA_DB=/data/arena.db
VOLUME /data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
