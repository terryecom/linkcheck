# 1. Build frontend using Node
FROM node:18 AS frontend
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

# 2. Build backend and install dependencies
FROM python:3.11-slim
WORKDIR /app

# Copy backend source code
COPY backend/ /app/backend

# Copy built frontend into backend public folder
COPY --from=frontend /app/frontend/dist /app/frontend-dist

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Force rebuild (prevents Railway cache from hiding issues)
RUN echo "FORCE_REDEPLOY_$(date +%s)"

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server directly (no shell script)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

