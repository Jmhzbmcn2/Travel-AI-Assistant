# Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Build Backend
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy backend code
COPY src/ ./src/
COPY main.py .

# Copy frontend static build (optional, if served by FastAPI)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure SQLite data dir exists
RUN mkdir -p /app/data

# Environment
ENV PYTHONPATH=/app/src
ENV DEMO_MODE=false
ENV PORT=8000

EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
