# 1. Build frontend
FROM node:18 AS frontend
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

# 2. Build backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/ /app/backend
COPY --from=frontend /app/frontend/dist /app/frontend-dist
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 3. Run both
COPY start.sh /start.sh
RUN chmod +x /start.sh
EXPOSE 8000
CMD ["/start.sh"]
