# 1. Build frontend
FROM node:18 AS frontend
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

# 2. Build backend and copy frontend build into static
FROM python:3.11-slim
WORKDIR /app
COPY backend/ /app/backend
COPY --from=frontend /app/frontend/dist /app/frontend-dist
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 3. Run FastAPI using Uvicorn directly
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


